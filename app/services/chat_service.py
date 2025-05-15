from typing import List, Optional, Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException, status, WebSocket
from datetime import datetime, timedelta
import logging
import json
import asyncio

from app.core.database import get_db
from app.models.user import User as UserModel
from app.models.chat import (
    ChatSession as ChatSessionModel,
    ChatMessage as ChatMessageModel,
    MessageRole
)
from app.schemas.chat_schemas import (
    ChatMessageCreate, ChatContext, ChatResponseSchema, ChatMessageResponse,
    ChatSessionResponse, ChatSessionUpdate, MessageFeedback,
    StreamEventType, StreamEvent # Added for streaming
)
from app.chaetra.brain import CHAETRA
from app.services.market_data_service import MarketDataService
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(
        self,
        chaetra_brain: CHAETRA,
        market_data_service: MarketDataService,
        analysis_service: AnalysisService
    ):
        self.chaetra = chaetra_brain
        self.market_data_service = market_data_service
        self.analysis_service = analysis_service
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def process_new_message(
        self, 
        db: Session,
        message_in: ChatMessageCreate, 
        user_id: int
    ) -> ChatResponseSchema:
        """Process a new incoming chat message from a user."""
        logger.info(f"Processing new message for user {user_id}, session_id: {message_in.session_id}")
        session = await self._get_or_create_session(db, message_in.session_id, user_id, message_in.context)
        logger.info(f"Using session {session.id}")

        # Store user message
        db_user_message = ChatMessageModel(
            session_id=session.id,
            role=MessageRole.USER,
            content=message_in.content,
            message_metadata=message_in.context.dict() if message_in.context else session.context
        )
        db.add(db_user_message)
        db.commit()
        db.refresh(db_user_message)
        logger.info(f"User message {db_user_message.id} stored for session {session.id}")

        try:
            logger.info("Understanding query intent...")
            current_chat_context = message_in.context if message_in.context else ChatContext(**session.context)
            query_intent = await self.chaetra.understand_query_intent(
                message_in.content,
                current_chat_context.dict(),
                provider_name="gemini"
            )
            logger.info(f"Query intent understood: {query_intent}")
            
            if not query_intent.get("can_handle", True):
                 raise HTTPException(
                     status_code=status.HTTP_400_BAD_REQUEST,
                     detail=query_intent.get("error_message", "Query cannot be processed.")
                 )

            input_data_for_chaetra = {}
            naetra_thought_process = []
            entities = query_intent.get("entities", {})
            symbols = entities.get("symbols", [])
            query_type = query_intent.get("query_type", "unknown")

            logger.info(f"NAETRA: Intent symbols: {symbols}, Query type: {query_type}")
            naetra_thought_process.append(f"Intent identified. Symbols: {symbols or 'None'}. Query type: {query_type}.")

            if symbols:
                primary_symbol = symbols[0]
                naetra_thought_process.append(f"Processing primary symbol: {primary_symbol}")
                input_data_for_chaetra[primary_symbol] = {}
                
                try:
                    profile = await self.market_data_service.get_company_profile(primary_symbol)
                    input_data_for_chaetra[primary_symbol]["profile"] = profile
                    naetra_thought_process.append(f"Profile for {primary_symbol} fetched.")
                except Exception as e:
                    logger.error(f"Error fetching profile: {e}")
                    naetra_thought_process.append(f"Error fetching profile: {str(e)}")

                try:
                    quote = await self.market_data_service.get_current_quote(primary_symbol)
                    input_data_for_chaetra[primary_symbol]["quote"] = quote
                    naetra_thought_process.append(f"Quote fetched.")
                except Exception as e:
                    logger.error(f"Error fetching quote: {e}")
                    naetra_thought_process.append(f"Error fetching quote: {str(e)}")

                if query_type == "technical_analysis":
                    try:
                        technical_data = await self.analysis_service.get_technical_analysis_report(primary_symbol)
                        input_data_for_chaetra[primary_symbol]["technical_analysis"] = technical_data
                        naetra_thought_process.append(f"Technical analysis fetched.")
                    except Exception as e:
                        logger.error(f"Error fetching technical analysis: {e}")
                        naetra_thought_process.append(f"Error fetching technical analysis: {str(e)}")
            else:
                naetra_thought_process.append("No specific stock symbols identified.")

            request_context = {
                "user_id": user_id,
                "session_id": session.id,
                "current_symbols": symbols,
                "current_timeframe": entities.get("timeframe"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Processing data and generating analysis...")
            chaetra_response_data = await self.chaetra.process_data_and_generate_analysis(
                input_data=input_data_for_chaetra,
                query_intent=query_intent,
                request_context=request_context
            )
            logger.info("CHAETRA response generated.")

            # Store assistant message
            assistant_message_metadata = current_chat_context.dict()
            assistant_message_metadata["chaetra_full_response"] = json.loads(json.dumps(chaetra_response_data, default=str))
            assistant_message_metadata["naetra_thought_process"] = naetra_thought_process

            db_assistant_message = ChatMessageModel(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=chaetra_response_data.get("analysis", {}).get("analysis_summary", "Could not generate a response."),
                message_metadata=assistant_message_metadata
            )
            db.add(db_assistant_message)
            
            if chaetra_response_data.get("updated_context"):
                session.context.update(chaetra_response_data["updated_context"])
            session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(db_assistant_message)
            logger.info(f"Assistant message {db_assistant_message.id} stored")

            # Construct responses
            user_msg_response = ChatMessageResponse(
                id=db_user_message.id,
                session_id=session.id,
                role=MessageRole.USER,
                content=db_user_message.content,
                timestamp=db_user_message.created_at,
                context_at_message=ChatContext(**db_user_message.message_metadata) if db_user_message.message_metadata else None
            )

            assistant_msg_response = ChatMessageResponse(
                id=db_assistant_message.id,
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=db_assistant_message.content,
                timestamp=db_assistant_message.created_at,
                context_at_message=current_chat_context,
                assistant_response_details={
                    "charts": chaetra_response_data.get("analysis", {}).get("charts_for_frontend"),
                    "actionable_insights": chaetra_response_data.get("analysis", {}).get("actionable_insights"),
                    "learning_updates": chaetra_response_data.get("opinion", {}).get("learning_feedback"),
                    "naetra_thought_process": naetra_thought_process
                }
            )

            response = ChatResponseSchema(
                session_id=session.id,
                user_message=user_msg_response,
                assistant_message=assistant_msg_response,
                updated_context=ChatContext(**session.context)
            )

            # Broadcast to WebSocket connections if any
            if session.id in self.active_connections:
                for websocket in self.active_connections[session.id]:
                    try:
                        await websocket.send_json(response.dict())
                    except Exception as e:
                        logger.error(f"Error broadcasting to WebSocket: {e}")

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            error_message_metadata = current_chat_context.dict()
            error_message_metadata["error_details"] = {"error": str(e)}
            db_error_message = ChatMessageModel(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=f"An error occurred: {str(e)}",
                message_metadata=error_message_metadata
            )
            db.add(db_error_message)
            db.commit()
            db.refresh(db_error_message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process message: {str(e)}"
            )

    async def process_stream_message(
        self,
        db: Session,
        message_in: ChatMessageCreate,
        user_id: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a new chat message with streaming updates."""
        session = await self._get_or_create_session(db, message_in.session_id, user_id, message_in.context)
        current_chat_context = message_in.context if message_in.context else ChatContext(**session.context)

        # Store user message
        db_user_message = ChatMessageModel(
            session_id=session.id,
            role=MessageRole.USER,
            content=message_in.content,
            message_metadata=current_chat_context.dict()
        )
        db.add(db_user_message)
        db.commit()
        # We don't need to refresh db_user_message for streaming, but it's good for consistency if accessed later

        try:
            yield StreamEvent(event=StreamEventType.PROCESSING, data="Understanding query intent...").dict()
            query_intent = await self.chaetra.understand_query_intent(
                message_in.content,
                current_chat_context.dict(),
                provider_name="gemini" # Assuming default, or get from config
            )
            yield StreamEvent(event=StreamEventType.INTENT, data=f"Intent: {query_intent.get('query_type', 'unknown')}").dict()

            if not query_intent.get("can_handle", True):
                error_detail = query_intent.get("error_message", "Query cannot be processed by CHAETRA.")
                yield StreamEvent(event=StreamEventType.ERROR, data=error_detail).dict()
                # Optionally, store an error message in DB as assistant response
                return

            input_data_for_chaetra = {}
            naetra_thought_process = [f"Intent identified. Query type: {query_intent.get('query_type', 'unknown')}."]
            entities = query_intent.get("entities", {})
            symbols = entities.get("symbols", [])

            if symbols:
                primary_symbol = symbols[0]
                naetra_thought_process.append(f"Processing primary symbol: {primary_symbol}")
                yield StreamEvent(event=StreamEventType.PROCESSING, data=f"Fetching data for {primary_symbol}...").dict()
                input_data_for_chaetra[primary_symbol] = {}

                async def fetch_and_yield(task_name: str, awaitable_task, data_key: str):
                    try:
                        data = await awaitable_task
                        input_data_for_chaetra[primary_symbol][data_key] = data
                        naetra_thought_process.append(f"{task_name} for {primary_symbol} fetched.")
                        yield StreamEvent(event=StreamEventType.DATA_FETCH, data=f"{task_name} for {primary_symbol} retrieved.").dict()
                    except Exception as e:
                        logger.error(f"Error fetching {task_name} for {primary_symbol}: {e}")
                        naetra_thought_process.append(f"Error fetching {task_name}: {str(e)}")
                        yield StreamEvent(event=StreamEventType.ERROR, data=f"Error fetching {task_name} for {primary_symbol}: {str(e)}").dict()

                async for event in fetch_and_yield("Profile", self.market_data_service.get_company_profile(primary_symbol), "profile"):
                    yield event
                async for event in fetch_and_yield("Quote", self.market_data_service.get_current_quote(primary_symbol), "quote"):
                    yield event

                if query_intent.get("query_type") == "technical_analysis":
                    async for event in fetch_and_yield("Technical Analysis", self.analysis_service.get_technical_analysis_report(primary_symbol), "technical_analysis"):
                        yield event
            else:
                naetra_thought_process.append("No specific stock symbols identified.")
                yield StreamEvent(event=StreamEventType.PROCESSING, data="No specific stock symbols identified. Proceeding with general query.").dict()


            request_context = {
                "user_id": user_id,
                "session_id": session.id,
                "current_symbols": symbols,
                "current_timeframe": entities.get("timeframe"),
                "timestamp": datetime.utcnow().isoformat()
            }

            yield StreamEvent(event=StreamEventType.PROCESSING, data="Generating analysis...").dict()
            # For actual token-by-token streaming from LLM, CHAETRA brain needs to support async generator
            # For now, we simulate it by sending the full response once generated.
            # To implement true token streaming, self.chaetra.process_data_and_generate_analysis would need to be an async generator
            # and yield tokens/chunks.

            chaetra_response_data = await self.chaetra.process_data_and_generate_analysis(
                input_data=input_data_for_chaetra,
                query_intent=query_intent,
                request_context=request_context
            )
            naetra_thought_process.append("CHAETRA analysis generated.")
            yield StreamEvent(event=StreamEventType.ANALYSIS, data="Analysis complete.").dict()

            # Store assistant message
            assistant_content = chaetra_response_data.get("analysis", {}).get("analysis_summary", "Could not generate a response.")
            assistant_message_metadata = current_chat_context.dict()
            assistant_message_metadata["chaetra_full_response"] = json.loads(json.dumps(chaetra_response_data, default=str)) # Ensure serializable
            assistant_message_metadata["naetra_thought_process"] = naetra_thought_process

            db_assistant_message = ChatMessageModel(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=assistant_content,
                message_metadata=assistant_message_metadata
            )
            db.add(db_assistant_message)

            if chaetra_response_data.get("updated_context"):
                session.context.update(chaetra_response_data["updated_context"])
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_assistant_message) # Refresh to get ID and other DB-generated fields

            # Construct the final ChatMessageResponse object to send
            # This is similar to what the non-streaming version does
            final_assistant_msg_response = ChatMessageResponse(
                id=db_assistant_message.id,
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=db_assistant_message.content,
                timestamp=db_assistant_message.created_at,
                context_at_message=current_chat_context, # Or ChatContext(**db_assistant_message.message_metadata)
                assistant_response_details={
                    "charts": chaetra_response_data.get("analysis", {}).get("charts_for_frontend"),
                    "actionable_insights": chaetra_response_data.get("analysis", {}).get("actionable_insights"),
                    "learning_updates": chaetra_response_data.get("opinion", {}).get("learning_feedback"),
                    "naetra_thought_process": naetra_thought_process
                }
            )
            yield StreamEvent(event=StreamEventType.FINAL, data=final_assistant_msg_response.model_dump_json()).dict()

        except HTTPException as e: # Handle HTTPExceptions raised by sub-components if any
            logger.error(f"HTTP error during stream processing: {e.detail}")
            yield StreamEvent(event=StreamEventType.ERROR, data=e.detail).dict()
        except Exception as e:
            logger.error(f"Unexpected error during stream processing: {e}", exc_info=True)
            yield StreamEvent(event=StreamEventType.ERROR, data=f"An unexpected error occurred: {str(e)}").dict()
            # Optionally, store an error message in DB
            error_message_metadata = current_chat_context.dict()
            error_message_metadata["error_details"] = {"error": str(e)}
            db_error_message = ChatMessageModel(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=f"Stream error: {str(e)}",
                message_metadata=error_message_metadata
            )
            db.add(db_error_message)
            db.commit()

    async def update_session(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        update_data: ChatSessionUpdate
    ) -> ChatSessionResponse:
        """Update a chat session's metadata."""
        session = await self._get_session(db, session_id, user_id)
        
        if update_data.title is not None:
            session.title = update_data.title
        if update_data.context:
            session.context.update(update_data.context.dict(exclude_unset=True))
        
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        
        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            initial_context=ChatContext(**session.context) if session.context else None,
            messages=[]
        )

    async def delete_session(
        self,
        db: Session,
        session_id: int,
        user_id: int
    ) -> None:
        """Delete a chat session and all its messages."""
        session = await self._get_session(db, session_id, user_id)
        if session.id in self.active_connections:
            # Close any active WebSocket connections
            for websocket in self.active_connections[session.id]:
                try:
                    await websocket.close()
                except Exception:
                    pass
            del self.active_connections[session.id]
        db.delete(session)
        db.commit()

    async def process_message_feedback(
        self,
        db: Session,
        message_id: int,
        user_id: int,
        feedback: MessageFeedback
    ) -> None:
        """Process feedback on a message and use it for CHAETRA learning."""
        message = db.query(ChatMessageModel).join(ChatSessionModel).filter(
            ChatMessageModel.id == message_id,
            ChatSessionModel.user_id == user_id
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or access denied"
            )

        # Store feedback in message metadata
        if not message.message_metadata:
            message.message_metadata = {}
        if "feedback" not in message.message_metadata:
            message.message_metadata["feedback"] = []
        
        message.message_metadata["feedback"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": feedback.type,
            "comment": feedback.comment,
            "rating": feedback.rating,
            "context": feedback.context
        })

        db.commit()

        # If this was an assistant message, send feedback to CHAETRA for learning
        if message.role == MessageRole.ASSISTANT:
            chaetra_response = message.message_metadata.get("chaetra_full_response")
            if chaetra_response:
                await self.chaetra.learn_from_interaction_outcome(
                    interaction_data={
                        "query_intent": chaetra_response.get("intent"),
                        "input_data_summary": chaetra_response.get("input_data"),
                        "chaetra_response": chaetra_response,
                        "request_context": chaetra_response.get("request_context")
                    },
                    actual_outcome={
                        "feedback_type": feedback.type,
                        "rating": feedback.rating,
                        "matches_belief": feedback.type == "helpful",
                        "additional_context": feedback.context
                    }
                )

    async def register_websocket(
        self,
        session_id: int,
        websocket: WebSocket
    ) -> None:
        """Register a WebSocket connection for a chat session."""
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    async def remove_websocket(
        self,
        session_id: int,
        websocket: WebSocket
    ) -> None:
        """Remove a WebSocket connection when it's closed."""
        if session_id in self.active_connections:
            try:
                self.active_connections[session_id].remove(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
            except ValueError:
                pass

    async def _get_or_create_session(
        self,
        db: Session,
        session_id: Optional[int],
        user_id: int,
        initial_context: Optional[ChatContext] = None
    ) -> ChatSessionModel:
        """Get an existing session or create a new one."""
        if session_id:
            session = db.query(ChatSessionModel).filter(
                ChatSessionModel.id == session_id,
                ChatSessionModel.user_id == user_id
            ).first()
            if session:
                if initial_context:
                    session.context.update(initial_context.dict(exclude_none=True))
                    session.updated_at = datetime.utcnow()
                    db.commit()
                    db.refresh(session)
                return session
            else:
                logger.warning(f"Session {session_id} not found for user {user_id}")

        new_session_context = initial_context.dict(exclude_none=True) if initial_context else {}
        session = ChatSessionModel(user_id=user_id, context=new_session_context)
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info(f"Created new chat session {session.id} for user {user_id}")
        return session

    async def _get_session(
        self,
        db: Session,
        session_id: int,
        user_id: int
    ) -> ChatSessionModel:
        """Get a chat session, ensuring the user has access."""
        session = db.query(ChatSessionModel).filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found or access denied"
            )
        
        return session

    async def get_chat_history(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> ChatSessionResponse:
        """Get chat session history with pagination."""
        session = await self._get_session(db, session_id, user_id)
        
        messages = db.query(ChatMessageModel)\
            .filter(ChatMessageModel.session_id == session_id)\
            .order_by(ChatMessageModel.created_at.asc())\
            .limit(limit).offset(offset).all()
        
        message_responses = []
        for msg in messages:
            msg_context_data = msg.message_metadata or {}
            assistant_resp_details = None
            
            if msg.role == MessageRole.ASSISTANT:
                raw_resp = msg_context_data.get("chaetra_full_response", {})
                assistant_resp_details = {
                    "charts": raw_resp.get("analysis", {}).get("charts_for_frontend"),
                    "actionable_insights": raw_resp.get("analysis", {}).get("actionable_insights"),
                    "learning_updates": raw_resp.get("opinion", {}).get("learning_feedback"),
                    "naetra_thought_process": msg_context_data.get("naetra_thought_process", [])
                }
            
            context_for_response = msg_context_data
            if msg.role == MessageRole.ASSISTANT and "chaetra_full_response" in msg_context_data:
                context_for_response = {
                    k: v for k, v in msg_context_data.items() 
                    if k not in ["chaetra_full_response", "naetra_thought_process"]
                }

            message_responses.append(
                ChatMessageResponse(
                    id=msg.id,
                    session_id=msg.session_id,
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.created_at,
                    context_at_message=ChatContext(**context_for_response) if context_for_response else None,
                    assistant_response_details=assistant_resp_details
                )
            )

        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            initial_context=ChatContext(**session.context) if session.context else None,
            messages=message_responses
        )

    async def get_user_chat_sessions(
        self,
        db: Session,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[ChatSessionResponse]:
        """Get a list of chat sessions for a user."""
        sessions = db.query(ChatSessionModel)\
            .filter(ChatSessionModel.user_id == user_id)\
            .order_by(ChatSessionModel.updated_at.desc())\
            .limit(limit).offset(offset).all()
        
        return [
            ChatSessionResponse(
                id=s.id,
                user_id=s.user_id,
                created_at=s.created_at,
                updated_at=s.updated_at,
                initial_context=ChatContext(**s.context) if s.context else None,
                messages=[]
            ) for s in sessions
        ]
