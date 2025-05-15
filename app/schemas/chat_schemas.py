"""
Pydantic schemas for chat functionality.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system" # For system-generated messages or initial prompts

class ChatContext(BaseModel):
    """Schema for chat context data."""
    current_symbol: Optional[str] = None
    current_timeframe: Optional[str] = None
    active_portfolio_id: Optional[int] = None
    user_risk_profile: Optional[str] = Field("moderate", description="User's risk profile for investment suggestions")

# Base schemas
class ChatSessionBase(BaseModel):
    """Base schema for chat sessions."""
    title: Optional[str] = Field(None, max_length=255)
    context: ChatContext = Field(default_factory=ChatContext)

class ChatMessageBase(BaseModel):
    """Base schema for chat messages."""
    content: str = Field(..., min_length=1)

# Create schemas
class ChatSessionCreate(ChatSessionBase):
    """Schema for creating a new chat session."""
    pass

class ChatMessageCreate(BaseModel):
    """Schema for creating a new chat message."""
    session_id: Optional[int] = None
    content: str = Field(..., min_length=1)
    context: Optional[ChatContext] = None

# Update schemas
class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session."""
    title: Optional[str] = Field(None, max_length=255)
    context: Optional[ChatContext] = None

# Response schemas
class ChatMessageResponse(BaseModel):
    """Schema for chat message responses."""
    id: int
    session_id: int
    role: MessageRole
    content: str
    timestamp: datetime
    context_at_message: Optional[ChatContext] = None
    assistant_response_details: Optional[Dict[str, Any]] = Field(None, description="Structured response data from assistant if applicable")

    class Config:
        from_attributes = True

class ChatSessionResponse(ChatSessionBase):
    """Schema for chat session responses."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True

class ChatResponseSchema(BaseModel):
    """Schema for the API response after processing a user's chat message."""
    session_id: int
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    updated_context: ChatContext

# List schemas
class ChatSessionList(BaseModel):
    """Schema for list of chat sessions."""
    items: List[ChatSessionResponse]
    total: int

class ChatMessageList(BaseModel):
    """Schema for list of chat messages."""
    items: List[ChatMessageResponse]
    total: int

# Feedback schemas
class FeedbackType(str, Enum):
    """Types of feedback that can be provided."""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    NEEDS_CLARIFICATION = "needs_clarification"
    IRRELEVANT = "irrelevant"

class MessageFeedback(BaseModel):
    """Schema for providing feedback on a message."""
    type: FeedbackType
    comment: Optional[str] = Field(None, max_length=1000)
    context: Optional[Dict[str, Any]] = None  # Additional context/metadata about the feedback
    rating: Optional[int] = Field(None, ge=1, le=5)  # Optional 1-5 rating

    class Config:
        schema_extra = {
            "example": {
                "type": "helpful",
                "comment": "The analysis was very clear and actionable",
                "rating": 5,
                "context": {"market_condition": "bullish", "acted_on_advice": True}
            }
        }

# Streaming Schemas
class StreamEventType(str, Enum):
    """Types of events in a streaming response."""
    PROCESSING = "processing"
    INTENT = "intent"
    DATA_FETCH = "data_fetch"
    ANALYSIS = "analysis"
    FINAL = "final"
    ERROR = "error"

class StreamEvent(BaseModel):
    """Schema for a single event in a streaming response."""
    event: StreamEventType
    data: str # Can be a simple string for processing messages, or JSON string for complex data
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
