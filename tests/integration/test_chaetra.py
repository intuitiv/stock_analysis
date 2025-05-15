"""
Integration tests for CHAETRA system.
Tests complete flow through all components.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from app.chaetra.brain import CHAETRABrain
from app.chaetra.interfaces import Evidence, KnowledgeType
from app.core.config import get_settings

settings = get_settings()

@pytest.fixture
async def chaetra():
    """Create and initialize CHAETRA brain instance"""
    brain = CHAETRABrain()
    await brain.initialize()
    yield brain
    await brain.shutdown()

@pytest.fixture
def market_data():
    """Sample market data for testing"""
    return {
        "symbol": "AAPL",
        "timeframe": "1D",
        "data": [
            {
                "timestamp": "2025-06-07T10:00:00Z",
                "open": 150.25,
                "high": 152.35,
                "low": 149.90,
                "close": 151.45,
                "volume": 1000000
            },
            {
                "timestamp": "2025-06-07T11:00:00Z",
                "open": 151.45,
                "high": 153.20,
                "low": 151.30,
                "close": 152.75,
                "volume": 1200000
            }
        ],
        "indicators": {
            "rsi": 65.5,
            "macd": {
                "macd": 2.35,
                "signal": 1.95,
                "histogram": 0.40
            }
        }
    }

@pytest.mark.asyncio
async def test_chaetra_initialization(chaetra):
    """Test CHAETRA initialization"""
    assert chaetra.initialized
    assert chaetra.memory is not None
    assert chaetra.learning is not None
    assert chaetra.reasoning is not None
    assert chaetra.opinion is not None
    assert chaetra.llm is not None

@pytest.mark.asyncio
async def test_market_data_processing(chaetra, market_data):
    """Test processing of market data"""
    result = await chaetra.process_input(
        input_type="market_data",
        content=market_data,
        context={
            "analysis_type": "technical",
            "timeframe": "1D"
        }
    )
    
    assert "error" not in result
    assert result.get("success", False)
    assert "analysis" in result
    assert result["analysis"].get("confidence", 0) > 0

@pytest.mark.asyncio
async def test_knowledge_formation(chaetra, market_data):
    """Test knowledge formation and retrieval"""
    # First, process some data to form knowledge
    await chaetra.process_input(
        input_type="market_data",
        content=market_data
    )
    
    # Query the knowledge
    knowledge = await chaetra.get_knowledge(
        "What is the trend for AAPL?",
        context={
            "timeframe": "1D",
            "include_confidence": True
        }
    )
    
    assert knowledge is not None
    assert "error" not in knowledge
    assert "key_concepts" in knowledge
    assert len(knowledge["key_concepts"]) > 0

@pytest.mark.asyncio
async def test_opinion_formation(chaetra, market_data):
    """Test opinion formation"""
    # Process data
    await chaetra.process_input(
        input_type="market_data",
        content=market_data
    )
    
    # Get analysis and opinion
    analysis = await chaetra.get_analysis(
        "AAPL_trend",
        context={
            "timeframe": "1D",
            "indicators": ["RSI", "MACD"]
        }
    )
    
    assert analysis is not None
    assert "error" not in analysis
    assert "opinion" in analysis
    if analysis["opinion"]:
        assert "confidence" in analysis["opinion"]
        assert "statement" in analysis["opinion"]

@pytest.mark.asyncio
async def test_learning_and_memory(chaetra):
    """Test learning process and memory storage"""
    # Create some evidence
    evidence = [
        Evidence(
            source="technical_analysis",
            content={
                "pattern": "double_bottom",
                "confidence": 0.85
            },
            confidence=0.85,
            timestamp=datetime.utcnow()
        )
    ]
    
    # Learn pattern
    learned = await chaetra.learning.learn(
        knowledge_type=KnowledgeType.PATTERN,
        content={
            "pattern": "double_bottom",
            "symbol": "AAPL",
            "timeframe": "1D"
        },
        evidence=evidence
    )
    
    assert learned
    
    # Verify storage in memory
    stored = await chaetra.memory.retrieve("knowledge:pattern:AAPL_double_bottom")
    assert stored is not None
    assert stored["content"]["pattern"] == "double_bottom"

@pytest.mark.asyncio
async def test_reasoning_process(chaetra, market_data):
    """Test reasoning capabilities"""
    # Create context with known patterns
    context = {
        "patterns": ["double_bottom"],
        "indicators": {
            "rsi": 65.5,
            "macd": "bullish"
        }
    }
    
    # Perform reasoning
    analysis = await chaetra.reasoning.analyze(
        context=context,
        knowledge_base={
            "market_data": market_data,
            "known_patterns": ["double_bottom"]
        }
    )
    
    assert analysis is not None
    assert "findings" in analysis
    assert analysis.get("confidence", 0) > 0

@pytest.mark.asyncio
async def test_llm_integration(chaetra):
    """Test LLM processing"""
    response = await chaetra.llm.process_text(
        "Analyze the current market sentiment for AAPL based on technical indicators.",
        context={
            "format": "json",
            "provider": "ollama"  # Use local Ollama for testing
        }
    )
    
    assert response is not None
    assert "error" not in response
    assert "response" in response
    assert response.get("provider") == "ollama"

@pytest.mark.asyncio
async def test_error_handling(chaetra):
    """Test error handling"""
    # Test with invalid input type
    result = await chaetra.process_input(
        input_type="invalid_type",
        content={}
    )
    
    assert "error" in result
    assert "unsupported input type" in result["error"].lower()
    
    # Test with invalid market data
    result = await chaetra.process_input(
        input_type="market_data",
        content={"invalid": "data"}
    )
    
    assert "error" in result

@pytest.mark.asyncio
async def test_full_analysis_flow(chaetra, market_data):
    """Test complete analysis flow"""
    # 1. Process market data
    input_result = await chaetra.process_input(
        input_type="market_data",
        content=market_data,
        context={"analysis_type": "full"}
    )
    
    assert input_result.get("success", False)
    
    # 2. Get knowledge
    knowledge = await chaetra.get_knowledge(
        "AAPL_analysis",
        context={"include_indicators": True}
    )
    
    assert knowledge is not None
    
    # 3. Get analysis with opinion
    analysis = await chaetra.get_analysis(
        "AAPL_trend",
        context={
            "timeframe": "1D",
            "include_patterns": True,
            "include_indicators": True
        }
    )
    
    assert analysis is not None
    assert "knowledge" in analysis
    assert "analysis" in analysis
    assert "opinion" in analysis

@pytest.mark.asyncio
async def test_shutdown_process(chaetra, market_data):
    """Test graceful shutdown"""
    # Create some pending processes
    await asyncio.gather(
        chaetra.process_input(
            input_type="market_data",
            content=market_data
        ),
        chaetra.get_analysis("AAPL_trend")
    )
    
    # Initiate shutdown
    await chaetra.shutdown()
    
    # Verify shutdown
    assert not chaetra.initialized
    assert len(chaetra._processing_queue) == 0
    # Verify LLM session is closed
    assert chaetra.llm._session is None or chaetra.llm._session.closed

if __name__ == "__main__":
    pytest.main([__file__])
