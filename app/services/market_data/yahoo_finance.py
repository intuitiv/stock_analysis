import asyncio
import logging
import numpy as np
import pandas as pd
import random
import requests
import time
import yfinance as yf
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Any, Optional
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from app.services.market_data.interface import MarketDataProvider
from app.core.cache import RedisCache  # Assuming RedisCache is implemented
from app.core.config import settings

logger = logging.getLogger(__name__)

def with_retry(max_retries=3, initial_delay=1, max_delay=60, exponential_base=2):
    """Decorator that implements exponential backoff retry logic with jitter."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for retry in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if "429" in str(e):  # Rate limit error
                        jitter = random.uniform(0.1, 0.5) * delay
                        sleep_time = delay + jitter
                        logger.warning(f"Rate limit hit, retrying in {sleep_time:.2f} seconds...")
                        await asyncio.sleep(sleep_time)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        raise e
            raise last_exception
        return wrapper
    return decorator

class RateLimiter:
    """Implements rate limiting for API calls."""
    def __init__(self, calls_per_second=2):
        self.calls_per_second = calls_per_second
        self.calls = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make an API call with rate limiting."""
        async with self.lock:
            now = time.time()
            # Remove old calls
            self.calls = [call_time for call_time in self.calls if now - call_time < 1]
            
            if len(self.calls) >= self.calls_per_second:
                sleep_time = 1 - (now - self.calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            self.calls.append(now)

class YahooFinanceProvider(MarketDataProvider):
    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache if cache else RedisCache()
        self.rate_limiter = RateLimiter(calls_per_second=2)  # Max 2 calls per second
        
        # Different cache TTLs for different data types
        self.cache_ttls = {
            "quote": 60,  # 1 minute for real-time quotes
            "price": 300,  # 5 minutes for historical prices
            "profile": 86400,  # 24 hours for company profiles
            "financials": 3600,  # 1 hour for financial statements
            "news": 300  # 5 minutes for news
        }
        self.session = self._create_retry_session()

    def _create_retry_session(
        self,
        retries: int = 3,
        backoff_factor: float = 0.3,
        status_forcelist: tuple = (429, 500, 502, 503, 504),
        session: Optional[requests.Session] = None,
    ) -> requests.Session:
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=frozenset(['GET', 'POST']) # yfinance uses GET and POST
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        # Set a common user agent to avoid being blocked
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        return session

    def _get_cache_ttl(self, data_type: str) -> int:
        return self.cache_ttls.get(data_type, 300)  # Default 5 minutes
    
    @with_retry()
    async def _fetch_with_cache(self, cache_key: str, data_type: str, fetch_func, *args, **kwargs) -> Any:
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        except Exception as e:
            logger.error(f"Redis cache GET error for {cache_key}: {e}")
        
        logger.debug(f"Cache miss for {cache_key}. Fetching from source.")
        
        # Apply rate limiting before making the request
        await self.rate_limiter.acquire()
        
        # Run blocking yfinance calls in a separate thread
        data = await asyncio.to_thread(fetch_func, *args, **kwargs)
        
        if data is not None and not (isinstance(data, pd.DataFrame) and data.empty) and not (isinstance(data, list) and not data):
            try:
                await self.cache.set(cache_key, data, ttl=self._get_cache_ttl(data_type))
                logger.debug(f"Cached data for {cache_key}")
            except Exception as e:
                logger.error(f"Redis cache SET error for {cache_key}: {e}")
        return data

    def _clean_data_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        if 'datetime' in df.columns:
             df.rename(columns={'datetime': 'timestamp'}, inplace=True)
        elif 'date' in df.columns:
            df.rename(columns={'date': 'timestamp'}, inplace=True)
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # If timezone naive, assume UTC or make it configurable
            if df['timestamp'].dt.tz is None:
                 df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        return df

    async def get_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        cache_key = f"yf:price:{symbol}:{start_date.strftime('%Y%m%d')}:{end_date.strftime('%Y%m%d')}:{interval}"
        
        def fetch_yf_history_sync():
            try:
                ticker = yf.Ticker(symbol, session=self.session)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    auto_adjust=False, # Get raw OHLCV, splits, dividends
                    actions=True # Include dividends and splits
                )
                if df.empty:
                    return []
                
                df.reset_index(inplace=True)
                df = self._clean_data_frame(df)

                # Ensure required columns exist, fill with 0 or None if not
                required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                for col in required_cols:
                    if col not in df.columns:
                        df[col] = 0 if col != 'timestamp' else pd.NaT
                
                # Handle potential NaNs from yfinance, convert to None for JSON
                df = df.replace({np.nan: None})

                return [{
                    'timestamp': row['timestamp'].to_pydatetime() if pd.notnull(row['timestamp']) else None,
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'adj_close': row.get('adjusted_close', row.get('adj_close')), # yfinance might change col name
                    'volume': int(row['volume']) if pd.notnull(row['volume']) else 0,
                    'dividends': row.get('dividends'),
                    'stock_splits': row.get('stock_splits')
                } for _, row in df.iterrows()]
            except Exception as e:
                logger.error(f"yfinance history fetch error for {symbol}: {e}")
                return []

        data = await self._fetch_with_cache(cache_key, "price", fetch_yf_history_sync)
        return data if data else []

    async def get_current_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        cache_key = f"yf:quote:{symbol}"

        def fetch_yf_quote_sync():
            try:
                ticker = yf.Ticker(symbol, session=self.session)
                info = ticker.info
                # yfinance info can be slow and sometimes incomplete for "current quote"
                # For more real-time, might need a different approach or accept slight delay
                # Fast info provides some quote like data
                fast_info = ticker.fast_info
                
                return {
                    "symbol": symbol,
                    "price": fast_info.last_price if hasattr(fast_info, 'last_price') else info.get("currentPrice", info.get("regularMarketPrice")),
                    "change": fast_info.last_price - fast_info.previous_close if hasattr(fast_info, 'last_price') and hasattr(fast_info, 'previous_close') else info.get("regularMarketChange"),
                    "change_percent": (fast_info.last_price / fast_info.previous_close - 1) * 100 if hasattr(fast_info, 'last_price') and hasattr(fast_info, 'previous_close') and fast_info.previous_close else info.get("regularMarketChangePercent"),
                    "volume": fast_info.volume if hasattr(fast_info, 'volume') else info.get("volume"),
                    "day_high": fast_info.day_high if hasattr(fast_info, 'day_high') else info.get("dayHigh"),
                    "day_low": fast_info.day_low if hasattr(fast_info, 'day_low') else info.get("dayLow"),
                    "previous_close": fast_info.previous_close if hasattr(fast_info, 'previous_close') else info.get("previousClose"),
                    "market_cap": fast_info.market_cap if hasattr(fast_info, 'market_cap') else info.get("marketCap"),
                    "timestamp": datetime.now().astimezone() # yfinance info doesn't give a quote timestamp
                }
            except Exception as e:
                logger.error(f"yfinance quote fetch error for {symbol}: {e}")
                return None
        
        data = await self._fetch_with_cache(cache_key, "quote", fetch_yf_quote_sync)
        return data

    async def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        cache_key = f"yf:profile:{symbol}"

        def fetch_yf_info_sync():
            try:
                ticker = yf.Ticker(symbol, session=self.session)
                info = ticker.info
                return {
                    "symbol": info.get("symbol"),
                    "name": info.get("longName"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "description": info.get("longBusinessSummary"),
                    "website": info.get("website"),
                    "logo_url": info.get("logo_url"), # Often not available or reliable
                    "country": info.get("country"),
                    "full_time_employees": info.get("fullTimeEmployees"),
                    "address": f"{info.get('address1', '')}, {info.get('city', '')}, {info.get('zip', '')}",
                    "phone": info.get("phone")
                }
            except Exception as e:
                logger.error(f"yfinance profile fetch error for {symbol}: {e}")
                return None
        
        data = await self._fetch_with_cache(cache_key, "profile", fetch_yf_info_sync)
        return data

    async def get_financial_statements(self, symbol: str, statement_type: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        cache_key = f"yf:financials:{symbol}:{statement_type}:{period}:{limit}"

        def fetch_yf_financials_sync():
            try:
                ticker = yf.Ticker(symbol, session=self.session)
                stmt = None
                if statement_type == "income_statement":
                    stmt = ticker.income_stmt if period == "annual" else ticker.quarterly_income_stmt
                elif statement_type == "balance_sheet":
                    stmt = ticker.balance_sheet if period == "annual" else ticker.quarterly_balance_sheet
                elif statement_type == "cash_flow":
                    stmt = ticker.cashflow if period == "annual" else ticker.quarterly_cashflow
                else:
                    return []

                if stmt is None or stmt.empty:
                    return []
                
                stmt = stmt.T # Transpose for easier iteration by date
                stmt.index = pd.to_datetime(stmt.index)
                stmt = stmt.sort_index(ascending=False).head(limit)
                
                # Convert NaN to None for JSON compatibility
                stmt = stmt.replace({np.nan: None})

                return [{
                    "date": index.strftime('%Y-%m-%d'), 
                    **row.to_dict()
                    } for index, row in stmt.iterrows()]
            except Exception as e:
                logger.error(f"yfinance financials fetch error for {symbol} ({statement_type}, {period}): {e}")
                return []

        data = await self._fetch_with_cache(cache_key, "financials", fetch_yf_financials_sync)
        return data if data else []

    async def get_key_financial_ratios(self, symbol: str) -> Optional[Dict[str, Any]]:
        # yfinance `info` dict contains many ratios.
        profile_data = await self.get_company_profile(symbol) # Leverages caching
        if not profile_data: # If profile fetch failed, info is likely unavailable
             # Attempt to get info directly if profile was minimal
            def fetch_info_direct():
                try:
                    return yf.Ticker(symbol, session=self.session).info
                except: return None
            info = await self._fetch_with_cache(f"yf:info_direct:{symbol}", fetch_info_direct)
            if not info: return None
        else: # Use info from profile if available
            info = profile_data # The profile data is essentially the .info dict

        # Extract common ratios, handle missing keys gracefully
        return {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe_ratio": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "peg_ratio": info.get("pegRatio"),
            "dividend_yield": info.get("dividendYield"),
            "eps_trailing_ttm": info.get("trailingEps"),
            "eps_forward": info.get("forwardEps"),
            "return_on_equity": info.get("returnOnEquity"),
            "return_on_assets": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "profit_margin": info.get("profitMargins"), # Note: yfinance calls it profitMargins
            "operating_margin": info.get("operatingMargins"),
            "beta": info.get("beta"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "50_day_ma": info.get("fiftyDayAverage"),
            "200_day_ma": info.get("twoHundredDayAverage"),
        }


    async def get_market_news(
        self,
        symbols: Optional[List[str]] = None,
        topics: Optional[List[str]] = None, # yfinance news is primarily ticker-based
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        # yfinance news is per-ticker. For general news, another source would be better.
        # If multiple symbols, fetch for first one or aggregate (simplifying to first for now)
        target_symbol = symbols[0] if symbols else None
        
        if not target_symbol: # No symbol, yfinance cannot provide general market news easily
            logger.info("YahooFinanceProvider: General market news not directly supported, returning empty.")
            return []

        cache_key = f"yf:news:{target_symbol}:{limit}"
        
        def fetch_yf_news_sync():
            try:
                ticker = yf.Ticker(target_symbol, session=self.session)
                news_items = ticker.news
                if not news_items:
                    return []
                
                processed_news = []
                for item in news_items[:limit]:
                    published_at = None
                    if item.get('providerPublishTime'):
                        try:
                            # Convert Unix timestamp to datetime
                            published_at = datetime.fromtimestamp(item['providerPublishTime']).astimezone()
                        except Exception:
                            pass # Keep None if conversion fails
                    
                    processed_news.append({
                        'title': item.get('title'),
                        'link': item.get('link'),
                        'publisher': item.get('publisher'),
                        'published_at': published_at,
                        'summary': item.get('summary'), # Often not present or short in yf
                        'symbols_mentioned': [target_symbol], # yf news is ticker-specific
                        'thumbnail_url': item.get('thumbnail', {}).get('resolutions', [{}])[0].get('url') if item.get('thumbnail') else None
                    })
                return processed_news
            except Exception as e:
                logger.error(f"yfinance news fetch error for {target_symbol}: {e}")
                return []

        data = await self._fetch_with_cache(cache_key, "news", fetch_yf_news_sync)
        return data if data else []

    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Fetch quotes for multiple symbols efficiently."""
        results = {}
        # Create tasks for all symbols but limit concurrent execution
        async def process_symbol(symbol: str):
            try:
                quote = await self.get_current_quote(symbol)
                results[symbol] = quote
            except Exception as e:
                logger.error(f"Error fetching quote for {symbol}: {e}")
                results[symbol] = None

        # Process in chunks of 5 to avoid overwhelming the API
        chunk_size = 5
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]
            tasks = [process_symbol(symbol) for symbol in chunk]
            await asyncio.gather(*tasks)
        
        return results

    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # yfinance does not have a direct symbol search API.
        # This would typically require a third-party API or a local database of symbols.
        # For a very basic workaround, one might try to fetch info for the query as if it's a symbol.
        logger.warning("YahooFinanceProvider: Symbol search is not directly supported. Returning empty.")
        # Example of a potential (unreliable) workaround:
        # try:
        #     ticker = yf.Ticker(query.upper())
        #     info = ticker.info
        #     if info and info.get('symbol'):
        #         return [{
        #             'symbol': info['symbol'],
        #             'name': info.get('longName', info.get('shortName')),
        #             'exchange': info.get('exchange'),
        #             'type': info.get('quoteType')
        #         }]
        # except:
        #     pass
        return []
