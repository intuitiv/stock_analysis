"""
Unit tests for CHAETRA's opinion engine.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from app.chaetra.opinion import OpinionEngine, Opinion
from app.chaetra.memory import MemorySystem
from app.chaetra.interfaces import Evidence
from app.core.config import get_settings

settings = get_settings()

@pytest.fixture
async def memory():
    """Create memory system instance"""
    return MemorySystem()

@pytest.fixture
async def opinion_engine(memory):
    """Create opinion engine instance"""
    return OpinionEngine(memory)

@pytest.fixture
def sample_evidence():
    """Create sample evidence"""
    return [
        Evidence(
            source="technical_analysis",
            content={
                "indicators": {"rsi": 70, "macd": "bullish"},
                "conclusion": "Overbought conditions"
            },
            confidence=0.85,
            timestamp=datetime.utcnow()
        ),
        Evidence(
            source="sentiment_analysis",
            content={
                "sentiment": "positive",
                "conclusion": "Bullish market sentiment"
            },
            confidence=0.75,
            timestamp=datetime.utcnow()
        )
    ]

@pytest.mark.asyncio
async def test_opinion_formation(opinion_engine, sample_evidence):
    """Test basic opinion formation"""
    topic = "AAPL_trend"
    
    # Form opinion
    opinion = await opinion_engine.form_opinion(topic, sample_evidence)
    
    assert opinion is not None
    assert "topic" in opinion
    assert "statement" in opinion
    assert "confidence" in opinion
    assert opinion["confidence"] > 0
    assert len(opinion["evidence"]) == len(sample_evidence)

@pytest.mark.asyncio
async def test_opinion_confidence_calculation(opinion_engine):
    """Test confidence calculation with weighted evidence"""
    topic = "test_confidence"
    now = datetime.utcnow()
    
    # Create evidence with different timestamps
    evidence = [
        Evidence(
            source="recent",
            content={"conclusion": "Recent data"},
            confidence=0.9,
            timestamp=now
        ),
        Evidence(
            source="old",
            content={"conclusion": "Old data"},
            confidence=0.8,
            timestamp=now - timedelta(days=1)
        )
    ]
    
    opinion = await opinion_engine.form_opinion(topic, evidence)
    
    # Recent evidence should have more weight
    assert opinion["confidence"] > 0.8
    assert opinion["confidence"] < 0.9

@pytest.mark.asyncio
async def test_opinion_update(opinion_engine, sample_evidence):
    """Test opinion updating"""
    topic = "update_test"
    
    # Form initial opinion
    initial_opinion = await opinion_engine.form_opinion(topic, sample_evidence)
    
    # Create new evidence
    new_evidence = [
        Evidence(
            source="price_action",
            content={
                "pattern": "breakout",
                "conclusion": "Strong buy signal"
            },
            confidence=0.95,
            timestamp=datetime.utcnow()
        )
    ]
    
    # Update opinion
    updated_opinion = await opinion_engine.update_opinion(topic, new_evidence)
    
    assert updated_opinion is not None
    assert updated_opinion["confidence"] != initial_opinion["confidence"]
    assert len(updated_opinion["evidence"]) > len(initial_opinion["evidence"])
    assert updated_opinion["update_count"] > initial_opinion["update_count"]

@pytest.mark.asyncio
async def test_opinion_retrieval(opinion_engine, sample_evidence):
    """Test opinion retrieval"""
    topic = "retrieval_test"
    
    # Form opinion
    formed_opinion = await opinion_engine.form_opinion(topic, sample_evidence)
    
    # Retrieve opinion
    retrieved_opinion = await opinion_engine.get_opinion(topic)
    
    assert retrieved_opinion is not None
    assert retrieved_opinion == formed_opinion

@pytest.mark.asyncio
async def test_opinion_confidence_tracking(opinion_engine):
    """Test confidence tracking over time"""
    topic = "confidence_tracking"
    
    # Initial evidence
    initial_evidence = [
        Evidence(
            source="test",
            content={"conclusion": "Initial"},
            confidence=0.7,
            timestamp=datetime.utcnow()
        )
    ]
    
    # Form initial opinion
    initial_opinion = await opinion_engine.form_opinion(topic, initial_evidence)
    initial_confidence = initial_opinion["confidence"]
    
    # Add stronger evidence
    stronger_evidence = [
        Evidence(
            source="test",
            content={"conclusion": "Stronger"},
            confidence=0.9,
            timestamp=datetime.utcnow()
        )
    ]
    
    updated_opinion = await opinion_engine.update_opinion(topic, stronger_evidence)
    
    assert updated_opinion["confidence"] > initial_confidence

@pytest.mark.asyncio
async def test_opinion_caching(opinion_engine, sample_evidence):
    """Test opinion caching"""
    topic = "cache_test"
    
    # Form opinion
    await opinion_engine.form_opinion(topic, sample_evidence)
    
    # Check cache
    assert topic in opinion_engine._opinion_cache
    
    # Verify cached data matches
    cached_opinion = opinion_engine._opinion_cache[topic]
    retrieved_opinion = await opinion_engine.get_opinion(topic)
    
    assert cached_opinion.to_dict() == retrieved_opinion

@pytest.mark.asyncio
async def test_opinion_history(opinion_engine, sample_evidence):
    """Test opinion history tracking"""
    topic = "history_test"
    
    # Form initial opinion
    initial = await opinion_engine.form_opinion(topic, sample_evidence)
    
    # Update multiple times
    updates = []
    for i in range(3):
        new_evidence = [
            Evidence(
                source=f"update_{i}",
                content={"conclusion": f"Update {i}"},
                confidence=0.8 + i * 0.05,
                timestamp=datetime.utcnow()
            )
        ]
        updates.append(await opinion_engine.update_opinion(topic, new_evidence))
    
    final_opinion = await opinion_engine.get_opinion(topic)
    
    assert len(final_opinion["history"]) == 3
    assert all(h["confidence"] < final_opinion["confidence"] for h in final_opinion["history"])

@pytest.mark.asyncio
async def test_opinion_expiration(opinion_engine, sample_evidence):
    """Test opinion expiration from cache"""
    topic = "expiration_test"
    
    # Form opinion
    await opinion_engine.form_opinion(topic, sample_evidence)
    
    # Manipulate cache entry timestamp
    opinion_engine._opinion_cache[topic].timestamp = (
        datetime.utcnow() - timedelta(seconds=opinion_engine._opinion_ttl + 1)
    )
    
    # Try to get opinion - should fetch from memory instead of cache
    opinion = await opinion_engine.get_opinion(topic)
    
    assert opinion is not None
    assert topic not in opinion_engine._opinion_cache

@pytest.mark.asyncio
async def test_concurrent_opinion_formation(opinion_engine):
    """Test concurrent opinion formation"""
    topics = [f"concurrent_test_{i}" for i in range(5)]
    evidence = [
        Evidence(
            source="test",
            content={"conclusion": "Test data"},
            confidence=0.8,
            timestamp=datetime.utcnow()
        )
    ]
    
    # Form opinions concurrently
    tasks = [
        opinion_engine.form_opinion(topic, evidence)
        for topic in topics
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == len(topics)
    assert all(r is not None for r in results)
    assert all(r["confidence"] > 0 for r in results)

@pytest.mark.asyncio
async def test_opinion_persistence(opinion_engine, memory, sample_evidence):
    """Test opinion persistence in memory"""
    topic = "persistence_test"
    
    # Form opinion with high confidence
    opinion = await opinion_engine.form_opinion(topic, sample_evidence)
    
    # Verify storage in memory
    stored = await memory.retrieve(f"opinion:{topic}")
    assert stored is not None
    assert stored["topic"] == topic
    assert stored["confidence"] == opinion["confidence"]

@pytest.mark.asyncio
async def test_error_handling(opinion_engine):
    """Test error handling in opinion operations"""
    # Invalid evidence
    result = await opinion_engine.form_opinion(
        "error_test",
        [Evidence(
            source="test",
            content=None,
            confidence=-1.0,
            timestamp=datetime.utcnow()
        )]
    )
    assert "error" in result
    
    # Nonexistent opinion
    result = await opinion_engine.get_opinion("nonexistent")
    assert result is None
    
    # Invalid topic
    result = await opinion_engine.form_opinion(None, [])
    assert "error" in result

if __name__ == "__main__":
    pytest.main([__file__])
