"""
Chat models for user interactions and conversations.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin

class MessageRole(enum.Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatSession(Base, TimestampMixin, UUIDMixin):
    """Model for chat sessions."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String)
    context = Column(JSON)  # Session context, including any relevant analysis IDs
    is_active = Column(Boolean, default=True)
    session_metadata = Column(JSON)  # Additional session metadata

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id})>"

    @property
    def last_message(self):
        """Get the last message in this session."""
        if not self.messages:
            return None
        return max(self.messages, key=lambda m: m.created_at)

class ChatMessage(Base, TimestampMixin, UUIDMixin):
    """Model for individual chat messages."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON)  # For storing additional message data

    # Optional fields for tracking analysis results
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"))

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    analysis = relationship("Analysis")
    analysis_result = relationship("AnalysisResult")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"
