"""Dependency injection utilities."""
from typing import AsyncGenerator, Optional
import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session_maker
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.market_data_service import MarketDataService
from app.services.analysis_service import AnalysisService
from app.services.analysis.technical import TechnicalAnalyzer
from app.services.analysis.fundamental import FundamentalAnalyzer
from app.services.analysis.sentiment import SentimentAnalyzer
from app.chaetra.brain import CHAETRA
from app.core.cache import RedisCache
from app.chaetra.llm import LLMManager
from app.chaetra.memory import MemorySystem
from app.chaetra.learning import LearningSystem
from app.chaetra.reasoning import ReasoningSystem
from app.chaetra.opinion import OpinionSystem
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.services.portfolio_service import PortfolioService

logger = logging.getLogger(__name__)

# Global instances
_redis_cache: Optional[RedisCache] = None
_llm_manager: Optional[LLMManager] = None
_chaetra_brain: Optional[CHAETRA] = None
_market_data_service: Optional[MarketDataService] = None
_user_service: Optional[UserService] = None
_portfolio_service: Optional[PortfolioService] = None
_chat_service: Optional[ChatService] = None

async def setup_dependencies() -> None:
    """Initialize all global service dependencies."""
    global _redis_cache, _llm_manager, _chaetra_brain, _market_data_service
    global _user_service, _portfolio_service, _chat_service
    
    try:
        # Initialize Redis cache
        _redis_cache = RedisCache()
        await _redis_cache.connect()
        
        # Initialize LLM manager
        _llm_manager = LLMManager()
        
        # Initialize CHAETRA brain with required dependencies
        memory_system = MemorySystem()
        learning_system = LearningSystem()
        reasoning_system = ReasoningSystem()
        opinion_system = OpinionSystem()
        
        _chaetra_brain = CHAETRA(
            memory_system=memory_system,
            learning_system=learning_system,
            reasoning_system=reasoning_system,
            opinion_system=opinion_system,
            llm_manager=_llm_manager
        )
        
        # Initialize services
        _market_data_service = MarketDataService(cache=_redis_cache)
        _user_service = UserService()  # Doesn't need session_factory, uses static methods
        _portfolio_service = PortfolioService(async_session_maker)
        _chat_service = ChatService(
            session_factory=async_session_maker,
            memory_system=memory_system,  # Reuse memory_system from CHAETRA
            chaetra_brain=_chaetra_brain,
            market_data_service=_market_data_service
        )
        
        logger.info("All dependencies initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize dependencies: {e}")
        raise

def get_redis_cache() -> RedisCache:
    """Get Redis cache instance."""
    if not _redis_cache:
        raise RuntimeError("Redis cache not initialized")
    return _redis_cache

def get_llm_manager() -> LLMManager:
    """Get LLM manager instance."""
    if not _llm_manager:
        raise RuntimeError("LLM manager not initialized")
    return _llm_manager

def get_chaetra_brain() -> CHAETRA:
    """Get CHAETRA brain instance."""
    if not _chaetra_brain:
        raise RuntimeError("CHAETRA brain not initialized")
    return _chaetra_brain

def get_user_service() -> UserService:
    """Get user service instance."""
    if not _user_service:
        raise RuntimeError("User service not initialized")
    return _user_service

def get_portfolio_service() -> PortfolioService:
    """Get portfolio service instance."""
    if not _portfolio_service:
        raise RuntimeError("Portfolio service not initialized")
    return _portfolio_service

def get_chat_service() -> ChatService:
    """Get chat service instance."""
    if not _chat_service:
        raise RuntimeError("Chat service not initialized")
    return _chat_service

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async for session in get_db():
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with database session."""
    return user

async def get_market_data_service() -> MarketDataService:
    """Get market data service instance."""
    if not _market_data_service:
        raise RuntimeError("Market data service not initialized")
    return _market_data_service

async def get_analysis_service(
    market_data_service: MarketDataService = Depends(get_market_data_service)
) -> AsyncGenerator[AnalysisService, None]:
    """Get analysis service instance."""
    technical_analyzer = TechnicalAnalyzer()
    fundamental_analyzer = FundamentalAnalyzer()
    sentiment_analyzer = SentimentAnalyzer()
    memory_system = MemorySystem()
    learning_system = LearningSystem()
    reasoning_system = ReasoningSystem()
    opinion_system = OpinionSystem()
    
    chaetra = CHAETRA(
        memory_system=memory_system,
        learning_system=learning_system,
        reasoning_system=reasoning_system,
        opinion_system=opinion_system,
        llm_manager=get_llm_manager()
    )
    
    service = AnalysisService(
        market_data_service=market_data_service,
        technical_analyzer=technical_analyzer,
        fundamental_analyzer=fundamental_analyzer,
        sentiment_analyzer=sentiment_analyzer,
        chaetra_brain=chaetra
    )
    try:
        yield service
    finally:
        await chaetra.close()
