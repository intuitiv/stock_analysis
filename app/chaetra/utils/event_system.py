from typing import List, Callable, Dict, Any, Set, Optional, AsyncIterator, Union
import asyncio
import logging
from datetime import datetime
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from contextlib import asynccontextmanager
from app.chaetra.utils.DateTimeEncoder import safe_datetime_to_string
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from contextlib import asynccontextmanager

from app.core.logging import setup_logger
from app.schemas.chat_schemas import ProcessingEvent, ProcessingEventType, StreamEvent

logger = setup_logger("chaetra.events")

class EventSystem:
    _instance = None
    
    def __init__(self):
        """Initialize the event system singleton."""
        self.websockets: Dict[int, Set[WebSocket]] = {}
        self.trace_websockets: Dict[str, Set[WebSocket]] = {}  # Map trace_id to websockets
        self.event_listeners: List[Callable] = []
        self.debug_logger = logger
        self.sequence_counters: Dict[int, int] = {}  # Track event sequence per session
        self.event_buffers: Dict[int, List[StreamEvent]] = {}  # Buffer events per session
        self.trace_buffers: Dict[str, List[Dict[str, Any]]] = {}  # Buffer events by trace_id
        self.buffer_delay = 0.05  # 50ms buffer delay
        self.last_activity: Dict[int, datetime] = {}  # Track last activity for each session
        self._ping_tasks: Dict[int, asyncio.Task] = {}  # Track ping tasks
        self.trace_expiry: Dict[str, datetime] = {}  # Track when to clean up trace data
        
        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._run_trace_cleanup())
        
    async def _run_trace_cleanup(self) -> None:
        """Background task to periodically clean up expired traces."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.clean_expired_traces()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.debug_logger.error(f"Error in trace cleanup task: {e}", exc_info=True)
        
    async def shutdown(self) -> None:
        """Cleanup resources when shutting down."""
        # Cancel trace cleanup task
        if hasattr(self, '_cleanup_task'):
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Cancel all ping tasks
        for task in self._ping_tasks.values():
            task.cancel()
        
        # Close all websockets
        for session_id in list(self.websockets.keys()):
            await self._close_session(session_id)

        # Close all trace websockets
        for trace_id in list(self.trace_websockets.keys()):
            websockets = self.trace_websockets[trace_id].copy()
            for ws in websockets:
                await self.remove_trace_websocket(trace_id, ws)

    @classmethod
    async def get_instance(cls) -> 'EventSystem':
        """Get the singleton instance of EventSystem."""
        if cls._instance is None:
            cls._instance = EventSystem()
        return cls._instance

    @classmethod
    async def destroy_instance(cls) -> None:
        """Cleanup and destroy the singleton instance."""
        if cls._instance is not None:
            await cls._instance.shutdown()
            cls._instance = None
        
    async def emit_thought(
        self,
        trace_id: str,
        thought: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Emit a thought as a server-sent event.
        
        Args:
            trace_id: Trace identifier for request tracking
            thought: The thought content
            timestamp: Optional timestamp (defaults to now)
        """
        if not timestamp:
            timestamp = datetime.utcnow()
            
        event = {
            "type": "thought",
            "content": thought,
            "trace_id": trace_id,
            "timestamp": timestamp.isoformat()
        }
        
        # Log the thought
        self.debug_logger.info(
            f"Thought[{trace_id}]: {thought}",
            extra={"trace_id": trace_id, "type": "thought"}
        )
        
        # Emit as server-sent event
        await self.emit(
            session_id=0,  # Using 0 as default system session
            event_type=ProcessingEventType.INFO,
            message=thought,
            data={
                "trace_id": trace_id,
                "type": "thought",
                "timestamp": timestamp.isoformat()
            }
        )

    async def emit(
        self,
        session_id: int,
        event_type: ProcessingEventType,
        message: str,
        data: Optional[Dict] = None
    ) -> None:
        """Emit an event to all listeners and websockets for the session and trace."""
        # Update activity timestamp for each event
        self.update_activity(session_id)
        
        # Extract trace_id if present in data
        trace_id = data.get("trace_id") if data else None
        
        event = ProcessingEvent(
            event=event_type,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            data=data
        )
        
        # Log the event for debugging
        self.debug_logger.info(
            f"Event[{session_id}]{f'[{trace_id}]' if trace_id else ''}: {event_type} - {message}",
            extra={
                "session_id": session_id,
                "trace_id": trace_id,
                "event_type": event_type,
                "data": data
            }
        )
        
        # Buffer event for trace if applicable
        if trace_id:
            if trace_id not in self.trace_buffers:
                self.trace_buffers[trace_id] = []
            
            trace_event = {
                "event": event_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            self.trace_buffers[trace_id].append(trace_event)
            
            # Send to trace-specific websockets
            if trace_id in self.trace_websockets:
                failed_sockets = set()
                for ws in self.trace_websockets[trace_id]:
                    try:
                        await ws.send_json(trace_event)
                    except Exception as e:
                        self.debug_logger.error(f"Failed to send to trace websocket: {e}")
                        failed_sockets.add(ws)
                
                # Remove failed websockets
                for ws in failed_sockets:
                    await self.remove_trace_websocket(trace_id, ws)
        
        # Notify all websockets for this session
        if session_id in self.websockets:
            # Increment sequence counter for this session
            if session_id not in self.sequence_counters:
                self.sequence_counters[session_id] = 0
            self.sequence_counters[session_id] += 1

            # Create and buffer the event
            stream_event = StreamEvent(
                event=event_type,
                data=message,
                timestamp=datetime.utcnow().isoformat(),
                metadata={
                    "type": event_type,
                    "session_id": session_id,
                    "sequence": self.sequence_counters[session_id],
                    **(data or {})
                }
            )

            # Initialize buffer if needed
            if session_id not in self.event_buffers:
                self.event_buffers[session_id] = []
            
            # Add event to buffer
            self.event_buffers[session_id].append(stream_event)

            # Process buffer if enough time has passed or on certain events
            should_flush = (
                event_type in [ProcessingEventType.ERROR, ProcessingEventType.INFO] or
                len(self.event_buffers[session_id]) >= 5
            )

            failed_sockets = set()
            
            # Process buffered events if needed
            if should_flush:
                for ws in self.websockets[session_id]:
                    try:
                        # Send all buffered events for this websocket
                        for buffered_event in self.event_buffers[session_id]:
                            event_data = safe_datetime_to_string(buffered_event.dict())
                            await ws.send_json(event_data)
                            
                        # Small delay after each batch for smooth UI updates
                        await asyncio.sleep(self.buffer_delay)
                        
                    except Exception as e:
                        self.debug_logger.error(
                            f"Failed to send to websocket: {e}",
                            extra={
                                "session_id": session_id,
                                "event_type": event_type,
                                "error": str(e)
                            },
                            exc_info=True
                        )
                        failed_sockets.add(ws)
                        
                # Clear buffer after attempting to send to all websockets
                self.event_buffers[session_id] = []
            
            # Remove failed websockets
            for ws in failed_sockets:
                await self.remove_websocket(session_id, ws)
                    
        # Notify all event listeners
        for listener in self.event_listeners:
            try:
                await listener(session_id, event)
            except Exception as e:
                self.debug_logger.error(
                    f"Event listener failed: {e}",
                    extra={
                        "session_id": session_id,
                        "event_type": event_type,
                        "error": str(e)
                    },
                    exc_info=True
                )
    
    async def _monitor_connection(self, session_id: int) -> None:
        """Monitor connection status and handle timeouts."""
        from app.core.config import settings
        
        try:
            while session_id in self.websockets:
                await asyncio.sleep(settings.WEBSOCKET_PING_INTERVAL_SECONDS)
                
                # Check last activity
                if session_id in self.last_activity:
                    last_active = self.last_activity[session_id]
                    now = datetime.utcnow()
                    idle_time = (now - last_active).total_seconds()
                    
                    if idle_time > settings.WEBSOCKET_IDLE_TIMEOUT_SECONDS:
                        self.debug_logger.warning(f"Session {session_id} timed out after {idle_time}s of inactivity")
                        await self._close_session(session_id, code=1001, reason="Session timeout")
                        break
                    
                    # Send ping to all connected websockets
                    failed_sockets = set()
                    for ws in self.websockets.get(session_id, set()):
                        try:
                            if ws.application_state == WebSocketState.CONNECTED:
                                await ws.send_json({"event": "ping", "timestamp": now.isoformat()})
                        except Exception as e:
                            self.debug_logger.error(f"Error sending ping: {e}")
                            failed_sockets.add(ws)
                    
                    # Remove failed sockets
                    for ws in failed_sockets:
                        await self.remove_websocket(session_id, ws)
                        
        except asyncio.CancelledError:
            self.debug_logger.info(f"Connection monitor for session {session_id} stopped")
        except Exception as e:
            self.debug_logger.error(f"Error in connection monitor: {e}", exc_info=True)

    async def _close_session(self, session_id: int, code: int = 1000, reason: str = "Normal closure") -> None:
        """Close all websockets for a session and clean up resources."""
        if session_id in self.websockets:
            failed_sockets = set()
            for ws in self.websockets[session_id]:
                try:
                    if ws.application_state != WebSocketState.DISCONNECTED:
                        await ws.close(code=code, reason=reason)
                except Exception as e:
                    self.debug_logger.error(f"Error closing websocket: {e}", exc_info=True)
                    failed_sockets.add(ws)
            
            # Clean up failed sockets
            for ws in failed_sockets:
                await self.remove_websocket(session_id, ws)
            
            # Cancel monitoring task if exists
            if session_id in self._ping_tasks:
                self._ping_tasks[session_id].cancel()
                del self._ping_tasks[session_id]
            
            # Clean up session data
            for key in [session_id]:
                self.websockets.pop(key, None)
                self.sequence_counters.pop(key, None)
                self.event_buffers.pop(key, None)
                self.last_activity.pop(key, None)
            
            self.debug_logger.info(f"Cleaned up session {session_id}")

    async def emit_final(
        self,
        session_id: int,
        result: Dict[str, Any]
    ) -> None:
        """Emit final result without closing the connection."""
        now = datetime.utcnow()
        self.last_activity[session_id] = now
        
        # Send final result
        await self.emit(
            session_id=session_id,
            event_type=ProcessingEventType.INFO,
            message="Final response ready",
            data={
                "final_response": result,
                "timestamp": now.isoformat(),
                "metadata": {"sequence": 998}
            }
        )

        # Send completion event
        await self.emit(
            session_id=session_id,
            event_type=ProcessingEventType.INFO,
            message="Processing complete",
            data={
                "status": "complete",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"sequence": 999}
            }
        )
    
    def update_activity(self, session_id: int) -> None:
        """Update last activity timestamp for a session."""
        self.last_activity[session_id] = datetime.utcnow()

    def add_trace_websocket(
        self,
        trace_id: str,
        websocket: WebSocket,
        expiry_minutes: int = 30
    ) -> None:
        """Register a websocket for a specific trace ID."""
        if trace_id not in self.trace_websockets:
            self.trace_websockets[trace_id] = set()
            self.trace_expiry[trace_id] = datetime.utcnow() + datetime.timedelta(minutes=expiry_minutes)

        self.trace_websockets[trace_id].add(websocket)
        self.debug_logger.info(f"WebSocket added for trace {trace_id}")

    async def remove_trace_websocket(self, trace_id: str, websocket: WebSocket) -> None:
        """Remove a websocket from trace tracking."""
        if trace_id in self.trace_websockets:
            self.trace_websockets[trace_id].discard(websocket)
            if not self.trace_websockets[trace_id]:
                del self.trace_websockets[trace_id]
                if trace_id in self.trace_buffers:
                    del self.trace_buffers[trace_id]
                if trace_id in self.trace_expiry:
                    del self.trace_expiry[trace_id]

    async def clean_expired_traces(self) -> None:
        """Clean up expired trace data."""
        now = datetime.utcnow()
        expired_traces = [
            trace_id for trace_id, expiry in self.trace_expiry.items()
            if now > expiry
        ]
        for trace_id in expired_traces:
            if trace_id in self.trace_websockets:
                websockets = self.trace_websockets[trace_id].copy()
                for ws in websockets:
                    await self.remove_trace_websocket(trace_id, ws)

    def add_websocket(self, session_id: int, websocket: WebSocket) -> None:
        """Register a websocket for a session and start monitoring."""
        if session_id not in self.websockets:
            self.websockets[session_id] = set()
            # Start connection monitoring task
            self._ping_tasks[session_id] = asyncio.create_task(
                self._monitor_connection(session_id)
            )

        self.websockets[session_id].add(websocket)
        self.last_activity[session_id] = datetime.utcnow()
        self.debug_logger.info(f"WebSocket added for session {session_id}")
    
    async def remove_websocket(self, session_id: int, websocket: WebSocket) -> None:
        """Remove a websocket for a session."""
        if session_id in self.websockets:
            self.websockets[session_id].discard(websocket)
            # Handle cleanup of last websocket for session
            if not self.websockets[session_id]:
                # Clean up all session resources
                del self.websockets[session_id]
                if session_id in self.sequence_counters:
                    del self.sequence_counters[session_id]
                if session_id in self.event_buffers:
                    del self.event_buffers[session_id]
                
                self.debug_logger.info(f"Cleaned up all resources for session {session_id}")
            else:
                self.debug_logger.info(f"WebSocket removed from session {session_id}, {len(self.websockets[session_id])} remaining")
            
            self.debug_logger.debug(f"Active sessions: {list(self.websockets.keys())}")
            try:
                if websocket.application_state != WebSocketState.DISCONNECTED:
                    await websocket.close(code=1000)  # Normal closure
            except Exception as e:
                self.debug_logger.warning(f"Error while closing websocket: {e}")
                # Continue with cleanup even if close fails

    def add_listener(self, listener: Callable) -> None:
        """Add a new event listener."""
        if listener not in self.event_listeners:
            self.event_listeners.append(listener)
            self.debug_logger.debug(f"Event listener added: {listener.__name__}")
        
    def remove_listener(self, listener: Callable) -> None:
        """Remove an event listener."""
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)
            self.debug_logger.debug(f"Event listener removed: {listener.__name__}")

    @asynccontextmanager
    async def session_context(self, session_id: int) -> AsyncIterator[None]:
        """Context manager for handling a chat session's lifecycle events."""
        start_time = datetime.utcnow()
        try:
            # Emit starting event
            await self.emit(
                session_id,
                ProcessingEventType.INFO,
                "Starting processing session",
                {
                    "status": "starting",
                    "timestamp": start_time.isoformat(),
                    "metadata": {"sequence": 0}
                }
            )
            yield
        except Exception as e:
            # Emit error event
            await self.emit(
                session_id,
                ProcessingEventType.ERROR,
                f"Session error: {str(e)}",
                {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                    "start_time": start_time.isoformat(),
                    "metadata": {"sequence": -1}  # Error gets priority
                }
            )
            raise
        finally:
            # Always emit completion event
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            await self.emit(
                session_id,
                ProcessingEventType.INFO,
                "Session complete",
                {
                    "status": "complete",
                    "timestamp": end_time.isoformat(),
                    "duration": duration,
                    "metadata": {"sequence": 999}  # Always last
                }
            )
            
            # Add small delay to ensure final event is processed
            await asyncio.sleep(0.1)

    async def get_trace_events(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a specific trace ID.
        
        Args:
            trace_id: The trace identifier to get events for
            
        Returns:
            List of events associated with this trace
        """
        return self.trace_buffers.get(trace_id, [])

# Global instance accessor
async def get_event_system() -> EventSystem:
    """Get the global EventSystem instance asynchronously."""
    return await EventSystem.get_instance()

async def ensure_shutdown():
    """Ensure proper shutdown of the event system."""
    await EventSystem.destroy_instance()
