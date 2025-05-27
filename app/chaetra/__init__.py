"""
CHAETRA - Cognitive Hybrid Analytical Engine for Trading and Research Analysis

Core ML and AI components of the NAETRA platform.
"""
from typing import TYPE_CHECKING

# Import only what's needed for type hints
if TYPE_CHECKING:
    from .brain import CHAETRA as Brain
    from .learning import LearningSystem
    from .memory import MemorySystem
    from .reasoning import ReasoningSystem
    from .opinion import OpinionSystem
    from .llm import LLMManager

def get_brain():
    """Get CHAETRA Brain instance (lazy import)"""
    from .brain import CHAETRA
    return CHAETRA

def get_learning_system():
    """Get Learning System instance (lazy import)"""
    from .learning import LearningSystem
    return LearningSystem

def get_memory_system():
    """Get Memory System instance (lazy import)"""
    from .memory import MemorySystem
    return MemorySystem

def get_reasoning_system():
    """Get Reasoning System instance (lazy import)"""
    from .reasoning import ReasoningSystem
    return ReasoningSystem

def get_opinion_system():
    """Get Opinion System instance (lazy import)"""
    from .opinion import OpinionSystem
    return OpinionSystem

def get_llm_manager():
    """Get LLM Manager instance (lazy import)"""
    from .llm import LLMManager
    return LLMManager

__all__ = [
    'get_brain',
    'get_learning_system',
    'get_memory_system',
    'get_reasoning_system',
    'get_opinion_system',
    'get_llm_manager',
]
