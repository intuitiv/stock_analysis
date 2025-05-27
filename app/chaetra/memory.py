"""Memory system implementation for CHAETRA."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from collections import defaultdict
from dataclasses import asdict

from app.chaetra.interfaces import MemoryItem, IMemorySystem
from app.chaetra.utils.event_system import get_event_system
from app.schemas.chat_schemas import ProcessingEventType

class MemorySystem(IMemorySystem):
    def __init__(self):
        """Initialize memory system."""
        self.memories: Dict[str, MemoryItem] = {}
        self.index: defaultdict = defaultdict(list)
        self.event_system = get_event_system()
        
    async def store_memory(self, item: Dict[str, Any]) -> str:
        """Store a new memory item."""
        # Generate unique ID
        memory_id = str(uuid.uuid4())
        
        # Create memory item
        memory_item = MemoryItem(
            id=memory_id,
            content=item,
            relevance=1.0,  # Initial relevance
            timestamp=datetime.utcnow(),
            metadata=item.get("metadata")
        )
        
        # Store memory
        self.memories[memory_id] = memory_item
        
        # Index memory content for retrieval
        self._index_memory(memory_item)
        
        return memory_id
        
    async def retrieve_memory(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[MemoryItem]:
        """Retrieve relevant memories based on query."""
        session_id = query.get("session_id", 0)
        
        await self.event_system.emit(
            session_id,
            ProcessingEventType.PROCESSING,
            "Searching memory store...",
            {"query": query}
        )
        
        # Find relevant memories
        relevant_memories = []
        for memory in self.memories.values():
            relevance_score = self._calculate_relevance(memory, query)
            if relevance_score > query.get("confidence_threshold", 0.5):
                # Update memory relevance
                memory.relevance = relevance_score
                relevant_memories.append(memory)
        
        # Sort by relevance and recency
        relevant_memories.sort(
            key=lambda x: (
                x.relevance * query.get("recency_weight", 0.7) +
                (1 - query.get("recency_weight", 0.7)) * 
                (datetime.utcnow() - x.timestamp).total_seconds()
            ),
            reverse=True
        )
        
        # Apply limit if specified
        if limit:
            relevant_memories = relevant_memories[:limit]
            
        await self.event_system.emit(
            session_id,
            ProcessingEventType.PROCESSING,
            "Memory retrieval complete",
            {
                "found_count": len(relevant_memories),
                "relevance_scores": [m.relevance for m in relevant_memories]
            }
        )
        
        return relevant_memories
    
    def _calculate_relevance(self, memory: MemoryItem, query: Dict[str, Any]) -> float:
        """Calculate relevance score for a memory item against a query."""
        # Simple relevance calculation - could be enhanced with embeddings, etc.
        relevance = 0.0
        query_relevance = query.get("relevance_to", "")
        
        # Check primary content match
        if query_relevance in str(memory.content):
            relevance += 0.5
            
        # Check context match
        query_context = query.get("context_match", {})
        memory_context = memory.content.get("context", {})
        
        matching_context = sum(
            1 for k, v in query_context.items()
            if k in memory_context and memory_context[k] == v
        )
        if matching_context:
            relevance += 0.3 * (matching_context / len(query_context))
            
        # Add metadata match
        if memory.metadata and query.get("metadata"):
            matching_meta = sum(
                1 for k, v in query.get("metadata", {}).items()
                if k in memory.metadata and memory.metadata[k] == v
            )
            if matching_meta:
                relevance += 0.2 * (matching_meta / len(query.get("metadata")))
                
        return min(1.0, relevance)
    
    def _index_memory(self, memory: MemoryItem) -> None:
        """Index memory item for faster retrieval."""
        # Index main content tokens
        content_str = str(memory.content)
        for token in content_str.split():
            self.index[token].append(memory.id)
            
        # Index metadata tokens if present
        if memory.metadata:
            meta_str = str(memory.metadata)
            for token in meta_str.split():
                self.index[token].append(memory.id)
