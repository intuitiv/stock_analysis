"""
Tests for the CHAETRA memory system
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.core.cache import RedisCache
from app.chaetra.memory import MemorySystem
from app.chaetra.utils.DateTimeEncoder import DateTimeEncoder

@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.exists = AsyncMock()
    return redis

@pytest.fixture
def mock_cache(mock_redis):
    cache = RedisCache()
    cache._redis = mock_redis
    return cache

@pytest.fixture
def memory_system(mock_cache):
    return MemorySystem(cache=mock_cache)

@pytest.mark.asyncio
async def test_store_and_retrieve(memory_system, mock_redis):
    # Test data with datetime
    test_data = {
        "timestamp": datetime.utcnow(),
        "value": "test_value"
    }
    
    # Store the data
    await memory_system.store("test_key", test_data)
    
    # Verify data was serialized correctly
    expected_json = json.dumps(test_data, cls=DateTimeEncoder)
    mock_redis.set.assert_called_once_with("chaetra:memory:test_key", expected_json, None)
    
    # Setup mock for retrieval
    mock_redis.get.return_value = expected_json
    
    # Retrieve the data
    retrieved_data = await memory_system.retrieve("test_key")
    
    # Verify retrieved data matches original
    assert retrieved_data["value"] == test_data["value"]
    assert isinstance(retrieved_data["timestamp"], str)  # JSON stores datetime as string

@pytest.mark.asyncio
async def test_store_pattern(memory_system):
    pattern = {
        "type": "test_pattern",
        "data": "test_data"
    }
    
    # Store pattern
    pattern_id = await memory_system.store_pattern(pattern)
    
    # Verify pattern ID format
    assert pattern_id.startswith("pattern:")
    
    # Verify timestamp was added
    stored_pattern = json.loads(memory_system.cache._redis.set.call_args[0][1])
    assert "timestamp" in stored_pattern
    assert isinstance(stored_pattern["timestamp"], str)

@pytest.mark.asyncio
async def test_exists(memory_system, mock_redis):
    # Setup mock
    mock_redis.exists.return_value = True
    
    # Check if key exists
    exists = await memory_system.exists("test_key")
    
    # Verify result
    assert exists is True
    mock_redis.exists.assert_called_once_with("chaetra:memory:test_key")

@pytest.mark.asyncio
async def test_forget(memory_system, mock_redis):
    # Delete a key
    await memory_system.forget("test_key")
    
    # Verify deletion
    mock_redis.delete.assert_called_once_with("chaetra:memory:test_key")
