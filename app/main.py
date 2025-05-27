import logging
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.database import async_engine, Base, get_db # Using async_engine instead of sync_engine
# Import all models to ensure they are registered with Base.metadata before create_all
import app.models # This should import __init__.py which imports all models

# Import services and CHAETRA for dependency injection setup
from app.core.cache import RedisCache
from app.chaetra.llm import LLMManager
from app.chaetra.memory import MemorySystem
from app.chaetra.learning import LearningSystem
from app.chaetra.reasoning import ReasoningSystem
from app.chaetra.opinion import OpinionSystem
from app.chaetra.brain import CHAETRA
from app.services.market_data_service import MarketDataService
from app.services.analysis.technical import TechnicalAnalyzer
from app.services.analysis.fundamental import FundamentalAnalyzer
from app.services.analysis.sentiment import SentimentAnalyzer
from app.services.analysis_service import AnalysisService
from app.services.user_service import UserService
from app.services.portfolio_service import PortfolioService
from app.services.chat_service import ChatService

# Import dependencies from core.dependencies
from app.core.dependencies import (
    setup_dependencies,
    get_market_data_service,
    get_analysis_service,
    get_user_service,
    get_portfolio_service,
    get_chat_service,
    get_redis_cache,
    get_llm_manager,
    get_chaetra_brain,
)

# Now import API routers after all dependencies they might need are defined
from app.api.routes.auth import router as auth_api_router
from app.api.routes.market import router as market_api_router
from app.api.routes.stocks import router as stock_api_router
from app.api.routes.analysis import router as analysis_api_router
from app.api.routes.portfolio import router as portfolio_api_router
from app.api.routes.chat import router as chat_api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NAETRA: Neural Analysis Engine for Trading Research & Assessment",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc"
)

# --- CORS Middleware ---
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else: # Allow all for local development if not specified
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Event Handlers ---
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting up {settings.APP_NAME} v{settings.APP_VERSION}...")
    
    try:
        # Initialize all dependencies
        await setup_dependencies()
        logger.info("CHAETRA core services initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize dependencies: {e}")
        raise

    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    try:
        redis_cache = get_redis_cache()
        if redis_cache:
            await redis_cache.close()
            logger.info("Redis connection closed.")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")

    try:
        market_service = get_market_data_service()
        if hasattr(market_service, "close_all_provider_sessions") and callable(getattr(market_service, "close_all_provider_sessions")):
            await market_service.close_all_provider_sessions()
            logger.info("Market data provider sessions closed.")
    except Exception as e:
        logger.error(f"Error closing market data provider sessions: {e}")
        
    logger.info("Application shutdown complete.")

# --- API Routers ---
app.include_router(auth_api_router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(market_api_router, prefix=f"{settings.API_V1_PREFIX}/market", tags=["Market Data"])
app.include_router(stock_api_router, prefix=f"{settings.API_V1_PREFIX}/stocks", tags=["Stock Specific Data"])
app.include_router(analysis_api_router, prefix=f"{settings.API_V1_PREFIX}/analysis", tags=["Analysis Engine"])
app.include_router(portfolio_api_router, prefix=f"{settings.API_V1_PREFIX}/portfolios", tags=["Portfolio Management"])
app.include_router(chat_api_router, prefix=f"{settings.API_V1_PREFIX}/chat", tags=["Chat Engine"])

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": f"Welcome to {settings.APP_NAME}! API docs at {settings.API_V1_PREFIX}/docs or {settings.API_V1_PREFIX}/redoc."
    }

# --- Health Check Endpoint ---
@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    # Basic DB check
    try:
        await db.execute(sa.text("SELECT 1")) # Async ping DB
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Basic Cache check
    try:
        redis_cache = get_redis_cache()
        cache_status = "healthy" if await redis_cache.ping() else "unhealthy"
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        cache_status = "unhealthy"

    # Check if CHAETRA is initialized
    try:
        llm_manager = await get_llm_manager()
        chaetra_status = "healthy" if llm_manager.default_provider_name else "unhealthy"
    except Exception as e:
        logger.error(f"CHAETRA health check failed: {e}")
        chaetra_status = "unhealthy"

    # Check Market Data Provider status
    market_data_provider_name = "unknown"
    try:
        market_service = get_market_data_service()
        if market_service and market_service.default_provider_name:
            market_data_provider_name = market_service.default_provider_name
    except Exception as e:
        logger.error(f"Market Data Service health check failed: {e}")
        market_data_provider_name = "error"
        
    # Determine overall status
    all_healthy = all(status == "healthy" for status in [db_status, cache_status, chaetra_status])
    overall_status = "healthy" if all_healthy and market_data_provider_name != "error" else "degraded"

    return {
        "status": overall_status,
        "database_status": db_status,
        "cache_status": cache_status,
        "chaetra_status": chaetra_status,
        "timestamp": datetime.utcnow().isoformat(),
        "llm_provider": llm_manager.default_provider_name if chaetra_status == "healthy" else None,
        "market_data_provider": market_data_provider_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
