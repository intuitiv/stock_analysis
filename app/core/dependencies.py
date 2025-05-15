# app/core/dependencies.py
from fastapi import Depends

from app.core.config import settings # Required by some service constructors implicitly or explicitly
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

# --- Singleton Instances for Dependency Injection ---
# These are initialized once and provided via getter functions.

# Cache
# Note: RedisCache constructor might implicitly use settings if designed that way,
# or it might need settings passed if it's refactored. For now, assume it handles it.
# Initialize Redis cache first
redis_cache_instance = RedisCache()

# Initialize basic memory system
memory_system_instance = MemorySystem(cache=redis_cache_instance)

# Instances will be initialized in setup_dependencies()
llm_manager_instance = None
learning_system_instance = None
reasoning_system_instance = None
opinion_system_instance = None
chaetra_brain_instance = None

async def setup_dependencies():
    """Initialize dependencies that require async setup"""
    global llm_manager_instance, learning_system_instance, reasoning_system_instance
    global opinion_system_instance, chaetra_brain_instance
    global sentiment_analyzer_instance, analysis_service_instance

    if llm_manager_instance is None: # Ensure it's only created once
        llm_manager_instance = await LLMManager.create()

    if learning_system_instance is None:
        learning_system_instance = LearningSystem(memory_system=memory_system_instance)
    
    if reasoning_system_instance is None:
        reasoning_system_instance = ReasoningSystem(
            memory_system=memory_system_instance,
            learning_system=learning_system_instance,
            llm_manager=llm_manager_instance
        )
    
    if opinion_system_instance is None:
        opinion_system_instance = OpinionSystem(
            memory_system=memory_system_instance,
            llm_manager=llm_manager_instance
        )

    if chaetra_brain_instance is None:
        chaetra_brain_instance = await CHAETRA.get_instance(
            memory_system=memory_system_instance,
            learning_system=learning_system_instance,
            reasoning_system=reasoning_system_instance,
            opinion_system=opinion_system_instance,
            llm_manager=llm_manager_instance
        )

    if sentiment_analyzer_instance is None:
        sentiment_analyzer_instance = SentimentAnalyzer(
            market_data_service=market_data_service_instance,
            llm_manager=llm_manager_instance
        )

    if analysis_service_instance is None:
        analysis_service_instance = AnalysisService(
            market_data_service=market_data_service_instance,
            technical_analyzer=technical_analyzer_instance,
            fundamental_analyzer=fundamental_analyzer_instance,
            sentiment_analyzer=sentiment_analyzer_instance,
            chaetra_brain=chaetra_brain_instance
        )
    
    # Ensure all global instances are set before returning
    # This function is primarily for its side effects (setting global instances)

# Application Services - some will be initialized in setup_dependencies
market_data_service_instance = MarketDataService(cache=redis_cache_instance)
technical_analyzer_instance = TechnicalAnalyzer()
fundamental_analyzer_instance = FundamentalAnalyzer(market_data_service=market_data_service_instance)
user_service_instance = UserService()
portfolio_service_instance = PortfolioService(market_data_service=market_data_service_instance)

# These depend on async initialized llm_manager or chaetra_brain
sentiment_analyzer_instance = None
analysis_service_instance = None
# --- Dependency Provider Functions ---
# These functions will be used by FastAPI's `Depends` system.

def get_redis_cache() -> RedisCache:
    return redis_cache_instance

async def get_llm_manager() -> LLMManager:
    if llm_manager_instance is None:
        await setup_dependencies() # Ensure dependencies are set up if not already
    return llm_manager_instance

def get_memory_system() -> MemorySystem:
    return memory_system_instance

def get_learning_system() -> LearningSystem:
    if learning_system_instance is None:
        # This indicates a setup issue if LLMManager was needed for it
        raise RuntimeError("Learning system not initialized. Call setup_dependencies().")
    return learning_system_instance

def get_reasoning_system() -> ReasoningSystem:
    if reasoning_system_instance is None:
        raise RuntimeError("Reasoning system not initialized. Call setup_dependencies().")
    return reasoning_system_instance

def get_opinion_system() -> OpinionSystem:
    if opinion_system_instance is None:
        raise RuntimeError("Opinion system not initialized. Call setup_dependencies().")
    return opinion_system_instance

async def get_chaetra_brain() -> CHAETRA:
    if chaetra_brain_instance is None:
        await setup_dependencies() # Ensure dependencies are set up
    return chaetra_brain_instance

def get_market_data_service() -> MarketDataService:
    return market_data_service_instance

def get_technical_analyzer() -> TechnicalAnalyzer:
    return technical_analyzer_instance

def get_fundamental_analyzer() -> FundamentalAnalyzer:
    return fundamental_analyzer_instance

def get_sentiment_analyzer() -> SentimentAnalyzer:
    if sentiment_analyzer_instance is None:
         raise RuntimeError("Sentiment analyzer not initialized. Call setup_dependencies().")
    return sentiment_analyzer_instance

def get_analysis_service() -> AnalysisService:
    if analysis_service_instance is None:
        raise RuntimeError("Analysis service not initialized. Call setup_dependencies().")
    return analysis_service_instance

def get_user_service() -> UserService:
    return user_service_instance

def get_portfolio_service() -> PortfolioService:
    return portfolio_service_instance

# chat_service_instance is created per-request due to async dependencies
async def get_chat_service(
    chaetra_brain_dep: CHAETRA = Depends(get_chaetra_brain), # Renamed to avoid conflict
    market_data_service_dep: MarketDataService = Depends(get_market_data_service), # Renamed
    analysis_service_dep: AnalysisService = Depends(get_analysis_service) # Renamed
) -> ChatService:
    # Ensure global instances are used if already initialized by setup_dependencies
    # This is a bit redundant if setup_dependencies is guaranteed to run at startup,
    # but acts as a safeguard for direct calls to get_chat_service if that were possible.
    global chaetra_brain_instance, market_data_service_instance, analysis_service_instance
    
    # Use the instances from Depends if they are correctly resolved by FastAPI
    # If not, this indicates a deeper issue with FastAPI's handling of async Depends at this point.
    # However, FastAPI should resolve these correctly.
    
    # The Depends mechanism should provide the initialized instances.
    # If chaetra_brain_instance is None here, it means setup_dependencies wasn't awaited properly at startup.
    
    return ChatService(
        chaetra_brain=chaetra_brain_dep,
        market_data_service=market_data_service_dep,
        analysis_service=analysis_service_dep
    )
