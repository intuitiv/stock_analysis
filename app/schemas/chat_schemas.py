"""Chat-related schema definitions."""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Union, Type
from pydantic import BaseModel, Field

class ProcessingEventType(str, Enum):
    """Types of processing events."""
    INTENT = "intent"
    PROCESSING = "processing"
    ANALYSIS = "analysis"
    THOUGHT = "thought"
    LEARNING = "learning"
    ERROR = "error"
    INFO = "info"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"

class ChatContext(BaseModel):
    """Chat context for CHAETRA."""
    domain: str = Field(default="market")
    intent: Optional[str] = None
    symbols: List[str] = Field(default_factory=list)
    timeframe: Optional[str] = None
    analysis_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatSessionBase(BaseModel):
    """Base chat session schema."""
    user_id: int
    title: Optional[str] = None
    context: Optional[ChatContext] = None

class ChatSessionCreate(ChatSessionBase):
    """Create chat session schema."""
    pass

class ChatSessionUpdate(ChatSessionBase):
    """Update chat session schema."""
    title: Optional[str] = None
    context: Optional[ChatContext] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatSession(ChatSessionBase):
    """Chat session schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "from_attributes": True
    }

class ChatSessionResponse(ChatSession):
    """Chat session response schema with messages."""
    messages: List['ChatMessageResponse'] = Field(default_factory=list)
    total_messages: int = 0

    model_config = {
        "from_attributes": True
    }

class ChatMessageBase(BaseModel):
    """Base chat message schema."""
    content: str
    session_id: int
    context: Optional[ChatContext] = None

class ChatMessageCreate(ChatMessageBase):
    """Create chat message schema."""
    pass

class ChatMessage(ChatMessageBase):
    """Chat message schema."""
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    role: str = "user"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "from_attributes": True
    }

class ChatMessageResponse(ChatMessage):
    """Chat message response schema."""
    feedback: Optional['MessageFeedback'] = None
    events: List['ProcessingEvent'] = Field(default_factory=list)
    assistant_response: Optional[str] = None
    processing_time: Optional[float] = None
    assistant_response_details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    context_at_message: Optional[ChatContext] = None

    @property
    def timestamp(self) -> datetime:
        """Get message timestamp (same as created_at)."""
        return self.created_at

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()}
    }

class MessageFeedback(BaseModel):
    """Message feedback schema."""
    message_id: int
    user_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()}
    }

class ProcessingEvent(BaseModel):
    """Event during message processing."""
    event: ProcessingEventType
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatResponse(BaseModel):
    """Response message schema."""
    content: str
    events: List[ProcessingEvent] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatResponseSchema(BaseModel):
    """Complete response schema."""
    session_id: int
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    updated_context: ChatContext = Field(default_factory=ChatContext)

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()}
    }

class StreamEvent(BaseModel):
    """Event streamed to WebSocket clients."""
    event: Union[ProcessingEventType, str]  # Allow string for legacy events and direct WebSocket control
    data: Union[str, Dict[str, Any]]
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def is_control_event(self) -> bool:
        """Check if this is a WebSocket control event (ping/pong/close)."""
        return self.event in [ProcessingEventType.PING, ProcessingEventType.PONG, ProcessingEventType.CLOSE]

__all__ = [
    'ProcessingEventType',
    'ChatContext',
    'ChatSessionBase',
    'ChatSessionCreate',
    'ChatSessionUpdate',
    'ChatSession',
    'ChatSessionResponse',
    'ChatMessageBase',
    'ChatMessageCreate',
    'ChatMessage',
    'ChatMessageResponse',
    'MessageFeedback',
    'ProcessingEvent',
    'ChatResponse',
    'ChatResponseSchema',
    'StreamEvent'
]
