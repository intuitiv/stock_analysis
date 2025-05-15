"""
CHAETRA: Cognitive Hybrid Analysis Engine for Trading Research & Assessment

This package implements CHAETRA's core components:
- Memory System (short and long-term market knowledge)
- Learning System (pattern detection and validation)
- Reasoning System (analysis and decision making)
- Opinion Formation (market insights and recommendations)
"""

__version__ = "0.1.0"

from .brain import CHAETRA as Brain
from .interfaces import ILearningSystem, IMemorySystem, IReasoningSystem, Pattern, MemoryItem, Opinion
from .memory import MemorySystem
from .reasoning import ReasoningSystem
from .learning import LearningSystem
from .opinion import OpinionSystem

__all__ = [
    'Brain',
    'ILearningSystem',
    'IMemorySystem', 
    'IReasoningSystem',
    'Pattern',
    'MemoryItem',
    'Opinion',
    'MemorySystem',
    'ReasoningSystem',
    'LearningSystem',
    'OpinionSystem',
]
