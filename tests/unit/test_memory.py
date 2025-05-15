"""
Unit tests for CHAETRA's memory system.
"""

import pytest
from datetime import datetime, timedelta

from app.chaetra.memory import MemorySystem
from app.chaetra.interfaces import Evidence
from app.core.config import get_settings

settings = get_settings()

@pytest.fixture
async def memory():
    """Create memory system instance"""
    return MemorySystem()

@pytest.mark.asyncio
async def test_short_term_storage(memory):
    """Test storing and retrieving from short-term memory"""
    test_data = {"test": "data"}
    key = "test_key"
    
    # Store data
    success = await memory.store_short_term(key, test_data)
    assert success
    
    # Retrieve data
    retrieved = await memory.retrieve(key, memory_type="short_term")
    assert retrieved == test_data

@pytest.mark.asyncio
async def test_core_storage(memory):
    """Test storing and retrieving from core memory"""
    test_data = {"test": "data"}
    key = "test_key"
    confidence = 0.9
    
    # Store data
    success = await memory.store_core(key, test_data, confidence)
    assert success
    
    # Retrieve data
    retrieved = await memory.retrieve(key, memory_type="core")
    assert retrieved == test_data

@pytest.mark.asyncio
async def test_memory_retrieval_priority(memory):
    """Test memory retrieval priority (short-term over core)"""
    key = "test_key"
    short_term_data = {"source": "short_term"}
    core_data = {"source": "core"}
    
    # Store in both memories
    await memory.store_short_term(key, short_term_data)
    await memory.store_core(key, core_data, 0.9)
    
    # Retrieve - should get short-term data
    retrieved = await memory.retrieve(key)
    assert retrieved == short_term_data

@pytest.mark.asyncio
async def test_knowledge_validation(memory):
    """Test knowledge validation process"""
    key = "test_knowledge"
    content = {"fact": "test fact"}
    
    # Store in short-term memory
    await memory.store_short_term(key, content)
    
    # Create evidence
    evidence = [
        Evidence(
            source="test",
            content={"validation": "pass"},
            confidence=0.9,
            timestamp=datetime.utcnow()
        )
        for _ in range(settings.CHAETRA_LEARNING_MIN_VALIDATIONS)
    ]
    
    # Validate knowledge
    validated = False
    for e in evidence:
        validated = await memory.validate_knowledge(key, e)
    
    assert validated
    
    # Check if moved to core memory
    core_data = await memory.retrieve(key, memory_type="core")
    assert core_data is not None

@pytest.mark.asyncio
async def test_memory_expiration(memory):
    """Test memory expiration"""
    key = "expiring_key"
    data = {"test": "data"}
    ttl = 1  # 1 second
    
    # Store with short TTL
    await memory.store_short_term(key, data, ttl)
    
    # Verify immediate retrieval
    assert await memory.retrieve(key, "short_term") == data
    
    # Wait for expiration
    await asyncio.sleep(ttl + 0.1)
    
    # Verify expired
    assert await memory.retrieve(key, "short_term") is None

@pytest.mark.asyncio
async def test_forget_operation(memory):
    """Test forgetting from both memories"""
    key = "forget_key"
    data = {"test": "data"}
    
    # Store in both memories
    await memory.store_short_term(key, data)
    await memory.store_core(key, data, 0.9)
    
    # Verify storage
    assert await memory.retrieve(key, "short_term") == data
    assert await memory.retrieve(key, "core") == data
    
    # Forget
    success = await memory.forget(key)
    assert success
    
    # Verify forgotten
    assert await memory.retrieve(key, "short_term") is None
    assert await memory.retrieve(key, "core") is None

@pytest.mark.asyncio
async def test_validation_period(memory):
    """Test validation period constraints"""
    key = "validation_test"
    content = {"test": "data"}
    
    # Store in short-term memory
    await memory.store_short_term(key, content)
    
    # Create evidence spread over time
    now = datetime.utcnow()
    evidence = [
        Evidence(
            source="test",
            content={"validation": "pass"},
            confidence=0.9,
            timestamp=now - timedelta(seconds=i * 3600)  # 1 hour apart
        )
        for i in range(settings.CHAETRA_LEARNING_MIN_VALIDATIONS)
    ]
    
    # Validate knowledge - should fail due to time spread
    validated = False
    for e in evidence:
        validated = await memory.validate_knowledge(key, e)
    
    assert not validated  # Should not validate due to period constraint

@pytest.mark.asyncio
async def test_confidence_threshold(memory):
    """Test confidence threshold for validation"""
    key = "confidence_test"
    content = {"test": "data"}
    
    # Store in short-term memory
    await memory.store_short_term(key, content)
    
    # Create low confidence evidence
    evidence = [
        Evidence(
            source="test",
            content={"validation": "pass"},
            confidence=0.3,  # Below threshold
            timestamp=datetime.utcnow()
        )
        for _ in range(settings.CHAETRA_LEARNING_MIN_VALIDATIONS)
    ]
    
    # Validate knowledge - should fail due to low confidence
    validated = False
    for e in evidence:
        validated = await memory.validate_knowledge(key, e)
    
    assert not validated

@pytest.mark.asyncio
async def test_memory_consistency(memory):
    """Test memory consistency across operations"""
    key = "consistency_test"
    initial_data = {"version": 1}
    updated_data = {"version": 2}
    
    # Initial store
    await memory.store_short_term(key, initial_data)
    retrieved = await memory.retrieve(key, "short_term")
    assert retrieved == initial_data
    
    # Update
    await memory.store_short_term(key, updated_data)
    retrieved = await memory.retrieve(key, "short_term")
    assert retrieved == updated_data
    
    # Move to core
    await memory.store_core(key, updated_data, 0.9)
    retrieved = await memory.retrieve(key, "core")
    assert retrieved == updated_data
    
    # Forget
    await memory.forget(key)
    assert await memory.retrieve(key, "both") is None

@pytest.mark.asyncio
async def test_concurrent_operations(memory):
    """Test concurrent memory operations"""
    keys = [f"concurrent_key_{i}" for i in range(10)]
    data = {"test": "data"}
    
    # Concurrent stores
    tasks = [
        memory.store_short_term(key, data)
        for key in keys
    ]
    results = await asyncio.gather(*tasks)
    assert all(results)
    
    # Concurrent retrievals
    tasks = [
        memory.retrieve(key)
        for key in keys
    ]
    results = await asyncio.gather(*tasks)
    assert all(r == data for r in results)
    
    # Concurrent forgets
    tasks = [
        memory.forget(key)
        for key in keys
    ]
    results = await asyncio.gather(*tasks)
    assert all(results)

@pytest.mark.asyncio
async def test_error_handling(memory):
    """Test error handling in memory operations"""
    # Invalid key
    assert await memory.retrieve(None) is None
    
    # Invalid data
    success = await memory.store_short_term("error_key", object())  # Non-serializable
    assert not success
    
    # Invalid confidence
    success = await memory.store_core("error_key", {"test": "data"}, -1.0)
    assert not success
    
    # Invalid evidence
    success = await memory.validate_knowledge(
        "error_key",
        Evidence(
            source="test",
            content=None,
            confidence=-1.0,
            timestamp=datetime.utcnow()
        )
    )
    assert not success

if __name__ == "__main__":
    pytest.main([__file__])
