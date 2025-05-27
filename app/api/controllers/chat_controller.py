"""Controller for chat-related endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import verify_and_get_user
from app.models.user import User
from app.schemas.chat_schemas import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatResponseSchema,
    ChatContext
)
from app.services.chat_service import ChatService
from app.chaetra.utils.event_system import get_event_system
from app.chaetra.memory import MemorySystem
from app.chaetra.learning import LearningSystem
from app.chaetra.reasoning import ReasoningSystem
from app.chaetra.opinion import OpinionSystem
from app.chaetra.llm import LLMManager
from app.chaetra.brain import CHAETRA
from app.services.market_data_service import MarketDataService
from app.services.analysis_service import AnalysisService

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: int,
    chat_service: ChatService = Depends(get_chat_service)
):
    """WebSocket endpoint for real-time chat updates."""
    try:
        # Get protocols list from the WebSocket connection request
        protocols = websocket.scope.get("subprotocols", [])
        if not protocols:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        protocol = protocols[0]  # Get the first protocol
        if not protocol.startswith("bearer."):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get token from protocol header
        token = protocol.replace("bearer.", "", 1)
        
        # Validate token and get user
        try:
            async with AsyncSession(chat_service.session_factory) as db:
                user = await verify_and_get_user(token=token, db=db)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept(subprotocol=protocol)
        
        # Add websocket to event system
        await chat_service.add_websocket(session_id, websocket)
        
        try:
            while True:
                # Wait for messages from the client
                data = await websocket.receive_json()
                
                # Process the message
                if message_content := data.get("content"):
                    message = ChatMessageCreate(
                        content=message_content,
                        session_id=session_id,
                        context=ChatContext(**data.get("context", {})) if data.get("context") else None
                    )
                    
                    # Process message through chat service
                    await chat_service.process_new_message(
                        message,
                        user_id=user.id
                    )
                
        except Exception as e:
            await websocket.send_json({
                "event": "error",
                "data": str(e)
            })
            
    except Exception as e:
        print(f"WebSocket connection failed: {e}")
        
    finally:
        # Clean up websocket connection
        await chat_service.remove_websocket(session_id, websocket)

@router.post("/messages/", response_model=ChatResponseSchema)
async def create_message(
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponseSchema:
    """Create a new chat message and get response."""
    return await chat_service.process_new_message(message, current_user.id)

# Dependency
async def get_chat_service(
    db: AsyncSession = Depends(get_db)
) -> ChatService:
    """Get chat service instance."""
    # Initialize core CHAETRA systems
    memory_system = MemorySystem()
    learning_system = LearningSystem()
    reasoning_system = ReasoningSystem()
    opinion_system = OpinionSystem()
    llm_manager = LLMManager()

    # Initialize CHAETRA brain with all systems
    chaetra_brain = CHAETRA(
        memory_system=memory_system,
        learning_system=learning_system,
        reasoning_system=reasoning_system,
        opinion_system=opinion_system,
        llm_manager=llm_manager
    )
    
    # Initialize additional services
    market_data_service = MarketDataService()
    analysis_service = AnalysisService()
    
    # Create and return ChatService instance
    return ChatService(
        session_factory=db,
        memory_system=memory_system,
        chaetra_brain=chaetra_brain,
        market_data_service=market_data_service,
        analysis_service=analysis_service
    )
