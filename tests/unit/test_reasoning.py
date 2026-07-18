"""
Unit tests for CHAETRA's reasoning engine.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from app.chaetra.reasoning import ReasoningEngine
from app.chaetra.memory import MemorySystem
from app.chaetra.interfaces import Evidence
from app.core.config import get_settings

settings = get_settings()

@pytest.fixture
async def memory():
    """Create memory system instance"""
    return MemorySystem()

@pytest.fixture
async def reasoning(memory):
    """Create reasoning engine instance"""
    return ReasoningEngine(memory)

@pytest.fixture
def market_context():
    """Sample market context"""
    return {
        "timeframe": "1D",
        "pattern_matching": True,
        "correlation_analysis": True,
        "source_weights": {
            "technical_analysis": 1.0,
            "fundamental_analysis": 0.8,
            "market_sentiment": 0.6
        }
    }

@pytest.fixture
def market_data():
    """Sample market data"""
    return {
        "symbol": "AAPL",
        "price_data": [
            {"timestamp": "2025-06-07T10:00:00Z", "price": 150.25},
            {"timestamp": "2025-06-07T11:00:00Z", "price": 151.50}
        ],
        "indicators": {
            "rsi": 65.5,
            "macd": {"value": 0.5, "signal": 0.3}
        },
        "patterns": ["double_bottom", "support_test"]
    }

@pytest.mark.asyncio
async def test_analyze_market_data(reasoning, market_context, market_data):
    """Test market data analysis"""
    result = await reasoning.analyze(
        context=market_context,
        knowledge_base={"market_data": market_data}
    )
    
    assert result is not None
    assert "findings" in result
    assert "confidence" in result
    assert result["confidence"] > 0
    assert len(result["reasoning"]) > 0

@pytest.mark.asyncio
async def test_form_hypothesis(reasoning):
    """Test hypothesis formation"""
    observations = [
        {
            "type": "price_action",
            "data": {"movement": "upward", "strength": 0.8}
        },
        {
            "type": "volume_profile",
            "data": {"volume": "increasing", "conviction": 0.7}
        }
    ]
    
    hypothesis = await reasoning.form_hypothesis(observations)
    
    assert hypothesis is not None
    assert "statement" in hypothesis
    assert "confidence" in hypothesis
    assert len(hypothesis["supporting_observations"]) > 0

@pytest.mark.asyncio
async def test_validate_hypothesis(reasoning):
    """Test hypothesis validation"""
    # Form initial hypothesis
    hypothesis = {
        "id": "test_hypothesis",
        "statement": "Market is trending upward",
        "confidence": 0.7,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Create supporting evidence
    evidence = [
        Evidence(
            source="price_action",
            content={"movement": "upward", "strength": 0.8},
            confidence=0.8,
            timestamp=datetime.utcnow()
        ),
        Evidence(
            source="volume_analysis",
            content={"volume": "high", "conviction": 0.9},
            confidence=0.9,
            timestamp=datetime.utcnow()
        )
    ]
    
    validation = await reasoning.validate_hypothesis(hypothesis, evidence)
    
    assert validation is not None
    assert validation["hypothesis_id"] == "test_hypothesis"
    assert validation["status"] in ["strengthened", "maintained", "weakened"]
    assert validation["validation_confidence"] > 0

@pytest.mark.asyncio
async def test_make_decision(reasoning, market_context):
    """Test decision making"""
    options = [
        {"action": "buy", "size": 100},
        {"action": "sell", "size": 50},
        {"action": "hold"}
    ]
    
    decision = await reasoning.make_decision(market_context, options)
    
    assert decision is not None
    assert "selected_option" in decision
    assert "confidence" in decision
    assert "reasoning" in decision
    assert len(decision["alternatives"]) == len(options) - 1

@pytest.mark.asyncio
async def test_evidence_evaluation(reasoning):
    """Test evidence evaluation logic"""
    evidence = [
        Evidence(
            source="technical_analysis",
            content={"indicator": "RSI", "value": 70},
            confidence=0.8,
            timestamp=datetime.utcnow()
        ),
        Evidence(
            source="fundamental_analysis",
            content={"metric": "P/E", "value": 15},
            confidence=0.9,
            timestamp=datetime.utcnow()
        )
    ]
    
    confidence, reasoning = reasoning._evaluate_evidence(
        evidence,
        context={"source_weights": {"technical_analysis": 1.0, "fundamental_analysis": 0.8}}
    )
    
    assert 0 <= confidence <= 1
    assert len(reasoning) > 0

@pytest.mark.asyncio
async def test_pattern_recognition(reasoning, market_data):
    """Test pattern recognition capabilities"""
    patterns = await reasoning._find_patterns(
        market_data,
        pattern_types=["all"]
    )
    
    assert isinstance(patterns, list)
    for pattern in patterns:
        assert "confidence" in pattern

@pytest.mark.asyncio
async def test_correlation_analysis(reasoning, market_data):
    """Test correlation analysis"""
    correlations = await reasoning._analyze_correlations(
        market_data,
        threshold=0.7
    )
    
    assert isinstance(correlations, list)
    for correlation in correlations:
        assert "confidence" in correlation

@pytest.mark.asyncio
async def test_observation_grouping(reasoning):
    """Test observation grouping logic"""
    observations = [
        {"type": "price", "data": {"value": 100}},
        {"type": "price", "data": {"value": 101}},
        {"type": "volume", "data": {"value": 1000}}
    ]
    
    grouped = reasoning._group_observations(observations)
    
    assert isinstance(grouped, dict)
    assert "price" in grouped
    assert "volume" in grouped
    assert len(grouped["price"]) == 2

@pytest.mark.asyncio
async def test_decision_factors(reasoning, market_context):
    """Test decision factor extraction"""
    factors = reasoning._extract_decision_factors(market_context)
    
    assert isinstance(factors, list)
    assert len(factors) > 0
    assert "timeframe" in factors

@pytest.mark.asyncio
async def test_error_handling(reasoning):
    """Test error handling in reasoning operations"""
    # Invalid context
    result = await reasoning.analyze(None, {})
    assert "error" in result
    
    # Invalid observations
    result = await reasoning.form_hypothesis(None)
    assert "error" in result
    
    # Invalid evidence
    result = await reasoning.validate_hypothesis({}, [])
    assert result["status"] == "unknown"

@pytest.mark.asyncio
async def test_confidence_thresholds(reasoning, market_context, market_data):
    """Test confidence threshold handling"""
    # Analysis with low confidence data
    low_confidence_data = {**market_data}
    low_confidence_data["indicators"]["rsi"] = 50  # Neutral
    
    result = await reasoning.analyze(
        context=market_context,
        knowledge_base={"market_data": low_confidence_data}
    )
    
    assert result["confidence"] < settings.CHAETRA_LEARNING_CONFIDENCE_THRESHOLD

@pytest.mark.asyncio
async def test_concurrent_analysis(reasoning, market_context, market_data):
    """Test concurrent analysis capabilities"""
    # Create multiple analysis tasks
    tasks = [
        reasoning.analyze(
            context=market_context,
            knowledge_base={"market_data": market_data}
        )
        for _ in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 5
    assert all(r.get("confidence", 0) > 0 for r in results)

@pytest.mark.asyncio
async def test_analysis_caching(reasoning, market_context, market_data):
    """Test analysis result caching"""
    # First analysis
    first_result = await reasoning.analyze(
        context=market_context,
        knowledge_base={"market_data": market_data}
    )
    
    # Second analysis with same data
    second_result = await reasoning.analyze(
        context=market_context,
        knowledge_base={"market_data": market_data}
    )
    
    assert first_result["id"] != second_result["id"]
    assert first_result["findings"] == second_result["findings"]

if __name__ == "__main__":
    pytest.main([__file__])
