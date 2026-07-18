"""API routes initialization."""
from fastapi import APIRouter

# Import route modules
from .auth import router as auth_router
from .market import router as market_router
from .stocks import router as stocks_router
from .analysis import router as analysis_router
from .portfolio import router as portfolio_router

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(market_router, prefix="/market", tags=["market"])
api_router.include_router(stocks_router, prefix="/stocks", tags=["stocks"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])

__all__ = [
    'api_router',
    'auth_router',
    'market_router',
    'stocks_router',
    'analysis_router',
    'portfolio_router',
]
