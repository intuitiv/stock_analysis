"""Interfaces for CHAETRA components."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class ChaetraResponse:
    """Data class for standardized Chaetra response."""
    response: str
    trace_id: str
    thoughts: List[str]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class MemoryItem:
    """Data class for memory items."""
    id: UUID
    content: Dict[str, Any]
    source: str
    timestamp: datetime
    memory_type: str = "short_term"  # "short_term" or "core"
    confidence: float = 0.0
    validation_count: int = 0
    tags: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class Pattern:
    """Data class for recognized patterns."""
    name: str
    description: str
    confidence: float
    occurrences: List[Dict[str, Any]]
    validation_count: int = 0
    last_observed: datetime = None
    metadata: Dict[str, Any] = None

@dataclass
class Opinion:
    """Data class for formed opinions."""
    id: UUID
    topic: str
    belief: str
    confidence: float
    evidence: List[Dict[str, Any]]
    formed_at: datetime
    last_updated: datetime = None
    validation_count: int = 0
    metadata: Dict[str, Any] = None

class ILLMProvider(ABC):
    """Interface for LLM providers."""
    
    @abstractmethod
    def __init__(
        self,
        provider_name: str,
        model_name: Optional[str],
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        pass

    @abstractmethod
    async def generate_text(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        schema: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate text from the LLM."""
        pass

class IMemorySystem(ABC):
    """Interface for memory system."""
    
    @abstractmethod
    async def add_to_short_term(
        self,
        user_id: str,
        content: Dict[str, Any],
        source: str,
        tags: List[str] = None,
        expires_at: Optional[datetime] = None
    ) -> MemoryItem:
        """Add item to short-term memory with user context."""
        pass

    @abstractmethod
    async def move_to_core(
        self,
        user_id: str,
        memory_item: MemoryItem
    ) -> bool:
        """Move item from short-term to core memory."""
        pass

    @abstractmethod
    async def retrieve_memory(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        filter_query: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryItem]:
        """
        Retrieve memories for a specific user.
        
        Args:
            user_id: User identifier for scoping memories
            memory_type: Optional type filter ('fact', 'opinion', etc)
            filter_query: Optional text filter for searching memories
            limit: Maximum number of memories to return
        """
        pass

    @abstractmethod
    async def bulk_edit_memories(
        self,
        user_id: str,
        edits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform bulk edits on memories.
        
        Args:
            user_id: User identifier for scoping edits
            edits: List of edit operations (add/update/delete)
        
        Returns:
            Dictionary containing success/failure information
        """
        pass

class ILearningSystem(ABC):
    """Interface for learning system."""
    
    @abstractmethod
    async def identify_patterns(self, data: Dict[str, Any]) -> List[Pattern]:
        """Identify patterns in the data."""
        pass

    @abstractmethod
    async def validate_pattern(self, pattern: Pattern, new_data: Dict[str, Any]) -> bool:
        """Validate a pattern against new data."""
        pass

class IReasoningSystem(ABC):
    """Interface for reasoning system."""
    
    @abstractmethod
    async def analyze_data(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any],
        query_intent: Dict[str, Any],
        trace_id: str,
        thoughts: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze data and generate insights.
        
        Args:
            data: Data to analyze
            context: Context including user_id and other metadata
            query_intent: Structured query intent
            trace_id: Unique trace identifier for request tracking
            thoughts: List to collect reasoning thoughts
            
        Returns:
            Dictionary containing analysis results and thoughts
        """
        pass

class IOpinionSystem(ABC):
    """Interface for opinion system."""
    
    @abstractmethod
    async def form_opinion(
        self,
        user_id: str,
        topic: str,
        analysis_result: Dict[str, Any],
        context: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> Opinion:
        """
        Form an opinion about a topic based on analysis.
        
        Args:
            user_id: User identifier for opinion ownership
            topic: Topic of the opinion
            analysis_result: Analysis data to base opinion on
            context: Additional context for opinion formation
            trace_id: Optional trace identifier for request tracking
        """
        pass

    @abstractmethod
    async def update_opinion(
        self,
        user_id: str,
        opinion_id: UUID,
        new_evidence: List[Dict[str, Any]],
        trace_id: Optional[str] = None
    ) -> Opinion:
        """
        Update an existing opinion with new evidence.
        
        Args:
            user_id: User identifier for opinion ownership
            opinion_id: Unique identifier of the opinion
            new_evidence: New evidence to incorporate
            trace_id: Optional trace identifier for request tracking
        """
        pass

    @abstractmethod
    async def get_opinions(
        self,
        user_id: str,
        filter_query: Optional[str] = None,
        limit: int = 10
    ) -> List[Opinion]:
        """
        Retrieve opinions for a user with optional filtering.
        
        Args:
            user_id: User identifier to scope opinions
            filter_query: Optional text query to filter opinions
            limit: Maximum number of opinions to return
        """
        pass
