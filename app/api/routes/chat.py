"""Chat routes."""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketState
from app.chaetra.utils.DateTimeEncoder import safe_datetime_to_string

from app.core.database import get_db, async_session_maker
from app.core.dependencies import get_current_user, get_chat_service
from app.core.security import verify_and_get_user
from app.models.user import User
from app.schemas.chat_schemas import (
    ChatSession,
    ChatMessage,
    ChatMessageCreate,
    ChatContext,
    ProcessingEventType
)
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["chat"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid authentication credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "Not enough privileges"}
    }
)

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: int
):
    """WebSocket endpoint for real-time chat updates."""
    logger.info(f"Initializing WebSocket connection for session {session_id}")
    chat_service = get_chat_service()
    is_connected = False
    message_content = None

    try:
        # Get protocols list from WebSocket connection request
        protocols = websocket.scope.get("subprotocols", [])
        if not protocols:
            logger.warning(f"No WebSocket protocols provided for session {session_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        protocol = protocols[0]  # Get the first protocol
        if not protocol.startswith("bearer."):
            logger.warning(f"Invalid protocol format for session {session_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get token from protocol header
        token = protocol.replace("bearer.", "", 1)
        
        # Accept the connection before any async operations
        await websocket.accept(subprotocol=protocol)
        is_connected = True
        logger.info(f"WebSocket connection accepted for session {session_id}")

        # Validate token and get user
        try:
            async with async_session_maker() as db:
                user = await verify_and_get_user(token=token, db=db)
        except Exception as e:
            logger.error(f"Token validation failed: {e}", exc_info=True)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        logger.info(f"Token validated for user {user.username} in session {session_id}")
        await chat_service.add_websocket(session_id, websocket)

        while True:
            data = await websocket.receive_json()
            message_content = data.get("content", "")
            
            if not message_content:
                continue

            logger.info(f"Processing message for session {session_id}: {message_content[:100]}...")
            
            context_data = data.get("context", {})
            if not isinstance(context_data, dict):
                context_data = {}
            context_data.setdefault("response_type", "info")
            
            # Handle ping/pong messages
            if data.get("event") == "pong":
                # Update last activity timestamp
                chat_service.event_system.last_activity[session_id] = datetime.utcnow()
                continue

            if data.get("event") == "close":
                logger.info(f"Client requested close for session {session_id}")
                await chat_service.event_system._close_session(session_id)
                break
            
            try:
                context = ChatContext(**context_data) if context_data else None
                message = ChatMessageCreate(
                    content=message_content,
                    session_id=session_id,
                    context=context
                )
                # Update activity timestamp for message processing
                chat_service.event_system.last_activity[session_id] = datetime.utcnow()

                response = await chat_service.process_new_message(message, user.id)
                logger.info(f"Message processed successfully for session {session_id}")
                
                if response:
                    await chat_service.emit_final(session_id, response.dict())

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                if websocket.application_state == WebSocketState.CONNECTED:
                    error_details = safe_datetime_to_string({
                        "event": "error",
                        "data": {
                            "message": f"Failed to process message: {str(e)}",
                            "type": "processing_error",
                            "timestamp": datetime.utcnow(),
                            "details": {
                                "session_id": session_id,
                                "query": message_content,
                                "error_type": type(e).__name__
                            }
                        }
                    })
                    await websocket.send_json(error_details)
                raise

    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {e}", exc_info=True)
        if is_connected and websocket.application_state == WebSocketState.CONNECTED:
            try:
                await websocket.close(code=1011)  # Internal Error
            except:
                pass
                
    finally:
        if is_connected:
            logger.info(f"Cleaning up WebSocket for session {session_id}")
            await chat_service.remove_websocket(session_id, websocket)

@router.post("/session", response_model=ChatSession)
async def create_chat_session(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatSession:
    """Create a new chat session."""
    service = ChatService()
    return await service.create_session(db, current_user)

@router.post("/message", response_model=ChatMessage)
async def send_message(
    message: str,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatMessage:
    """Send a message in a chat session."""
    service = ChatService()
    return await service.send_message(db, current_user, session_id, message)
