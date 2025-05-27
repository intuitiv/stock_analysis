"""Core interfaces for CHAETRA components."""
from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Intent:
    primary_goal: str
    sub_goals: List[str]
    required_context: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    response_type: Optional[str] = None

@dataclass
class MemoryItem:
    id: str
    content: Dict[str, Any]
    relevance: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Pattern:
    pattern_type: str
    data: Dict[str, Any]
    confidence: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Evidence:
    source: str
    data: Any
    confidence: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Opinion:
    subject: str
    summary: str
    confidence: float
    evidence: List[Evidence]
    metadata: Optional[Dict[str, Any]] = None

class IMemorySystem(Protocol):
    async def store_memory(self, item: Dict[str, Any]) -> str:
        """Store a new memory item."""
        ...

    async def retrieve_memory(
        self, 
        query: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[MemoryItem]:
        """Retrieve relevant memories based on query."""
        ...

class ILearningSystem(Protocol):
    async def learn_from_interaction(self, interaction_data: Dict[str, Any]) -> None:
        """Learn from an interaction."""
        ...

    async def get_learned_patterns(self) -> List[Pattern]:
        """Get learned patterns."""
        ...

class IReasoningSystem(Protocol):
    async def analyze(
        self,
        query: str,
        intent: Intent,
        memories: List[MemoryItem],
        available_tools: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze a query with context."""
        ...

class IOpinionSystem(Protocol):
    async def form_opinion(
        self,
        subject: str,
        reasoning_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Opinion]:
        """Form an opinion based on analysis."""
        ...

class ILLMProvider(Protocol):
    async def generate_structured_output(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured output following a schema."""
        ...

    async def get_completion(
        self,
        prompt: str,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """Get a completion for a prompt."""
        ...
