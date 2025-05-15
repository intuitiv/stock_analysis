"""
Unit tests for CHAETRA's learning engine.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.chaetra.learning import LearningEngine
from app.chaetra.memory import MemorySystem
from app.chaetra.interfaces import Evidence, KnowledgeType
from app.core.config import get_settings

settings = get_settings()

@pytest.fixture
async def memory():
    """Create memory system instance"""
    return MemorySystem()

@pytest.fixture
async def learning(memory):
    """Create learning engine instance"""
    return LearningEngine(memory)

@pytest.mark.asyncio
async def test_learn_new_knowledge(learning):
    """Test learning new knowledge"""
    content = {
        "pattern": "double_bottom",
        "symbol": "AAPL",
        "timeframe": "1D"
    }
    
    evidence = [
        Evidence(
            source="technical_analysis",
            content={"confidence": 0.85},
            confidence=0.85,
            timestamp=datetime.utcnow()
        )
    ]
    
    # Learn new knowledge
    success = await learning.learn(
        knowledge_type=KnowledgeType.PATTERN,
        content=content,
        evidence=evidence
    )
    
    assert success
    assert learning._learning_attempts.get(
        f"knowledge:{KnowledgeType.PATTERN.value}:{hash(str(content))}"
    ) == 1

@pytest.mark.asyncio
async def test_failed_learning_tracking(learning):
    """Test tracking of failed learning attempts"""
    # Create invalid content that will fail
    content = object()  # Non-serializable
    
    evidence = [
        Evidence(
            source="test",
            content={"test": "data"},
            confidence=0.5,
            timestamp=datetime.utcnow()
        )
    ]
    
    # Attempt learning multiple times
    key = f"knowledge:{KnowledgeType.FACT.value}:{hash(str(content))}"
    
    for _ in range(3):
        success = await learning.learn(
            knowledge_type=KnowledgeType.FACT,
            content=content,
            evidence=evidence
        )
        assert not success
    
    # Verify tracking
    assert learning._learning_attempts[key] == 3
    assert key in learning._failed_learnings

@pytest.mark.asyncio
async def test_unlearn_knowledge(learning):
    """Test unlearning knowledge"""
    # First learn something
    content = {"fact": "test fact"}
    evidence = [
        Evidence(
            source="test",
            content={"test": "data"},
            confidence=0.9,
            timestamp=datetime.utcnow()
        )
    ]
    
    await learning.learn(
        knowledge_type=KnowledgeType.FACT,
        content=content,
        evidence=evidence
    )
    
    # Now unlearn it
    success = await learning.unlearn(
        knowledge_type=KnowledgeType.FACT,
        identifier=str(hash(str(content)))
    )
    
    assert success
    
    # Verify it's gone
    key = f"knowledge:{KnowledgeType.FACT.value}:{hash(str(content))}"
    assert key not in learning._learning_attempts
    assert key not in learning._failed_learnings

@pytest.mark.asyncio
async def test_relearn_knowledge(learning):
    """Test relearning with updated content"""
    # Initial learning
    initial_content = {"version": 1}
    updated_content = {"version": 2}
    
    evidence = [
        Evidence(
            source="test",
            content={"test": "data"},
            confidence=0.9,
            timestamp=datetime.utcnow()
        )
    ]
    
    # Learn initial version
    await learning.learn(
        knowledge_type=KnowledgeType.CONCEPT,
        content=initial_content,
        evidence=evidence
    )
    
    # Relearn with updated content
    success = await learning.relearn(
        knowledge_type=KnowledgeType.CONCEPT,
        identifier=str(hash(str(initial_content))),
        new_content=updated_content,
        evidence=evidence
    )
    
    assert success

@pytest.mark.asyncio
async def test_learning_validation(learning):
    """Test validation of learned information"""
    content = {"test": "data"}
    identifier = str(hash(str(content)))
    
    # Learn with validation
    await learning.learn(
        knowledge_type=KnowledgeType.FACT,
        content=content,
        evidence=[
            Evidence(
                source="test",
                content={"validation": True},
                confidence=0.9,
                timestamp=datetime.utcnow()
            )
        ]
    )
    
    # Check validation status
    status = await learning.validate_learning(
        knowledge_type=KnowledgeType.FACT,
        identifier=identifier
    )
    
    assert status["exists"]
    assert "confidence_trend" in status
    assert status["learning_attempts"] == 1

@pytest.mark.asyncio
async def test_concurrent_learning(learning):
    """Test concurrent learning operations"""
    content_list = [{"id": i} for i in range(5)]
    evidence = [
        Evidence(
            source="test",
            content={"test": "data"},
            confidence=0.9,
            timestamp=datetime.utcnow()
        )
    ]
    
    # Learn multiple items concurrently
    tasks = [
        learning.learn(
            knowledge_type=KnowledgeType.FACT,
            content=content,
            evidence=evidence
        )
        for content in content_list
    ]
    
    results = await asyncio.gather(*tasks)
    assert all(results)

@pytest.mark.asyncio
async def test_evidence_confidence_calculation(learning):
    """Test confidence calculation from evidence"""
    now = datetime.utcnow()
    evidence = [
        Evidence(
            source="test",
            content={"test": "data"},
            confidence=0.9,
            timestamp=now
        ),
        Evidence(
            source="test",
            content={"test": "data"},
            confidence=0.8,
            timestamp=now - timedelta(hours=1)
        )
    ]
    
    # Learn with multiple evidence
    success = await learning.learn(
        knowledge_type=KnowledgeType.FACT,
        content={"test": "data"},
        evidence=evidence
    )
    
    assert success

@pytest.mark.asyncio
async def test_learning_persistence(learning, memory):
    """Test persistence of learned information"""
    content = {"test": "persistent data"}
    key = f"knowledge:{KnowledgeType.FACT.value}:{hash(str(content))}"
    
    # Learn with high confidence
    await learning.learn(
        knowledge_type=KnowledgeType.FACT,
        content=content,
        evidence=[
            Evidence(
                source="test",
                content={"test": "data"},
                confidence=0.95,
                timestamp=datetime.utcnow()
            )
        ]
    )
    
    # Verify storage in memory
    stored = await memory.retrieve(key)
    assert stored is not None
    assert stored["content"] == content

@pytest.mark.asyncio
async def test_error_handling(learning):
    """Test error handling in learning operations"""
    # Invalid knowledge type
    with pytest.raises(ValueError):
        await learning.learn(
            knowledge_type="invalid",
            content={"test": "data"},
            evidence=[]
        )
    
    # Missing evidence
    success = await learning.learn(
        knowledge_type=KnowledgeType.FACT,
        content={"test": "data"},
        evidence=[]
    )
    assert not success
    
    # Invalid identifier
    success = await learning.unlearn(
        knowledge_type=KnowledgeType.FACT,
        identifier=None
    )
    assert not success

@pytest.mark.asyncio
async def test_relearn_nonexistent(learning):
    """Test relearning nonexistent knowledge"""
    success = await learning.relearn(
        knowledge_type=KnowledgeType.FACT,
        identifier="nonexistent",
        new_content={"test": "data"},
        evidence=[
            Evidence(
                source="test",
                content={"test": "data"},
                confidence=0.9,
                timestamp=datetime.utcnow()
            )
        ]
    )
    
    assert not success

@pytest.mark.asyncio
async def test_learning_cleanup(learning):
    """Test cleanup of learning tracking"""
    content = {"test": "data"}
    key = f"knowledge:{KnowledgeType.FACT.value}:{hash(str(content))}"
    
    # Add some tracking data
    learning._learning_attempts[key] = 1
    learning._failed_learnings.add(key)
    
    # Unlearn should clean up tracking
    await learning.unlearn(
        knowledge_type=KnowledgeType.FACT,
        identifier=str(hash(str(content)))
    )
    
    assert key not in learning._learning_attempts
    assert key not in learning._failed_learnings

if __name__ == "__main__":
    pytest.main([__file__])
