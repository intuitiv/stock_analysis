"""Minimal test for LM Studio integration."""
import asyncio
import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from app.core.cache import RedisCache
from app.chaetra.llm import LLMManager
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_llm_manager() -> Optional[LLMManager]:
    """Initialize LLM manager with error handling."""
    try:
        logger.info("Initializing LLM Manager...")
        llm_manager = await LLMManager.create()
        
        if not llm_manager.providers:
            logger.error("No LLM providers were initialized!")
            return None
            
        if "lm_studio" not in llm_manager.providers:
            logger.error("LM Studio provider not available! Check your configuration.")
            logger.info(f"Available providers: {list(llm_manager.providers.keys())}")
            return None
            
        return llm_manager
    except Exception as e:
        logger.error(f"Failed to initialize LLM Manager: {str(e)}")
        return None

async def test_basic_generation(llm_manager: LLMManager) -> bool:
    """Test basic text generation."""
    prompt = "What is technical analysis in stock trading?"
    logger.info(f"\nTesting basic generation with prompt: {prompt}")
    
    try:
        response = await llm_manager.generate_text(
            prompt=prompt,
            provider_name="lm_studio",
            temperature=0.7
        )
        logger.info(f"Response:\n{response}")
        return True
    except Exception as e:
        logger.error(f"Basic generation test failed: {str(e)}")
        return False

async def test_context_aware_generation(llm_manager: LLMManager) -> bool:
    """Test generation with market context."""
    prompt = "Analyze this stock's current technical indicators."
    context = {
        "current_symbol": "AAPL",
        "timestamp": datetime.utcnow().isoformat(),
        "indicators": {
            "RSI": 65.4,
            "MA_50": 175.23,
            "MA_200": 168.45,
            "MACD": {
                "line": 2.3,
                "signal": 1.8,
                "histogram": 0.5
            }
        }
    }
    
    logger.info(f"\nTesting context-aware generation:")
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Context: {context}")
    
    try:
        response = await llm_manager.generate_text(
            prompt=prompt,
            context=context,
            provider_name="lm_studio",
            temperature=0.7
        )
        logger.info(f"Response:\n{response}")
        return True
    except Exception as e:
        logger.error(f"Context-aware generation test failed: {str(e)}")
        return False

async def run_tests() -> Tuple[int, int]:
    """Run all tests and return results."""
    tests_passed = 0
    total_tests = 2
    
    logger.info("\nLM Studio Configuration:")
    logger.info(f"Enabled: {getattr(settings, 'ENABLE_LM_STUDIO', False)}")
    logger.info(f"Base URL: {settings.LM_STUDIO_BASE_URL}")
    logger.info(f"Model: {settings.LM_STUDIO_MODEL}")
    
    # Initialize LLM Manager
    llm_manager = await init_llm_manager()
    if not llm_manager:
        logger.error("Cannot proceed with tests due to initialization failure")
        return 0, total_tests
    
    logger.info(f"Available Providers: {list(llm_manager.providers.keys())}")
    
    # Run tests
    if await test_basic_generation(llm_manager):
        tests_passed += 1
    
    if await test_context_aware_generation(llm_manager):
        tests_passed += 1
    
    return tests_passed, total_tests

async def main():
    """Main test runner."""
    logger.info("Starting LM Studio integration tests...")
    
    try:
        passed, total = await run_tests()
        logger.info(f"\nTests completed: {passed}/{total} passed")
        
        if passed != total:
            logger.warning("Some tests failed!")
        else:
            logger.info("All tests passed successfully!")
            
    except Exception as e:
        logger.error(f"Testing failed with error: {str(e)}")
    finally:
        logger.info("Testing completed.")

if __name__ == "__main__":
    asyncio.run(main())