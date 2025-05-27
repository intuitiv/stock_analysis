"""
NAETRA Services Package

Service layer components for business logic implementation.
Uses lazy imports to avoid circular dependencies.
"""
from typing import TYPE_CHECKING

# Import only what's needed for type hints
if TYPE_CHECKING:
    from .user_service import UserService
    from .analysis_service import AnalysisService
    from .portfolio_service import PortfolioService
    from .market_data_service import MarketDataService
    from .chat_service import ChatService

def get_user_service():
    """Get UserService instance (lazy import)"""
    from .user_service import UserService
    return UserService

def get_analysis_service():
    """Get AnalysisService instance (lazy import)"""
    from .analysis_service import AnalysisService
    return AnalysisService

def get_portfolio_service():
    """Get PortfolioService instance (lazy import)"""
    from .portfolio_service import PortfolioService
    return PortfolioService

def get_market_data_service():
    """Get MarketDataService instance (lazy import)"""
    from .market_data_service import MarketDataService
    return MarketDataService

def get_chat_service():
    """Get ChatService instance (lazy import)"""
    from .chat_service import ChatService
    return ChatService

__all__ = [
    'get_user_service',
    'get_analysis_service',
    'get_portfolio_service',
    'get_market_data_service',
    'get_chat_service',
]
