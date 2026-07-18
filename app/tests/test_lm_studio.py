"""Test script for LM Studio integration."""
import asyncio
import logging
from app.chaetra.llm import LLMManager
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_lm_studio_connection():
    """Test basic connection to LM Studio."""
    logger.info("Testing LM Studio connection...")
    llm = await LLMManager.create()
    
    logger.info("\nConfiguration:")
    logger.info(f"LM Studio Enabled: {getattr(settings, 'ENABLE_LM_STUDIO', False)}")
    logger.info(f"Base URL: {settings.LM_STUDIO_BASE_URL}")
    logger.info(f"Model: {settings.LM_STUDIO_MODEL}")
    logger.info(f"Available Providers: {list(llm.providers.keys())}")

async def test_lm_studio_generation():
    """Test text generation with LM Studio."""
    llm = await LLMManager.create()
    
    # Test cases
    test_cases = [
        {
            "name": "Simple Query",
            "prompt": "What is fundamental analysis?",
            "context": None,
            "temperature": 0.7
        },
        {
            "name": "Stock Analysis",
            "prompt": "Analyze this stock's performance",
            "context": {
                "current_symbol": "AAPL",
                "timeframe": "1D",
                "market_condition": "bullish"
            },
            "temperature": 0.7
        },
        {
            "name": "Technical Analysis",
            "prompt": "Provide technical analysis insights",
            "context": {
                "current_symbol": "AAPL",
                "indicators": {
                    "RSI": 65.4,
                    "MA_50": 175.23,
                    "MA_200": 168.45,
                    "MACD": {"line": 2.3, "signal": 1.8, "histogram": 0.5}
                }
            },
            "temperature": 0.3
        }
    ]

    for test in test_cases:
        logger.info(f"\nRunning test: {test['name']}")
        logger.info(f"Prompt: {test['prompt']}")
        logger.info(f"Context: {test['context']}")
        
        try:
            response = await llm.generate_text(
                prompt=test['prompt'],
                context=test['context'],
                temperature=test['temperature'],
                provider_name="lm_studio"
            )
            logger.info(f"Response:\n{response}\n")
            logger.info("=" * 50)
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")

async def main():
    """Run all tests."""
    logger.info("Starting LM Studio integration tests...")
    
    try:
        await test_lm_studio_connection()
        await test_lm_studio_generation()
    except Exception as e:
        logger.error(f"Testing failed: {str(e)}")
    
    logger.info("Testing completed.")

if __name__ == "__main__":
    asyncio.run(main())