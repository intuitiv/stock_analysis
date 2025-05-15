import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
import pandas as pd # For date parsing if needed, and potential data manipulation

from app.services.market_data.interface import MarketDataProvider
from app.core.config import settings
from app.core.cache import RedisCache

logger = logging.getLogger(__name__)

class AlphaVantageProvider(MarketDataProvider):
    def __init__(self, cache: Optional[RedisCache] = None):
        self.api_key = str(settings.ALPHA_VANTAGE_API_KEY.get_secret_value()) if settings.ALPHA_VANTAGE_API_KEY else None
        if not self.api_key:
            logger.warning("Alpha Vantage API key not configured. Provider will not function.")
        self.base_url = "https://www.alphavantage.co/query"
        self.cache = cache if cache else RedisCache()
        self.cache_ttl_seconds = settings.MARKET_DATA_CACHE_TTL_SECONDS # e.g., 300

    async def _fetch_with_cache(self, cache_key: str, fetch_func, *args, **kwargs) -> Any:
        if not self.api_key: return kwargs.get("default_return", None) # Don't attempt if no API key

        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit for AV:{cache_key}")
                return cached_data
        except Exception as e:
            logger.error(f"Redis cache GET error for AV:{cache_key}: {e}")
        
        logger.debug(f"Cache miss for AV:{cache_key}. Fetching from source.")
        data = await fetch_func(*args, **kwargs)
        
        if data is not None:
            try:
                # Ensure all datetime objects in data are serialized before caching
                serialized_data_for_cache = self._serialize_datetimes_in_data(data)
                await self.cache.set(cache_key, serialized_data_for_cache, ttl=self.cache_ttl_seconds)
                logger.debug(f"Cached data for AV:{cache_key}")
            except Exception as e:
                logger.error(f"Redis cache SET error for AV:{cache_key}: {e}")
        return data

    def _serialize_datetimes_in_data(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._serialize_datetimes_in_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_datetimes_in_data(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        return data

    async def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.api_key: return None
        # Create a new params dict to avoid modifying the original
        request_params = params.copy()
        request_params["apikey"] = self.api_key
        
        # Log the full request details
        request_url = f"{self.base_url}?{'&'.join(f'{k}={v}' for k, v in request_params.items() if k != 'apikey')}"
        logger.info(f"Making Alpha Vantage request: {request_url} (API key hidden)")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=request_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Log the response structure
                        logger.info(f"Alpha Vantage response keys: {data.keys()}")
                        
                        if "Error Message" in data:
                            logger.error(f"Alpha Vantage API Error: {data['Error Message']} for request: {params.get('function')} - {params.get('symbol')}")
                            return None
                        if "Information" in data and "call frequency" in data["Information"].lower():
                            logger.warning(f"Alpha Vantage API limit reached: {data['Information']}")
                            return None
                        if not data:
                            logger.error(f"Alpha Vantage returned empty response for: {params.get('function')} - {params.get('symbol')}")
                            return None
                        return data
                    else:
                        logger.error(f"Alpha Vantage HTTP Error {response.status} for: {params.get('function')} - {params.get('symbol')}")
                        response_text = await response.text()
                        logger.error(f"Response content: {response_text}")
                        return None
            except aiohttp.ClientError as e:
                logger.error(f"Alpha Vantage request error for {params.get('function')} - {params.get('symbol')}: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error during Alpha Vantage request for {params.get('function')} - {params.get('symbol')}: {e}")
                return None

    async def get_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        av_interval_map = {
            "1d": ("TIME_SERIES_DAILY_ADJUSTED", "Time Series (Daily)"),
            "1wk": ("TIME_SERIES_WEEKLY_ADJUSTED", "Weekly Adjusted Time Series"),
            "1mo": ("TIME_SERIES_MONTHLY_ADJUSTED", "Monthly Adjusted Time Series"),
            # Intraday intervals: '1min', '5min', '15min', '30min', '60min'
        }
        
        av_function: Optional[str] = None
        av_series_key: Optional[str] = None
        av_interval_param: Optional[str] = None

        if interval in av_interval_map:
            av_function, av_series_key = av_interval_map[interval]
        elif "min" in interval:
            av_function = "TIME_SERIES_INTRADAY"
            av_series_key = f"Time Series ({interval})"
            av_interval_param = interval
        else:
            logger.warning(f"Unsupported interval '{interval}' for Alpha Vantage. Defaulting to daily or skipping.")
            return []

        cache_key = f"av:price:{symbol}:{start_date.strftime('%Y%m%d')}:{end_date.strftime('%Y%m%d')}:{interval}"
        
        async def fetch_av_prices_sync():
            params = {"function": av_function, "symbol": symbol, "outputsize": "full"}
            if av_interval_param:
                params["interval"] = av_interval_param
            
            raw_data = await self._make_request(params)
            if not raw_data or not av_series_key or av_series_key not in raw_data:
                return []

            time_series = raw_data[av_series_key]
            processed_data = []
            date_format = '%Y-%m-%d %H:%M:%S' if av_interval_param else '%Y-%m-%d'

            for date_str, values in time_series.items():
                try:
                    dt_obj = datetime.strptime(date_str, date_format)
                    # AlphaVantage data is typically end-of-day for daily, ensure timezone consistency if needed
                    if dt_obj.tzinfo is None:
                         dt_obj = dt_obj.replace(tzinfo=datetime.now().astimezone().tzinfo) # Assume local if naive, or UTC

                    if start_date <= dt_obj <= end_date:
                        processed_data.append({
                            'timestamp': dt_obj.isoformat(),
                            'open': float(values['1. open']),
                            'high': float(values['2. high']),
                            'low': float(values['3. low']),
                            'close': float(values['4. close']),
                            # Adjusted close might be '5. adjusted close', volume '6. volume'
                            'adj_close': float(values.get('5. adjusted close', values['4. close'])),
                            'volume': int(values.get('6. volume', values.get('5. volume', 0)))
                        })
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping malformed data point for {symbol} on {date_str}: {e}")
                    continue
            return sorted(processed_data, key=lambda x: x['timestamp'])

        data = await self._fetch_with_cache(cache_key, fetch_av_prices_sync, default_return=[])
        return data if data else []

    async def get_current_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        cache_key = f"av:quote:{symbol}"

        # Handle market indices specifically
        index_map = {
            "^GSPC": "S&P 500",
            "^IXIC": "NASDAQ 100",
            "^DJI": "DOW JONES"
        }

        async def fetch_av_quote_sync():
            # Map common index symbols to representative ETFs for Alpha Vantage GLOBAL_QUOTE
            etf_map = {
                "^GSPC": "SPY",  # S&P 500 ETF
                "^IXIC": "QQQ",  # Nasdaq 100 ETF
                "^DJI": "DIA",   # Dow Jones ETF
                # Add other common indices if needed
            }
            api_symbol = etf_map.get(symbol, symbol) # Use mapped symbol if available, else original
            
            logger.info(f"Alpha Vantage: Fetching GLOBAL_QUOTE for original symbol '{symbol}' using API symbol '{api_symbol}'")
            params = {"function": "GLOBAL_QUOTE", "symbol": api_symbol}
            data = await self._make_request(params)

            if not data or "Global Quote" not in data or not data["Global Quote"]:
                logger.warning(f"Alpha Vantage: No 'Global Quote' data for API symbol '{api_symbol}' (original: '{symbol}'). Response: {data}")
                return None
            
            quote_data = data["Global Quote"]
            if not quote_data: # Check if the "Global Quote" object itself is empty
                logger.warning(f"Alpha Vantage: Empty 'Global Quote' object for API symbol '{api_symbol}' (original: '{symbol}').")
                return None
            try:
                price = float(quote.get("05. price", 0))
                prev_close = float(quote.get("08. previous close", 0))
                change = float(quote.get("09. change", 0))
                change_percent = float(quote.get("10. change percent", "0").rstrip('%'))
                
                latest_trading_day_str = quote.get("07. latest trading day")
                timestamp = datetime.strptime(latest_trading_day_str, '%Y-%m-%d').replace(tzinfo=datetime.now().astimezone().tzinfo) if latest_trading_day_str else datetime.now().astimezone()


                result = {
                    "symbol": symbol, # Return with the original queried symbol
                    "name": index_map.get(symbol, quote_data.get("01. symbol")), # Use mapped name for indices or AV name
                    "price": price,
                    "change": change,
                    "change_percent": change_percent,
                    "volume": int(quote.get("06. volume", 0)),
                    "day_high": float(quote.get("03. high", 0)),
                    "day_low": float(quote.get("04. low", 0)),
                    "previous_close": prev_close,
                    "timestamp": timestamp.isoformat()
                }
                
                if result["symbol"] in index_map:
                    result["name"] = index_map[result["symbol"]]  # Add index name if it's an index
                
                return result
            except (ValueError, TypeError, KeyError) as e:
                logger.error(f"Error parsing Alpha Vantage quote for {symbol}: {e}. Data: {quote_data}") # Ensure this uses quote_data
                return None
        
        data = await self._fetch_with_cache(cache_key, fetch_av_quote_sync)
        return data

    async def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        cache_key = f"av:profile:{symbol}"

        async def fetch_av_profile_sync():
            params = {"function": "OVERVIEW", "symbol": symbol}
            data = await self._make_request(params)
            if not data or data.get("Symbol") is None : # Check if symbol is in response, indicates valid data
                return None
            
            return {
                "symbol": data.get("Symbol"),
                "name": data.get("Name"),
                "sector": data.get("Sector"),
                "industry": data.get("Industry"),
                "description": data.get("Description"),
                "website": data.get("WebsitURL"), # Note: AV key might be WebsiteURL or similar
                "logo_url": None, # Alpha Vantage OVERVIEW doesn't typically provide logo
                "country": data.get("Country"),
                "exchange": data.get("Exchange"),
                "currency": data.get("Currency"),
                "market_cap": int(data.get("MarketCapitalization", 0)) if data.get("MarketCapitalization") != "None" else None,
                "full_time_employees": int(data.get("FullTimeEmployees",0)) if data.get("FullTimeEmployees") and data.get("FullTimeEmployees") != "None" else None,
            }
        
        data = await self._fetch_with_cache(cache_key, fetch_av_profile_sync)
        return data

    async def get_financial_statements(self, symbol: str, statement_type: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        statement_map = {
            "income_statement": "INCOME_STATEMENT",
            "balance_sheet": "BALANCE_SHEET",
            "cash_flow": "CASH_FLOW"
        }
        if statement_type not in statement_map:
            return []
        
        av_function = statement_map[statement_type]
        cache_key = f"av:financials:{symbol}:{av_function}:{period}:{limit}"

        async def fetch_av_financials_sync():
            params = {"function": av_function, "symbol": symbol}
            raw_data = await self._make_request(params)
            
            if not raw_data: return []
            
            report_key = f"{period}Reports" if period == "annual" else "quarterlyReports"
            if report_key not in raw_data or not raw_data[report_key]:
                return []

            reports = raw_data[report_key][:limit]
            processed_reports = []
            for report in reports:
                # Convert numeric strings to numbers, None for "None" or empty strings
                processed_report = {}
                for key, value in report.items():
                    if isinstance(value, str):
                        if value == "None" or value == "-":
                            processed_report[key] = None
                        else:
                            try:
                                processed_report[key] = float(value) if '.' in value else int(value)
                            except ValueError:
                                processed_report[key] = value # Keep as string if not numeric
                    else:
                        processed_report[key] = value
                processed_reports.append(processed_report)
            return processed_reports

        data = await self._fetch_with_cache(cache_key, fetch_av_financials_sync, default_return=[])
        return data if data else []


    async def get_key_financial_ratios(self, symbol: str) -> Optional[Dict[str, Any]]:
        # Alpha Vantage OVERVIEW endpoint contains many ratios
        profile_data = await self.get_company_profile(symbol) # Leverages caching
        if not profile_data:
            return None
        
        # Extract ratios from profile data (which is from OVERVIEW endpoint)
        return {
            "pe_ratio": float(profile_data.get("PERatio", 0)) if profile_data.get("PERatio") not in [None, "None"] else None,
            "forward_pe_ratio": float(profile_data.get("ForwardPE", 0)) if profile_data.get("ForwardPE") not in [None, "None"] else None,
            "pb_ratio": float(profile_data.get("PriceToBookRatio", 0)) if profile_data.get("PriceToBookRatio") not in [None, "None"] else None,
            "ps_ratio": float(profile_data.get("PriceToSalesRatioTTM", 0)) if profile_data.get("PriceToSalesRatioTTM") not in [None, "None"] else None,
            "peg_ratio": float(profile_data.get("PEGRatio", 0)) if profile_data.get("PEGRatio") not in [None, "None"] else None,
            "dividend_yield": float(profile_data.get("DividendYield", 0)) if profile_data.get("DividendYield") not in [None, "None"] else None,
            "eps_trailing_ttm": float(profile_data.get("EPS", 0)) if profile_data.get("EPS") not in [None, "None"] else None,
            "beta": float(profile_data.get("Beta", 0)) if profile_data.get("Beta") not in [None, "None"] else None,
            "profit_margin": float(profile_data.get("ProfitMargin", 0)) if profile_data.get("ProfitMargin") not in [None, "None"] else None,
            "operating_margin_ttm": float(profile_data.get("OperatingMarginTTM", 0)) if profile_data.get("OperatingMarginTTM") not in [None, "None"] else None,
            "return_on_equity_ttm": float(profile_data.get("ReturnOnEquityTTM", 0)) if profile_data.get("ReturnOnEquityTTM") not in [None, "None"] else None,
            "return_on_assets_ttm": float(profile_data.get("ReturnOnAssetsTTM", 0)) if profile_data.get("ReturnOnAssetsTTM") not in [None, "None"] else None,
            "52_week_high": float(profile_data.get("52WeekHigh", 0)) if profile_data.get("52WeekHigh") not in [None, "None"] else None,
            "52_week_low": float(profile_data.get("52WeekLow", 0)) if profile_data.get("52WeekLow") not in [None, "None"] else None,
            "50_day_ma": float(profile_data.get("50DayMovingAverage", 0)) if profile_data.get("50DayMovingAverage") not in [None, "None"] else None,
            "200_day_ma": float(profile_data.get("200DayMovingAverage", 0)) if profile_data.get("200DayMovingAverage") not in [None, "None"] else None,
        }

    async def get_market_news(
        self,
        symbols: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"function": "NEWS_SENTIMENT", "limit": str(min(limit, 1000))} # AV max limit is 1000
        if symbols:
            params["tickers"] = ",".join(symbols)
        if topics:
            params["topics"] = ",".join(topics)
        
        # If no symbols or topics, AV might require one. Default to broad market topics.
        if not symbols and not topics:
            params["topics"] = "technology,financial_markets,economy_fiscal" # Example broad topics

        cache_key = f"av:news:{params.get('tickers','general')}:{params.get('topics','all')}:{limit}"

        async def fetch_av_news_sync():
            data = await self._make_request(params)
            if not data or "feed" not in data:
                return []
            
            news_items = []
            for item in data["feed"]: # AV already limits by 'limit' param in request
                published_dt = None
                time_str = item.get("time_published") # Format: "20231026T153000"
                if time_str:
                    try:
                        published_dt = datetime.strptime(time_str, "%Y%m%dT%H%M%S").replace(tzinfo=datetime.now().astimezone().tzinfo)
                    except ValueError:
                        logger.warning(f"Could not parse news time_published: {time_str}")
                
                mentioned_symbols = [ticker_sentiment['ticker'] for ticker_sentiment in item.get('ticker_sentiment', [])]

                news_items.append({
                    'title': item.get('title'),
                    'link': item.get('url'),
                    'publisher': item.get('source'),
                    'published_at': published_dt.isoformat() if published_dt else None,
                    'summary': item.get('summary'),
                    'banner_image': item.get('banner_image'),
                    'overall_sentiment_score': item.get('overall_sentiment_score'),
                    'overall_sentiment_label': item.get('overall_sentiment_label'),
                    'symbols_mentioned': mentioned_symbols
                })
            return news_items

        data = await self._fetch_with_cache(cache_key, fetch_av_news_sync, default_return=[])
        return data if data else []

    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        cache_key = f"av:search:{query}:{limit}"

        async def fetch_av_search_sync():
            params = {"function": "SYMBOL_SEARCH", "keywords": query}
            data = await self._make_request(params)
            if not data or "bestMatches" not in data:
                return []
            
            results = []
            for match in data["bestMatches"][:limit]:
                results.append({
                    "symbol": match.get("1. symbol"),
                    "name": match.get("2. name"),
                    "type": match.get("3. type"),
                    "region": match.get("4. region"),
                    "exchange": match.get("7. exchange", match.get("marketOpen") + "-" + match.get("marketClose")), # Exchange not always directly available
                    "currency": match.get("8. currency"),
                })
            return results
            
        data = await self._fetch_with_cache(cache_key, fetch_av_search_sync, default_return=[])
        return data if data else []
