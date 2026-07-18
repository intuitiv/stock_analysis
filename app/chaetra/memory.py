"""Memory system implementation for CHAETRA."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from app.core.cache import RedisCache
from app.chaetra.interfaces import IMemorySystem, MemoryItem

class MemorySystem(IMemorySystem):
    """Implementation of the memory system."""

    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.short_term_cache_prefix = "st_memory:"
        self.core_memory_cache_prefix = "core_memory:"

    async def add_to_short_term(
        self, 
        content: Dict[str, Any], 
        source: str, 
        tags: List[str] = None
    ) -> MemoryItem:
        """Add item to short-term memory."""
        memory_item = MemoryItem(
            id=uuid.uuid4(),
            content=content,
            source=source,
            timestamp=datetime.utcnow(),
            memory_type="short_term",
            confidence=0.0,
            validation_count=0,
            tags=tags or [],
            metadata={}
        )
        
        # Store in Redis with TTL
        await self.cache.set(
            f"{self.short_term_cache_prefix}{memory_item.id}",
            memory_item.__dict__,
            ttl=86400  # 24 hours TTL for short-term memory
        )
        return memory_item

    async def move_to_core(self, memory_item: MemoryItem) -> bool:
        """Move item from short-term to core memory."""
        try:
            # Update memory type
            memory_item.memory_type = "core"
            
            # Remove from short-term
            await self.cache.delete(f"{self.short_term_cache_prefix}{memory_item.id}")
            
            # Add to core memory (no TTL)
            await self.cache.set(
                f"{self.core_memory_cache_prefix}{memory_item.id}",
                memory_item.__dict__
            )
            return True
        except Exception as e:
            # Log error and return False
            print(f"Error moving memory to core: {e}")
            return False

    async def retrieve_memory(
        self, 
        query: Dict[str, Any],
        memory_type: str = "all",
        limit: int = 10
    ) -> List[MemoryItem]:
        """Retrieve memories matching the query."""
        memories = []
        
        # Determine which cache prefixes to search based on memory_type
        prefixes = []
        if memory_type in ["all", "short_term"]:
            prefixes.append(self.short_term_cache_prefix)
        if memory_type in ["all", "core"]:
            prefixes.append(self.core_memory_cache_prefix)
        
        # Search through all relevant memory items
        for prefix in prefixes:
            # Get all keys with this prefix
            keys = await self.cache.scan(f"{prefix}*")
            for key in keys:
                # Get memory item data
                memory_data = await self.cache.get(key)
                if memory_data:
                    # Check if memory matches query
                    if self._matches_query(memory_data, query):
                        memories.append(MemoryItem(**memory_data))
                        if len(memories) >= limit:
                            break
            if len(memories) >= limit:
                break
                
        return memories[:limit]

    def _matches_query(self, memory_data: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if memory data matches the query criteria."""
        for key, value in query.items():
            if key not in memory_data:
                return False
            if isinstance(value, list):
                # For lists (like tags), check for any overlap
                if not any(v in memory_data[key] for v in value):
                    return False
            elif memory_data[key] != value:
                return False
        return True
