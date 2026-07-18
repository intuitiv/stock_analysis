"""
Unit tests for CHAETRA's LLM processor.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.chaetra.llm import LLMProcessor, LLMProvider
from app.core.config import get_settings
from aiohttp import ClientSession, ClientResponse

settings = get_settings()

@pytest.fixture
def llm():
    """Create LLM processor instance"""
    return LLMProcessor()

@pytest.fixture
def mock_session():
    """Create mock aiohttp session"""
    session = MagicMock(spec=ClientSession)
    response = AsyncMock(spec=ClientResponse)
    response.status = 200
    session.post.return_value.__aenter__.return_value = response
    return session

@pytest.fixture
def sample_text():
    """Sample text for processing"""
    return "Analyze the current market sentiment for AAPL based on technical indicators."

@pytest.fixture
def sample_context():
    """Sample context for LLM requests"""
    return {
        "format": "json",
        "system_prompt": "You are a financial analyst."
    }

@pytest.mark.asyncio
async def test_ollama_processing(llm, mock_session, sample_text, sample_context):
    """Test Ollama LLM processing"""
    mock_response = {
        "response": "Market sentiment analysis...",
        "context": {"key": "value"}
    }
    mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=mock_response
    )
    
    with patch.object(llm, '_session', mock_session):
        result = await llm.process_text(
            sample_text,
            {**sample_context, "provider": LLMProvider.OLLAMA}
        )
    
    assert result is not None
    assert result["provider"] == "ollama"
    assert "response" in result
    assert result["response"] == mock_response["response"]

@pytest.mark.asyncio
async def test_openai_processing(llm, mock_session, sample_text, sample_context):
    """Test OpenAI LLM processing"""
    mock_response = {
        "choices": [{
            "message": {
                "content": "Market analysis result...",
                "role": "assistant"
            },
            "finish_reason": "stop"
        }]
    }
    mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=mock_response
    )
    
    with patch.object(llm, '_session', mock_session):
        result = await llm.process_text(
            sample_text,
            {**sample_context, "provider": LLMProvider.OPENAI}
        )
    
    assert result is not None
    assert result["provider"] == "openai"
    assert "response" in result
    assert isinstance(result["response"], str)

@pytest.mark.asyncio
async def test_gemini_processing(llm, mock_session, sample_text, sample_context):
    """Test Gemini LLM processing"""
    mock_response = {
        "candidates": [{
            "content": {
                "parts": [{"text": "Analysis results..."}]
            },
            "safetyRatings": []
        }]
    }
    mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=mock_response
    )
    
    with patch.object(llm, '_session', mock_session):
        result = await llm.process_text(
            sample_text,
            {**sample_context, "provider": LLMProvider.GEMINI}
        )
    
    assert result is not None
    assert result["provider"] == "gemini"
    assert "response" in result
    assert isinstance(result["response"], str)

@pytest.mark.asyncio
async def test_response_generation(llm, mock_session, sample_text):
    """Test response generation"""
    mock_response = {"response": "Generated response..."}
    mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=mock_response
    )
    
    with patch.object(llm, '_session', mock_session):
        response = await llm.generate_response(sample_text)
    
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_knowledge_extraction(llm, mock_session):
    """Test knowledge extraction from text"""
    input_text = """
    AAPL has formed a double bottom pattern on the daily chart,
    with RSI showing bullish divergence and MACD crossing above signal line.
    """
    
    mock_response = {
        "response": json.dumps({
            "key_concepts": ["double bottom", "bullish divergence"],
            "relationships": [{"type": "confirms", "items": ["RSI", "MACD"]}],
            "confidence": 0.85
        })
    }
    mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=mock_response
    )
    
    with patch.object(llm, '_session', mock_session):
        knowledge = await llm.extract_knowledge(input_text)
    
    assert knowledge is not None
    assert "key_concepts" in knowledge
    assert "relationships" in knowledge
    assert "confidence" in knowledge

@pytest.mark.asyncio
async def test_response_caching(llm, mock_session, sample_text, sample_context):
    """Test response caching"""
    mock_response = {"response": "Cached response..."}
    mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=mock_response
    )
    
    with patch.object(llm, '_session', mock_session):
        # First call
        first_result = await llm.process_text(sample_text, sample_context)
        # Second call with same input
        second_result = await llm.process_text(sample_text, sample_context)
    
    # Should be identical due to caching
    assert first_result == second_result
    # Session post should only be called once
    assert mock_session.post.call_count == 1

@pytest.mark.asyncio
async def test_error_handling(llm, mock_session, sample_text):
    """Test error handling"""
    # Simulate API error
    mock_session.post.side_effect = Exception("API Error")
    
    with patch.object(llm, '_session', mock_session):
        result = await llm.process_text(sample_text)
    
    assert "error" in result
    assert result["error"] == "API Error"
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_session_management(llm):
    """Test session management"""
    # Session should be created on first use
    assert llm._session is None
    await llm._ensure_session()
    assert llm._session is not None
    
    # Get session should return existing session
    session1 = await llm._get_session()
    session2 = await llm._get_session()
    assert session1 is session2

@pytest.mark.asyncio
async def test_provider_selection(llm, mock_session, sample_text):
    """Test provider selection logic"""
    mock_response = {"response": "Test response"}
    mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=mock_response
    )
    
    with patch.object(llm, '_session', mock_session):
        # Test default provider
        result1 = await llm.process_text(sample_text)
        assert result1["provider"] == settings.DEFAULT_LLM_PROVIDER
        
        # Test explicit provider
        result2 = await llm.process_text(
            sample_text,
            {"provider": LLMProvider.OLLAMA}
        )
        assert result2["provider"] == "ollama"

@pytest.mark.asyncio
async def test_invalid_provider(llm, sample_text):
    """Test handling of invalid provider"""
    with pytest.raises(ValueError):
        await llm.process_text(
            sample_text,
            {"provider": "invalid_provider"}
        )

@pytest.mark.asyncio
async def test_context_handling(llm, mock_session, sample_text):
    """Test context handling in requests"""
    test_context = {
        "system_prompt": "You are an expert.",
        "temperature": 0.7,
        "format": "json"
    }
    
    with patch.object(llm, '_session', mock_session):
        await llm.process_text(sample_text, test_context)
    
    # Verify context was properly included in request
    call_kwargs = mock_session.post.call_args.kwargs
    assert "json" in call_kwargs
    request_body = call_kwargs["json"]
    
    if settings.DEFAULT_LLM_PROVIDER == LLMProvider.OPENAI:
        assert "temperature" in request_body
        assert request_body["temperature"] == 0.7
    elif settings.DEFAULT_LLM_PROVIDER == LLMProvider.OLLAMA:
        assert "context" in request_body

@pytest.mark.asyncio
async def test_concurrent_requests(llm, mock_session):
    """Test handling of concurrent requests"""
    mock_response = {"response": "Concurrent test response"}
    mock_session.post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=mock_response
    )
    
    with patch.object(llm, '_session', mock_session):
        # Make multiple concurrent requests
        tasks = [
            llm.process_text(f"Request {i}")
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)
    
    assert len(results) == 5
    assert all(r.get("response") == "Concurrent test response" for r in results)

if __name__ == "__main__":
    pytest.main([__file__])
