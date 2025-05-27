"""Chat service for handling chat sessions and messages with CHAETRA integration."""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
from fastapi import WebSocket, HTTPException, status
from datetime import datetime
import logging
import json
import asyncio
from starlette.websockets import WebSocketState

from app.models.user import User as UserModel
from app.chaetra.utils.DateTimeEncoder import safe_datetime_to_string
from app.models.chat import (
    ChatSession as ChatSessionModel,
    ChatMessage as ChatMessageModel,
    MessageRole
)
from app.schemas.chat_schemas import (
    ChatMessageCreate, ChatContext, ChatResponseSchema, ChatMessageResponse,
    ChatSessionResponse, ChatSessionUpdate, MessageFeedback,
    StreamEvent, ProcessingEventType
)
from app.chaetra.brain import CHAETRA
from app.chaetra.memory import MemorySystem
from app.services.market_data_service import MarketDataService
from app.services.analysis_service import AnalysisService
from app.core.database import async_session_maker
from app.chaetra.utils.event_system import get_event_system, EventSystem

logger = logging.getLogger(__name__)

class ChatService:
    """Service for managing chat interactions with CHAETRA"""

    def __init__(
        self,
        session_factory: AsyncSession,
        memory_system: MemorySystem,
        chaetra_brain: Optional[CHAETRA] = None,
        market_data_service: Optional[MarketDataService] = None,
        analysis_service: Optional[AnalysisService] = None
    ):
        """Initialize chat service with required dependencies"""
        self.session_factory = session_factory
        self.memory_system = memory_system
        self.chaetra = chaetra_brain
        self.market_data_service = market_data_service
        self.analysis_service = analysis_service
        self.event_system = get_event_system()

    async def process_new_message(
        self, 
        message_in: ChatMessageCreate, 
        user_id: int
    ) -> ChatResponseSchema:
        """Process a new incoming chat message and emit events."""
        async with async_session_maker() as db:
            try:
                session = await self._get_or_create_session(db, message_in.session_id, user_id, message_in.context)
                session_id = session.id
                
                # Use event system for processing updates
                async with self.event_system.session_context(session_id):
                    logger.info(f"Using session {session_id}")

                    # Store user message
                    db_user_message = ChatMessageModel(
                        session_id=session_id,
                        role=MessageRole.USER,
                        content=message_in.content,
                        message_metadata=message_in.context.dict() if message_in.context else session.context
                    )
                    db.add(db_user_message)
                    await db.commit()
                    await db.refresh(db_user_message)
                    
                    await self.event_system.emit(
                        session_id,
                        ProcessingEventType.INFO,
                        "User message stored",
                        {"message_id": db_user_message.id}
                    )

                    if not self.chaetra:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="CHAETRA brain not available"
                        )

                    current_chat_context = message_in.context if message_in.context else ChatContext(**session.context)
                    try:
                        # Process through CHAETRA
                        domain_context = safe_datetime_to_string({
                            "user_id": user_id,
                            "session_id": session_id,
                            "chat_context": current_chat_context.dict(),
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "chat_service"
                        })
                        
                        available_tools = {
                            "market_data": bool(self.market_data_service),
                            "analysis": bool(self.analysis_service)
                        }

                        # Process the query
                        chaetra_response = await self.chaetra.process_input(
                            query=message_in.content,
                            domain_context=domain_context,
                            available_tools=available_tools,
                            session_id=session_id
                        )

                        # Store assistant message
                        assistant_message = await self._store_assistant_message(
                            db, session, current_chat_context, chaetra_response
                        )

                        # Create response objects
                        response = self._create_chat_response(
                            db_user_message, assistant_message, chaetra_response,
                            current_chat_context, session
                        )

                        # Send final response and close connection
                        await self.event_system.emit_final(session_id, response.dict())

                        return response

                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        await self._store_error_message(db, session, str(e), current_chat_context)
                        if isinstance(e, HTTPException):
                            raise
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to process message: {str(e)}"
                        )
            except Exception as e:
                await db.rollback()
                raise
            finally:
                await db.close()

    async def _get_or_create_session(
        self,
        db: AsyncSession,
        session_id: Optional[int],
        user_id: int,
        context: Optional[ChatContext] = None
    ) -> ChatSessionModel:
        """Get existing chat session or create a new one."""
        if session_id:
            # Get existing session
            stmt = select(ChatSessionModel).where(
                ChatSessionModel.id == session_id,
                ChatSessionModel.user_id == user_id
            )
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
            
            # Update context if provided
            if context:
                session.context.update(context.dict())
                await db.commit()
                await db.refresh(session)
            
            return session
        else:
            # Create new session
            new_session = ChatSessionModel(
                user_id=user_id,
                title=f"Chat Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                context=context.dict() if context else {}
            )
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session

    async def _store_assistant_message(
        self,
        db: AsyncSession,
        session: ChatSessionModel,
        context: ChatContext,
        response_data: Dict[str, Any]
    ) -> ChatMessageModel:
        """Store the assistant's response message."""
        message_metadata = context.dict()
        message_metadata["chaetra_full_response"] = json.loads(json.dumps(response_data, default=str))
        
        # Extract content from reasoning and opinion
        analysis_content = ""
        if reasoning_result := response_data.get("reasoning_process"):
            analysis_content = reasoning_result.get("conclusion", "")
        
        if opinion_data := response_data.get("formed_opinion"):
            if opinion_content := opinion_data.get("summary"):
                analysis_content = f"{analysis_content}\n\n{opinion_content}" if analysis_content else opinion_content

        # Fallback content if no analysis or opinion is available
        if not analysis_content:
            analysis_content = "Could not generate a response."

        message = ChatMessageModel(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=analysis_content.strip(),
            message_metadata=message_metadata
        )
        db.add(message)
        
        # Update session context with query understanding
        if query_understanding := response_data.get("query_understanding"):
            session.context.update({"last_query_understanding": query_understanding})
        session.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(message)
        return message

    def _create_chat_response(
        self,
        user_message: ChatMessageModel,
        assistant_message: ChatMessageModel,
        chaetra_response: Dict[str, Any],
        context: ChatContext,
        session: ChatSessionModel
    ) -> ChatResponseSchema:
        """Create the chat response object."""
        try:
            # Create user message response
            user_msg_response = ChatMessageResponse(
                id=user_message.id,
                session_id=session.id,
                role=MessageRole.USER.value,
                content=user_message.content,
                created_at=user_message.created_at,
                context_at_message=ChatContext(**user_message.message_metadata) if user_message.message_metadata else None,
                metadata=user_message.message_metadata or {}
            )

            # Extract thought process
            thought_process = []
            if reasoning_result := chaetra_response.get("reasoning_process"):
                thought_process.extend(reasoning_result.get("path", []))

            # Create assistant message response
            assistant_msg_response = ChatMessageResponse(
                id=assistant_message.id,
                session_id=session.id,
                role=MessageRole.ASSISTANT.value,
                content=assistant_message.content,
                created_at=assistant_message.created_at,
                context_at_message=context,
                metadata=assistant_message.message_metadata or {},
                assistant_response_details={
                    "charts": chaetra_response.get("reasoning_process", {}).get("charts", []),
                    "actionable_insights": chaetra_response.get("reasoning_process", {}).get("insights", []),
                    "learning_updates": chaetra_response.get("processing_metadata", {}).get("learning_feedback", []),
                    "naetra_thought_process": thought_process,
                    "confidence": chaetra_response.get("confidence", 0.0)
                }
            )

            response = ChatResponseSchema(
                session_id=session.id,
                user_message=user_msg_response,
                assistant_message=safe_datetime_to_string(assistant_msg_response),
                updated_context=ChatContext(**session.context)
            )

            return response

        except Exception as e:
            logger.error(f"Error creating chat response: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create chat response: {str(e)}"
            )

    async def _store_error_message(
        self,
        db: AsyncSession,
        session: ChatSessionModel,
        error: str,
        context: ChatContext
    ) -> None:
        """Store an error message in the database."""
        error_metadata = context.dict()
        error_metadata["error_details"] = {"error": error}
        message = ChatMessageModel(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=f"An error occurred: {error}",
            message_metadata=error_metadata
        )
        db.add(message)
        await db.commit()

    async def add_websocket(self, session_id: int, websocket: WebSocket) -> None:
        """Add a WebSocket connection to a chat session with retry logic."""
        max_retries = 3
        retry_delay = 0.1  # 100ms

        for attempt in range(max_retries):
            try:
                self.event_system.add_websocket(session_id, websocket)
                logger.info(f"WebSocket added for session {session_id}")
                return
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    logger.error(f"Failed to add WebSocket after {max_retries} attempts: {e}", exc_info=True)
                    raise
                logger.warning(f"Failed to add WebSocket (attempt {attempt + 1}): {e}")
                await asyncio.sleep(retry_delay)

    async def remove_websocket(self, session_id: int, websocket: WebSocket) -> None:
        """Remove a WebSocket connection with cleanup."""
        try:
            await self.event_system.remove_websocket(session_id, websocket)
            logger.info(f"WebSocket removed from session {session_id}")
        except Exception as e:
            logger.error(f"Error removing WebSocket from session {session_id}: {e}", exc_info=True)
            # Try closing the websocket directly as a fallback
            try:
                if websocket.application_state != WebSocketState.DISCONNECTED:
                    await websocket.close(code=1001)  # Going away
            except Exception as close_error:
                logger.error(f"Failed to close WebSocket: {close_error}", exc_info=True)

    async def emit_final(self, session_id: int, result: Dict[str, Any]) -> None:
        """Emit final result through the event system."""
        try:
            # Send final result with success status
            result["status"] = "success"
            result["timestamp"] = datetime.utcnow().isoformat()
            await self.event_system.emit_final(session_id, result)
        except Exception as e:
            logger.error(f"Error emitting final result for session {session_id}: {e}", exc_info=True)
            # Try to emit error event
            try:
                await self.event_system.emit(
                    session_id,
                    ProcessingEventType.ERROR,
                    f"Failed to send final response: {str(e)}",
                    {"error": str(e), "close_connection": True}
                )
            except:
                # If error event fails, just log it
                logger.error("Failed to emit error event", exc_info=True)
