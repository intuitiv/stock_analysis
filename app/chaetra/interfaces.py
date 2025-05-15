"""Interfaces for CHAETRA components."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

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
    async def add_to_short_term(self, content: Dict[str, Any], source: str, tags: List[str] = None) -> MemoryItem:
        """Add item to short-term memory."""
        pass

    @abstractmethod
    async def move_to_core(self, memory_item: MemoryItem) -> bool:
        """Move item from short-term to core memory."""
        pass

    @abstractmethod
    async def retrieve_memory(
        self, 
        query: Dict[str, Any],
        memory_type: str = "all",
        limit: int = 10
    ) -> List[MemoryItem]:
        """Retrieve memories matching the query."""
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
        query_intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze data and generate insights."""
        pass

class IOpinionSystem(ABC):
    """Interface for opinion system."""
    
    @abstractmethod
    async def form_opinion(
        self,
        topic: str,
        analysis_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Opinion:
        """Form an opinion about a topic based on analysis."""
        pass

    @abstractmethod
    async def update_opinion(
        self,
        opinion_id: UUID,
        new_evidence: List[Dict[str, Any]]
    ) -> Opinion:
        """Update an existing opinion with new evidence."""
        pass
