"""Models module initialization."""
from typing import TYPE_CHECKING

# Import models
from .user import User
from .portfolio import Portfolio, Position, Transaction, TransactionType
from .stock import Stock
from .analysis import (
    Analysis, AnalysisType, AnalysisStatus,
    AnalysisInput, AnalysisResult, AnalysisRun
)
from .chat import ChatSession, ChatMessage, MessageRole
from .analysis_output import AnalysisOutput

# Handle relationships with type checking
if TYPE_CHECKING:
    from .analysis import Analysis  # noqa

    class User:
        portfolios: list[Portfolio]
        analyses: list[Analysis]
        chat_sessions: list[ChatSession]

    class Portfolio:
        user: User
        positions: list[Position]
        transactions: list[Transaction]

    class Position:
        portfolio: Portfolio
        stock: Stock
        transactions: list[Transaction]

    class Transaction:
        portfolio: Portfolio
        position: Position
        stock: Stock

    class Analysis:
        user: User
        inputs: list[AnalysisInput]
        runs: list[AnalysisRun]
        outputs: list[AnalysisOutput]

    class AnalysisRun:
        analysis: Analysis
        results: list[AnalysisResult]

    class AnalysisResult:
        analysis_run: AnalysisRun

    class AnalysisInput:
        analysis: Analysis

    class ChatSession:
        user: User
        messages: list[ChatMessage]

    class ChatMessage:
        session: ChatSession
        analysis: Analysis
        analysis_result: AnalysisResult

    class AnalysisOutput:
        analysis: Analysis

__all__ = [
    'User',
    'Portfolio',
    'Position',
    'Transaction',
    'TransactionType',
    'Stock',
    'Analysis',
    'AnalysisType',
    'AnalysisStatus',
    'AnalysisInput',
    'AnalysisResult',
    'AnalysisRun',
    'AnalysisOutput',
    'ChatSession',
    'ChatMessage',
    'MessageRole'
]
