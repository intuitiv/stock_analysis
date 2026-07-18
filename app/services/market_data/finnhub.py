import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from app.services.market_data.interface import MarketDataProvider
from app.core.cache import RedisCache
from app.core.config import settings

logger = logging.getLogger(__name__)

FINNHUB_API_BASE_URL = "https://finnhub.io/api/v1"

class FinnhubProvider(MarketDataProvider):
    def __init__(self, cache: Optional[RedisCache] = None):
        self.api_key = settings.FINNHUB_API_KEY.get_secret_value() if settings.FINNHUB_API_KEY else None
        if not self.api_key:
            logger.error("Finnhub API key is not configured. FinnhubProvider will not be functional.")
            # You might want to raise an error here or handle it gracefully
            # For now, it will lead to errors when methods are called without an API key.
        self.cache = cache if cache else RedisCache()
        self.session = None # Will be created in an async context

        # Cache TTLs for different Finnhub data types (in seconds)
        self.cache_ttls = {
            "quote": 60,          # 1 minute
            "profile": 86400,     # 24 hours
            "candles": 300,       # 5 minutes for historical candles
            "news": 300,          # 5 minutes
            "search": 3600 * 6,   # 6 hours for symbol search
        }
        # Finnhub rate limits: https://finnhub.io/docs/api#rate-limit
        # Free plan: 60 API calls/minute. We should implement rate limiting.
        # For simplicity in this initial implementation, direct calls are made.
        # A proper implementation would use a RateLimiter similar to YahooFinanceProvider.

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            # Consider adding timeout configurations here from settings
            # timeout = aiohttp.ClientTimeout(total=settings.MARKET_DATA_API_TIMEOUT_SECONDS)
            self.session = aiohttp.ClientSession()
        return self.session

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            logger.error(f"Finnhub API key not available. Cannot make request to {endpoint}.")
            return None

        session = await self._get_session()
        url = f"{FINNHUB_API_BASE_URL}{endpoint}"
        request_params = params if params else {}
        request_params['token'] = self.api_key
        
        try:
            logger.debug(f"Requesting Finnhub: {url} with params: {request_params}")
            async with session.get(url, params=request_params) as response:
                response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
                data = await response.json()
                logger.debug(f"Finnhub response for {endpoint}: {str(data)[:200]}...") # Log snippet
                return data
        except aiohttp.ClientResponseError as e:
            logger.error(f"Finnhub API error for {url} (status: {e.status}): {e.message}")
        except aiohttp.ClientError as e: # Other client errors (network, etc.)
            logger.error(f"Finnhub connection error for {url}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Finnhub JSON decode error for {url}: {e}. Response text: {await response.text()[:200]}")
        except Exception as e:
            logger.error(f"Unexpected error during Finnhub request to {url}: {e}")
        return None

    async def _fetch_with_cache(self, cache_key: str, data_type: str, fetch_func, *args, **kwargs) -> Any:
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit for Finnhub data: {cache_key}")
                return cached_data
        except Exception as e:
            logger.error(f"Redis cache GET error for Finnhub {cache_key}: {e}")
        
        logger.debug(f"Cache miss for Finnhub {cache_key}. Fetching from source.")
        data = await fetch_func(*args, **kwargs)
        
        if data is not None: # Also consider checking for empty dicts/lists if API returns that for "not found"
            try:
                await self.cache.set(cache_key, data, ttl=self.cache_ttls.get(data_type, 300))
                logger.debug(f"Cached Finnhub data for {cache_key}")
            except Exception as e:
                logger.error(f"Redis cache SET error for Finnhub {cache_key}: {e}")
        return data

    async def get_current_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        cache_key = f"finnhub:quote:{symbol}"
        
        async def fetch_live_quote():
            data = await self._request("/quote", params={"symbol": symbol})
            if not data:
                logger.warning(f"No data from Finnhub quote for {symbol}")
                return None
            if isinstance(data, dict) and "error" in data and "subscription required" in data["error"].lower():
                logger.warning(f"Finnhub subscription required for {symbol}: {data['error']}")
                return {"error_type": "SUBSCRIPTION_REQUIRED", "provider": "finnhub", "symbol": symbol, "message": data["error"]}
            
            if 'c' not in data: # 'c' is current price
                logger.warning(f"No current price ('c') in Finnhub quote response for {symbol}: {data}")
                # Potentially return a different marker or None if data is present but malformed
                return None # Or a specific error marker for malformed data
            return {
                "symbol": symbol,
                "price": data.get("c"),
                "change": data.get("d"),
                "change_percent": data.get("dp"),
                "day_high": data.get("h"),
                "day_low": data.get("l"),
                "open": data.get("o"),
                "previous_close": data.get("pc"),
                "timestamp": datetime.fromtimestamp(data.get("t")) if data.get("t") else datetime.now().astimezone(),
                # Finnhub quote doesn't include volume or market cap directly
                "volume": None, 
                "market_cap": None,
            }
        return await self._fetch_with_cache(cache_key, "quote", fetch_live_quote)

    async def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        cache_key = f"finnhub:profile:{symbol}"

        async def fetch_live_profile():
            # Finnhub has /stock/profile2 for general profile
            profile_data = await self._request("/stock/profile2", params={"symbol": symbol})
            if not profile_data or not isinstance(profile_data, dict):
                logger.warning(f"No profile data or unexpected format from Finnhub for {symbol}: {profile_data}")
                return None
            
            return {
                "symbol": profile_data.get("ticker"),
                "name": profile_data.get("name"),
                "sector": profile_data.get("finnhubIndustry"), # Finnhub calls it industry
                "industry": profile_data.get("industry"), # May need to map if different from sector
                "description": profile_data.get("description"), # Not directly in profile2, might need /company-news
                "website": profile_data.get("weburl"),
                "logo_url": profile_data.get("logo"),
                "country": profile_data.get("country"),
                "exchange": profile_data.get("exchange"),
                "market_cap": profile_data.get("marketCapitalization"),
                # Other fields like employees, address are not in profile2
            }
        return await self._fetch_with_cache(cache_key, "profile", fetch_live_profile)

    async def get_price_data(self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "D") -> List[Dict[str, Any]]:
        # Finnhub interval mapping: 1, 5, 15, 30, 60, D, W, M
        # Our '1d' maps to 'D', '1wk' to 'W', '1mo' to 'M'
        resolution_map = {"1d": "D", "1wk": "W", "1mo": "M", "D": "D", "W": "W", "M": "M"}
        finnhub_resolution = resolution_map.get(interval, "D")
        
        cache_key = f"finnhub:candles:{symbol}:{start_date.strftime('%Y%m%d')}:{end_date.strftime('%Y%m%d')}:{finnhub_resolution}"

        async def fetch_live_candles():
            params = {
                "symbol": symbol,
                "resolution": finnhub_resolution,
                "from": int(start_date.timestamp()),
                "to": int(end_date.timestamp())
            }
            data = await self._request("/stock/candle", params=params)
            if not data or data.get("s") != "ok":
                logger.warning(f"Failed to fetch candles or no data for {symbol} from Finnhub: {data}")
                return []

            processed_candles = []
            timestamps = data.get("t", [])
            opens = data.get("o", [])
            highs = data.get("h", [])
            lows = data.get("l", [])
            closes = data.get("c", [])
            volumes = data.get("v", [])

            for i in range(len(timestamps)):
                processed_candles.append({
                    "timestamp": datetime.fromtimestamp(timestamps[i]).astimezone(),
                    "open": opens[i] if i < len(opens) else None,
                    "high": highs[i] if i < len(highs) else None,
                    "low": lows[i] if i < len(lows) else None,
                    "close": closes[i] if i < len(closes) else None,
                    "volume": int(volumes[i]) if i < len(volumes) else 0,
                    "adj_close": closes[i] if i < len(closes) else None, # Finnhub candles are typically adjusted
                })
            return processed_candles
        return await self._fetch_with_cache(cache_key, "candles", fetch_live_candles)

    async def get_market_news(self, symbols: Optional[List[str]] = None, topics: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
        # Finnhub uses 'category' for general news, or symbol for company news
        # For simplicity, if symbols are provided, use the first symbol for company news.
        # Otherwise, fetch general market news.
        
        params = {"count": limit}
        endpoint = "/news"
        cache_type = "general_news"
        
        if symbols and symbols[0]:
            params["symbol"] = symbols[0]
            endpoint = "/company-news" # Finnhub endpoint for company specific news
            cache_type = f"company_news_{symbols[0]}"
        else:
            params["category"] = "general" # Default to general news if no symbol
        
        cache_key = f"finnhub:{cache_type}:{limit}"

        async def fetch_live_news():
            news_items = await self._request(endpoint, params=params)
            if not news_items or not isinstance(news_items, list):
                logger.warning(f"No news items or unexpected format from Finnhub for {params}: {news_items}")
                return []
            
            processed_news = []
            for item in news_items:
                processed_news.append({
                    'title': item.get('headline'),
                    'link': item.get('url'),
                    'publisher': item.get('source'),
                    'published_at': datetime.fromtimestamp(item.get('datetime')).astimezone() if item.get('datetime') else None,
                    'summary': item.get('summary'),
                    'symbols_mentioned': [item.get('related')] if item.get('related') and item.get('related') != params.get("symbol") else (symbols or []), # Finnhub 'related' can be the symbol itself
                    'thumbnail_url': item.get('image')
                })
            return processed_news
        return await self._fetch_with_cache(cache_key, "news", fetch_live_news)

    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        cache_key = f"finnhub:search:{query}:{limit}"
        
        async def fetch_live_search():
            data = await self._request("/search", params={"q": query})
            if not data or not data.get("result"):
                logger.warning(f"No search results from Finnhub for query '{query}': {data}")
                return []
            
            results = []
            for item in data["result"][:limit]:
                results.append({
                    "symbol": item.get("symbol"),
                    "name": item.get("description"), # Finnhub 'description' is often the name
                    "exchange": None, # Finnhub search doesn't always provide exchange directly
                    "type": item.get("type")
                })
            return results
        return await self._fetch_with_cache(cache_key, "search", fetch_live_search)

    # Placeholder implementations for other interface methods
    async def get_financial_statements(self, symbol: str, statement_type: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        logger.warning("FinnhubProvider: get_financial_statements not fully implemented yet.")
        # Example endpoint: /stock/financials-reported?symbol=AAPL&freq=annual
        # Needs parsing of complex JSON structure.
        return []

    async def get_key_financial_ratios(self, symbol: str) -> Optional[Dict[str, Any]]:
        logger.warning("FinnhubProvider: get_key_financial_ratios not fully implemented yet.")
        # Example endpoint: /stock/metric?symbol=AAPL&metric=all
        # Needs parsing and mapping of metrics.
        return None

    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        # Finnhub free plan is 1 API call per second. Batching needs care.
        # For simplicity, call get_current_quote sequentially with small delay.
        results = {}
        for symbol in symbols:
            results[symbol] = await self.get_current_quote(symbol)
            await asyncio.sleep(1.1) # Respect 1 call/sec limit for free tier
        return results

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
            logger.info("FinnhubProvider: aiohttp session closed.")