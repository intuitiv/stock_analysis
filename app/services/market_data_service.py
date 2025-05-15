from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import Depends # For potential future use if service is injected directly into routes

from app.services.market_data.interface import MarketDataProvider
from app.services.market_data.yahoo_finance import YahooFinanceProvider
from app.services.market_data.alpha_vantage import AlphaVantageProvider
from app.services.market_data.finnhub import FinnhubProvider # Import FinnhubProvider
# Import other providers like SEC Edgar if implemented
# from app.services.market_data.sec_edgar import SECEdgarProvider
from app.core.config import settings
from app.core.cache import RedisCache
import logging # Import logging

logger = logging.getLogger(__name__) # Add logger for this module

class MarketDataService:
    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache if cache else RedisCache()
        
        self.providers: Dict[str, MarketDataProvider] = {}
        # Temporarily disable Yahoo Finance as per user request
        # if settings.YAHOO_FINANCE_ENABLED:
        #     self.providers["yahoo_finance"] = YahooFinanceProvider(cache=self.cache)
        #     logger.info("YahooFinanceProvider initialized.")
        # else:
        #     logger.info("YahooFinanceProvider is disabled by settings.")

        if settings.ALPHA_VANTAGE_ENABLED and settings.ALPHA_VANTAGE_API_KEY:
            self.providers["alpha_vantage"] = AlphaVantageProvider(cache=self.cache)
            logger.info("AlphaVantageProvider initialized.")
        else:
            logger.info("AlphaVantageProvider is disabled or API key is missing.")
        if settings.FINNHUB_ENABLED and settings.FINNHUB_API_KEY: # Check if enabled and API key exists
            self.providers["finnhub"] = FinnhubProvider(cache=self.cache)
        # if settings.SEC_EDGAR_ENABLED:
        #     self.providers["sec_edgar"] = SECEdgarProvider(cache=self.cache)

        self.default_provider_name = settings.MARKET_DATA_PROVIDER.lower()
        
        if not self.providers:
            raise ValueError("No market data providers are enabled or configured correctly.")
        
        if self.default_provider_name not in self.providers:
            # Fallback to the first available provider if default is not configured/enabled
            original_default = settings.MARKET_DATA_PROVIDER.lower()
            self.default_provider_name = list(self.providers.keys())[0]
            logger.warning(f"Default market data provider '{original_default}' not available or not configured. Falling back to '{self.default_provider_name}'.")
        
        logger.info(f"MarketDataService initialized. Default provider: {self.default_provider_name}. Available: {list(self.providers.keys())}")

    def _get_provider(self, provider_name: Optional[str] = None) -> MarketDataProvider:
        name_to_use = provider_name.lower() if provider_name else self.default_provider_name
        provider = self.providers.get(name_to_use)
        
        if not provider:
            # If the specifically requested provider is not available, try the default
            if provider_name and name_to_use != self.default_provider_name:
                logger.warning(f"Requested provider '{name_to_use}' not available. Trying default '{self.default_provider_name}'.")
                provider = self.providers.get(self.default_provider_name)
            
            if not provider: # If default is also not available (should be caught by init, but defensive)
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
            # Fallback logic if primary provider fails and it wasn't the default one already
            if provider_name and provider_name.lower() != self.default_provider_name:
                logger.info(f"Falling back to default provider {self.default_provider_name} for price data.")
                default_provider = self._get_provider() # Gets default
                if default_provider != provider: # Ensure it's a different provider
                    try:
                        return await default_provider.get_price_data(symbol, start_date, end_date, interval)
                    except Exception as e_fallback:
                        logger.error(f"Fallback provider {default_provider.__class__.__name__} also failed for price data: {str(e_fallback)}")
            return [] # Return empty list if all attempts fail

    async def get_current_quote(self, symbol: str, provider_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        provider = self._get_provider(provider_name)
        try:
            data = await provider.get_current_quote(symbol)
            
            # Check for specific "SUBSCRIPTION_REQUIRED" error from Finnhub (or other providers)
            if isinstance(data, dict) and data.get("error_type") == "SUBSCRIPTION_REQUIRED":
                logger.warning(f"Provider {provider.__class__.__name__} requires subscription for {symbol}. Attempting Alpha Vantage fallback.")
                if "alpha_vantage" in self.providers and provider.__class__.__name__ != "AlphaVantageProvider":
                    av_provider = self.providers["alpha_vantage"]
                    try:
                        logger.info(f"Attempting targeted fallback to AlphaVantage for {symbol} quote.")
                        av_data = await av_provider.get_current_quote(symbol)
                        if av_data and not (isinstance(av_data, dict) and av_data.get("error_type")): # Check if AV also returned an error marker
                            return av_data
                        else:
                            logger.warning(f"AlphaVantage fallback for {symbol} also failed or returned no data/error: {av_data}")
                    except Exception as e_av_fallback:
                        logger.error(f"AlphaVantage targeted fallback for {symbol} quote failed: {e_av_fallback}")
                # If Alpha Vantage fallback fails or is not applicable, return the original error marker or None
                return data # Or return None if we don't want to propagate the error marker
            
            return data # Return data if not a subscription error
            
        except Exception as e:
            logger.error(f"Error fetching current quote from {provider.__class__.__name__} for {symbol}: {e}")
            # Generic fallback logic if a non-specific error occurred or targeted fallback failed
            if provider_name and provider_name.lower() != self.default_provider_name:
                logger.info(f"Falling back to default provider {self.default_provider_name} for {symbol} current quote.")
                default_provider = self._get_provider() # Gets default
                if default_provider != provider: # Ensure it's a different provider
                    try:
                        return await default_provider.get_current_quote(symbol)
                    except Exception as e_fallback:
                        logger.error(f"Default fallback provider {default_provider.__class__.__name__} also failed for {symbol} current quote: {e_fallback}")
            return None # Return None if all attempts fail

    async def get_company_profile(self, symbol: str, provider_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        provider = self._get_provider(provider_name)
        try:
            return await provider.get_company_profile(symbol)
        except Exception as e:
            logger.error(f"Error fetching company profile from {provider.__class__.__name__} for {symbol}: {str(e)}")
            if provider_name and provider_name.lower() != self.default_provider_name:
                logger.info(f"Falling back to default provider {self.default_provider_name} for company profile.")
                default_provider = self._get_provider()
                if default_provider != provider:
                    try:
                        return await default_provider.get_company_profile(symbol)
                    except Exception as e_fallback:
                        logger.error(f"Fallback provider {default_provider.__class__.__name__} also failed for company profile: {str(e_fallback)}")
            return None

    async def get_financial_statements(
        self, 
        symbol: str, 
        statement_type: str, 
        period: str = "annual", 
        limit: int = 5,
        provider_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        provider = self._get_provider(provider_name)
        try:
            return await provider.get_financial_statements(symbol, statement_type, period, limit)
        except Exception as e:
            logger.error(f"Error fetching financial statements from {provider.__class__.__name__} for {symbol}: {str(e)}")
            if provider_name and provider_name.lower() != self.default_provider_name:
                logger.info(f"Falling back to default provider {self.default_provider_name} for financial statements.")
                default_provider = self._get_provider()
                if default_provider != provider:
                    try:
                        return await default_provider.get_financial_statements(symbol, statement_type, period, limit)
                    except Exception as e_fallback:
                        logger.error(f"Fallback provider {default_provider.__class__.__name__} also failed for financial statements: {str(e_fallback)}")
            return []

    async def get_key_financial_ratios(self, symbol: str, provider_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        provider = self._get_provider(provider_name)
        try:
            return await provider.get_key_financial_ratios(symbol)
        except Exception as e:
            logger.error(f"Error fetching key financial ratios from {provider.__class__.__name__} for {symbol}: {str(e)}")
            if provider_name and provider_name.lower() != self.default_provider_name:
                logger.info(f"Falling back to default provider {self.default_provider_name} for key ratios.")
                default_provider = self._get_provider()
                if default_provider != provider:
                    try:
                        return await default_provider.get_key_financial_ratios(symbol)
                    except Exception as e_fallback:
                        logger.error(f"Fallback provider {default_provider.__class__.__name__} also failed for key ratios: {str(e_fallback)}")
            return None
        
    async def get_market_news(
        self,
        symbols: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        limit: int = 20,
        provider_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        provider = self._get_provider(provider_name)
        try:
            return await provider.get_market_news(symbols, topics, limit)
        except Exception as e:
            logger.error(f"Error fetching market news from {provider.__class__.__name__}: {str(e)}")
            if provider_name and provider_name.lower() != self.default_provider_name:
                logger.info(f"Falling back to default provider {self.default_provider_name} for market news.")
                default_provider = self._get_provider()
                if default_provider != provider:
                    try:
                        return await default_provider.get_market_news(symbols, topics, limit)
                    except Exception as e_fallback:
                        logger.error(f"Fallback provider {default_provider.__class__.__name__} also failed for market news: {str(e_fallback)}")
            return []

    async def search_symbols(self, query: str, limit: int = 10, provider_name: Optional[str] = None) -> List[Dict[str, Any]]:
        provider = self._get_provider(provider_name)
        try:
            return await provider.search_symbols(query, limit)
        except Exception as e:
            logger.error(f"Error searching symbols from {provider.__class__.__name__} for query '{query}': {str(e)}")
            if provider_name and provider_name.lower() != self.default_provider_name:
                logger.info(f"Falling back to default provider {self.default_provider_name} for symbol search.")
                default_provider = self._get_provider()
                if default_provider != provider:
                    try:
                        return await default_provider.search_symbols(query, limit)
                    except Exception as e_fallback:
                        logger.error(f"Fallback provider {default_provider.__class__.__name__} also failed for symbol search: {str(e_fallback)}")
            return []

    async def close_all_provider_sessions(self):
        """Closes any open sessions for all configured providers."""
        for provider_name, provider_instance in self.providers.items():
            if hasattr(provider_instance, "close_session") and callable(getattr(provider_instance, "close_session")):
                try:
                    await provider_instance.close_session()
                    # logger.info(f"Closed session for {provider_name} provider.") # Add logger if available
                except Exception as e:
                    logger.error(f"Error closing session for {provider_name} provider: {str(e)}")


# Example of how to get an instance (e.g., for FastAPI dependency injection)
# market_data_service_instance = MarketDataService()
# def get_market_data_service():
#     return market_data_service_instance
# Then in API routes: market_service: MarketDataService = Depends(get_market_data_service)
