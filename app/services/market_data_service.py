"""Market Data Service for managing and coordinating different market data providers."""
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import Depends

from app.services.market_data.interface import MarketDataProvider
from app.services.market_data.yahoo_finance import YahooFinanceProvider
from app.services.market_data.alpha_vantage import AlphaVantageProvider
from app.services.market_data.finnhub import FinnhubProvider
from app.core.config import settings
from app.core.cache import RedisCache
import logging

logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(self, cache: Optional[RedisCache] = None):
        """Initialize the market data service with optional cache."""
        self.cache = cache if cache else RedisCache()
        self.providers: Dict[str, MarketDataProvider] = {}
        self.default_provider_name = settings.MARKET_DATA_PROVIDER.lower()
        self._setup_providers()

    def _setup_providers(self) -> None:
        """Set up market data providers based on configuration."""
        if settings.ALPHA_VANTAGE_ENABLED and settings.ALPHA_VANTAGE_API_KEY:
            self.providers["alpha_vantage"] = AlphaVantageProvider(cache=self.cache)
            logger.info("AlphaVantageProvider initialized.")
        else:
            logger.info("AlphaVantageProvider is disabled or API key is missing.")

        if settings.FINNHUB_ENABLED and settings.FINNHUB_API_KEY:
            self.providers["finnhub"] = FinnhubProvider(cache=self.cache)
            logger.info("FinnhubProvider initialized.")
        else:
            logger.info("FinnhubProvider is disabled or API key is missing.")

        if settings.YAHOO_FINANCE_ENABLED:
            self.providers["yahoo_finance"] = YahooFinanceProvider(cache=self.cache)
            logger.info("YahooFinanceProvider initialized.")
        else:
            logger.info("YahooFinanceProvider is disabled.")

        if not self.providers:
            raise ValueError("No market data providers are enabled or configured correctly.")

        if self.default_provider_name not in self.providers:
            original_default = self.default_provider_name
            self.default_provider_name = list(self.providers.keys())[0]
            logger.warning(f"Default market data provider '{original_default}' not available. Falling back to '{self.default_provider_name}'.")

        logger.info(f"MarketDataService initialized with providers: {list(self.providers.keys())}")

    def _get_provider(self, provider_name: Optional[str] = None) -> MarketDataProvider:
        """Get the specified provider or fall back to default."""
        name_to_use = provider_name.lower() if provider_name else self.default_provider_name
        provider = self.providers.get(name_to_use)
        
        if not provider:
            if provider_name and name_to_use != self.default_provider_name:
                logger.warning(f"Requested provider '{name_to_use}' not available. Trying default '{self.default_provider_name}'.")
                provider = self.providers.get(self.default_provider_name)
            
            if not provider:
                raise ValueError(f"Market data provider '{name_to_use}' (and default) not found or not configured.")
        return provider

    async def get_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
        provider_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        provider = self._get_provider(provider_name)
        try:
            return await provider.get_price_data(symbol, start_date, end_date, interval)
        except Exception as e:
            logger.error(f"Error fetching price data from {provider.__class__.__name__} for {symbol}: {str(e)}")
            if provider_name and provider_name.lower() != self.default_provider_name:
                logger.info(f"Falling back to default provider {self.default_provider_name} for price data.")
                default_provider = self._get_provider()
                if default_provider != provider:
                    try:
                        return await default_provider.get_price_data(symbol, start_date, end_date, interval)
                    except Exception as e_fallback:
                        logger.error(f"Fallback provider {default_provider.__class__.__name__} also failed: {str(e_fallback)}")
            return []

    async def close(self) -> None:
        """Close any open connections."""
        await self.close_all_provider_sessions()
        if hasattr(self.cache, "close"):
            await self.cache.close()

    # Rest of the methods remain unchanged
    # (Methods: get_current_quote, get_company_profile, get_financial_statements, 
    #  get_key_financial_ratios, get_market_news, search_symbols, close_all_provider_sessions)
