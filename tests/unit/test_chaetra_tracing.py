"""Test cases for CHAETRA's tracing functionality."""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from app.chaetra.brain import CHAETRA
from app.chaetra.utils.event_system import get_event_system
from app.schemas.chat_schemas import ProcessingEventType

@pytest.fixture
def mock_websocket():
    """Create a mock websocket."""
    ws = MagicMock()
    ws.send_json = AsyncMock()
    return ws

@pytest.fixture
def mock_dependencies():
    """Mock CHAETRA dependencies."""
    return {
        "memory_system": MagicMock(retrieve_memory=AsyncMock(return_value=[])),
        "learning_system": MagicMock(learn_from_interaction=AsyncMock()),
        "reasoning_system": MagicMock(analyze=AsyncMock(return_value={
            "conclusion": "Test conclusion",
            "confidence": 0.8,
            "path": ["Step 1", "Step 2"]
        })),
        "opinion_system": MagicMock(form_opinion=AsyncMock(return_value=None)),
        "llm_manager": MagicMock(generate_structured_output=AsyncMock(return_value={
            "primary_goal": "stock analysis",
            "sub_goals": ["check price", "analyze trend"],
            "required_context": {"symbol": "TSLA"}
        }))
    }

@pytest.mark.asyncio
async def test_chaetra_tracing(mock_websocket, mock_dependencies):
    """Test that CHAETRA emits all expected events during processing."""
    # Get event system and register mock websocket
    event_system = get_event_system()
    session_id = 123
    event_system.add_websocket(session_id, mock_websocket)
    
    # Initialize CHAETRA with mock dependencies
    chaetra = CHAETRA(**mock_dependencies)
    
    # Process a test query
    query = "can I buy tesla?"
    result = await chaetra.process_input(
        query=query,
        session_id=session_id
    )
    
    # Verify all expected events were emitted
    expected_events = [
        # Intent events
        {
            "event": ProcessingEventType.INTENT,
            "message": "Understanding query intent...",
            "data": {"query": query}
        },
        {
            "event": ProcessingEventType.INTENT,
            "message": "Query intent understood",
            "data": {
                "primary_goal": "stock analysis",
                "sub_goals": ["check price", "analyze trend"],
                "required_context": {"symbol": "TSLA"}
            }
        },
        
        # Processing events
        {
            "event": ProcessingEventType.PROCESSING,
            "message": "Retrieving relevant memories..."
        },
        {
            "event": ProcessingEventType.PROCESSING,
            "message": "Memory retrieval complete"
        },
        
        # Analysis events
        {
            "event": ProcessingEventType.ANALYSIS,
            "message": "Starting query analysis..."
        },
        
        # Thought events
        {
            "event": ProcessingEventType.THOUGHT,
            "message": "Analyzing available information..."
        },
        {
            "event": ProcessingEventType.THOUGHT,
            "message": "Initial analysis complete"
        },
        
        # Learning events
        {
            "event": ProcessingEventType.LEARNING,
            "message": "Learning from interaction..."
        },
        {
            "event": ProcessingEventType.LEARNING,
            "message": "Learning complete"
        }
    ]
    
    # Check that each expected event was sent to the websocket
    call_args_list = mock_websocket.send_json.call_args_list
    for expected in expected_events:
        event_sent = False
        for call in call_args_list:
            args = call[0][0]  # Get the argument passed to send_json
            if (
                args["event"] == expected["event"] and
                args["message"] == expected["message"]
            ):
                event_sent = True
                break
        assert event_sent, f"Expected event not sent: {expected}"
    
    # Verify final result contains reasoning path
    assert result["reasoning_process"]["path"] == ["Step 1", "Step 2"]
    assert result["confidence"] == 0.8
    assert "query_understanding" in result
    
    # Clean up
    event_system.remove_websocket(session_id, mock_websocket)

@pytest.mark.asyncio
async def test_error_handling(mock_websocket, mock_dependencies):
    """Test that errors are properly emitted as events."""
    # Make memory system raise an error
    mock_dependencies["memory_system"].retrieve_memory.side_effect = Exception("Test error")
    
    # Get event system and register mock websocket
    event_system = get_event_system()
    session_id = 124
    event_system.add_websocket(session_id, mock_websocket)
    
    # Initialize CHAETRA with mock dependencies
    chaetra = CHAETRA(**mock_dependencies)
    
    # Process query and expect error
    with pytest.raises(Exception):
        await chaetra.process_input(
            query="can I buy tesla?",
            session_id=session_id
        )
    
    # Verify error event was emitted
    error_sent = False
    for call in mock_websocket.send_json.call_args_list:
        args = call[0][0]
        if (
            args["event"] == ProcessingEventType.ERROR and
            "Test error" in str(args.get("data", {}))
        ):
            error_sent = True
            break
    
    assert error_sent, "Error event was not emitted"
    
    # Clean up
    event_system.remove_websocket(session_id, mock_websocket)
