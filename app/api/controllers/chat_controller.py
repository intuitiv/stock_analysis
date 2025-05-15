from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body, WebSocket, WebSocketDisconnect, Header
from sse_starlette.sse import EventSourceResponse # Added for SSE
import logging
from sqlalchemy.orm import Session
import json
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.chaetra.utils.DateTimeEncoder import DateTimeEncoder
from app.services.chat_service import ChatService
from app.schemas import chat_schemas as schemas
from app.core.security import get_current_active_user, verify_access_token, get_current_user
from app.models.user import User as UserModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependencies for ChatService
from app.chaetra.brain import CHAETRA
from app.services.market_data_service import MarketDataService
from app.services.analysis_service import AnalysisService
from app.services.analysis.technical import TechnicalAnalyzer
from app.services.analysis.fundamental import FundamentalAnalyzer
from app.services.analysis.sentiment import SentimentAnalyzer
from app.chaetra.llm import LLMManager

from app.core.dependencies import get_chat_service

@router.post("/message", response_model=schemas.ChatResponseSchema, status_code=status.HTTP_200_OK)
@router.post("/", response_model=schemas.ChatResponseSchema, status_code=status.HTTP_200_OK)
async def send_chat_message(
    message_in: schemas.ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a new message in a chat session.
    If `session_id` is not provided, a new session will be created.
    """
    try:
        logger.info(f"[CHAT] Incoming request - User ID: {current_user.id}, Session ID: {message_in.session_id}")
        response = await chat_service.process_new_message(
            db=db, 
            message_in=message_in, 
            user_id=current_user.id
        )
        logger.info(f"Successfully processed chat message for user {current_user.id}")
        return response
    except HTTPException as e:
        logger.error(f"HTTP error processing chat message: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing chat message: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/sessions", response_model=List[schemas.ChatSessionResponse])
async def list_user_chat_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    List all chat sessions for the current user.
    """
    return await chat_service.get_user_chat_sessions(
        db=db, 
        user_id=current_user.id, 
        limit=limit, 
        offset=skip
    )

@router.get("/sessions/{session_id}", response_model=schemas.ChatSessionResponse)
async def get_chat_session_history(
    session_id: int = Path(..., description="The ID of the chat session to retrieve"),
    message_limit: int = Query(50, ge=1, le=200),
    message_offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Retrieve a specific chat session and its message history.
    """
    session_with_history = await chat_service.get_chat_history(
        db=db, 
        session_id=session_id, 
        user_id=current_user.id, 
        limit=message_limit, 
        offset=message_offset
    )
    if not session_with_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Chat session not found"
        )
    return session_with_history

@router.put("/sessions/{session_id}", response_model=schemas.ChatSessionResponse)
async def update_chat_session(
    session_id: int,
    session_update: schemas.ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Update a chat session's metadata (title, context).
    """
    try:
        updated_session = await chat_service.update_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            update_data=session_update
        )
        return updated_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete a chat session and all its messages.
    """
    try:
        await chat_service.delete_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )

@router.post("/messages/{message_id}/feedback", status_code=status.HTTP_200_OK)
async def provide_message_feedback(
    message_id: int,
    feedback: schemas.MessageFeedback,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Provide feedback on a specific message for CHAETRA learning.
    """
    try:
        await chat_service.process_message_feedback(
            db=db,
            message_id=message_id,
            user_id=current_user.id,
            feedback=feedback
        )
        return {"status": "Feedback processed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {str(e)}"
        )

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: int,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    WebSocket endpoint for real-time chat interaction.
    """
    try:
        # Get token from Sec-WebSocket-Protocol header
        protocols = websocket.headers.get('sec-websocket-protocol', '').split(',')
        token = None
        for protocol in protocols:
            if protocol.strip().startswith('bearer.'):
                token = protocol.strip().replace('bearer.', '')
                break
        
        if not token:
            logger.error("No valid bearer token found in WebSocket protocols")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        token_data = await verify_access_token(token)
        user = await get_current_user(token_data=token_data, db=db)
        # Now check if user is active
        if not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get the selected protocol with the token
        selected_protocol = next(
            (p.strip() for p in websocket.headers.get('sec-websocket-protocol', '').split(',')
            if p.strip().startswith('bearer.')),
            None
        )
        
        # Accept the connection with the selected protocol
        await websocket.accept(subprotocol=selected_protocol)
        
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()
                message_content = data.get("content")
                if not message_content:
                    await websocket.send_json({"error": True, "message": "Content is required."})
                    continue

                message_in = schemas.ChatMessageCreate(
                    session_id=session_id, # Use session_id from path
                    content=message_content,
                    context=data.get("context") # Optional context from client
                )
                
                # Process message using the streaming service method
                async for event_dict in chat_service.process_stream_message(
                    db=db,
                    message_in=message_in,
                    user_id=user.id
                ):
                    json_str = json.dumps(event_dict, cls=DateTimeEncoder)
                    await websocket.send_text(json_str)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                await chat_service.remove_websocket(session_id, websocket) # Ensure cleanup
                break
            except Exception as e:
                logger.error(f"Error in WebSocket session {session_id}: {str(e)}", exc_info=True)
                error_response = {
                    "event": "error", # Consistent with StreamEventType
                    "data": str(e)
                }
                try:
                    json_str = json.dumps(error_response, cls=DateTimeEncoder)
                    await websocket.send_text(json_str)
                except Exception: # If sending fails, socket might be already closed
                    pass
                
    except Exception as e: # Handles errors during initial connection or user auth
        logger.error(f"WebSocket connection error for session {session_id}: {str(e)}", exc_info=True)
        # Attempt to close gracefully if possible, though it might already be closed
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
    finally:
        # Ensure the websocket is removed from active connections on any exit
        await chat_service.remove_websocket(session_id, websocket)

@router.post("/message/stream", response_class=EventSourceResponse)
@router.get("/message/stream", response_class=EventSourceResponse)
async def stream_chat_message_sse(
    content: str = Query(..., description="Message content"),
    session_id: Optional[int] = Query(None, description="Optional session ID"),
    authorization: str = Header(None, description="Bearer token"),
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a new message and receive a stream of Server-Sent Events.
    """
    try:
        # Check for authorization header
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")

        # Extract and verify token
        token = authorization.split(" ")[1]
        token_data = await verify_access_token(token)
        user = await get_current_active_user(token_data)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        message_in = schemas.ChatMessageCreate(
            content=content,
            session_id=session_id
        )
        logger.info(f"[CHAT-SSE] Incoming stream request - User ID: {user.id}, Session ID: {session_id}")
        
        async def event_generator():
            try:
                async for event_dict in chat_service.process_stream_message(
                    db=db,
                    message_in=message_in,
                    user_id=user.id
                ):
                    # SSE expects 'event' and 'data' fields.
                    # Our StreamEvent schema already matches this if we send event_dict directly.
                    # However, sse-starlette expects data to be a string.
                    event_name = event_dict.get("event")
                    event_data_payload = event_dict.get("data")
                    
                    # Ensure data is a string, typically JSON for complex objects
                    if not isinstance(event_data_payload, str):
                        event_data_str = json.dumps(event_data_payload)
                    else:
                        event_data_str = event_data_payload

                    yield {"event": event_name, "data": event_data_str}
                    await asyncio.sleep(0.01) # Small delay to allow client to process
            except Exception as e:
                logger.error(f"Error during SSE event generation: {str(e)}", exc_info=True)
                # Yield a final error event to the client
                yield {"event": "error", "data": json.dumps({"detail": f"Stream failed: {str(e)}"})}

        return EventSourceResponse(event_generator())
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error setting up SSE stream: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize chat stream: {str(e)}"
        )
