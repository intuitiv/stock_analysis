from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

class MarketDataProvider(ABC):
    @abstractmethod
    async def get_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str # e.g., "1d", "1h", "5m"
    ) -> List[Dict[str, Any]]:
        """
        Fetches historical price data (OHLCV).
        Each item in list: {'timestamp': datetime, 'open': float, 'high': float, 'low': float, 'close': float, 'volume': int}
        """
        pass

    @abstractmethod
    async def get_current_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches the latest quote for a symbol.
        e.g., {'price': float, 'change': float, 'change_percent': float, 'volume': int, 'timestamp': datetime}
        """
        pass

    @abstractmethod
    async def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches company profile information.
        e.g., {'name': str, 'sector': str, 'industry': str, 'description': str, 'website': str, 'logo_url': str}
        """
        pass

    @abstractmethod
    async def get_financial_statements(self, symbol: str, statement_type: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetches financial statements (income, balance_sheet, cash_flow).
        statement_type: 'income_statement', 'balance_sheet', 'cash_flow'
        period: 'annual' or 'quarterly'
        """
        pass

    @abstractmethod
    async def get_key_financial_ratios(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches key financial ratios.
        e.g., {'pe_ratio': float, 'pb_ratio': float, 'eps': float, 'dividend_yield': float, ...}
        """
        pass
        
    @abstractmethod
    async def get_market_news(
        self,
        symbols: Optional[List[str]] = None, # List of symbols or None for general market news
        topics: Optional[List[str]] = None, # e.g., ['earnings', 'ipo']
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetches market news.
        Each item: {'title': str, 'link': str, 'publisher': str, 'published_at': datetime, 'summary': Optional[str], 'symbols_mentioned': List[str]}
        """
        pass

    @abstractmethod
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Searches for stock symbols matching the query.
        Each item: {'symbol': str, 'name': str, 'exchange': str, 'type': str}
        """
        pass
