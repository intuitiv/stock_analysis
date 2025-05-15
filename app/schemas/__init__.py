"""
Module for Pydantic schema definitions.
"""

from .auth_schemas import (
    Token,
    TokenData,
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse
)

from .portfolio_schemas import (
    PortfolioBase,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioList,
    PositionBase,
    PositionCreate,
    PositionUpdate,
    PositionResponse,
    PositionList,
    TransactionBase,
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionList,
    # PortfolioSummary, # Commented out as it's deprecated by PortfolioWithValueResponse
    # PositionSummary,  # Commented out as it's deprecated by PositionResponse with value fields
    TransactionType,
    PortfolioWithValueResponse # Ensure this is exported if used elsewhere directly from schemas package
)

from .chat_schemas import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionList,
    ChatMessageList
)

__all__ = [
    # Auth schemas
    "Token",
    "TokenData",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    
    # Portfolio schemas
    "PortfolioBase",
    "PortfolioCreate",
    "PortfolioUpdate",
    "PortfolioResponse",
    "PortfolioList",
    "PositionBase",
    "PositionCreate",
    "PositionUpdate",
    "PositionResponse",
    "PositionList",
    "TransactionBase",
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionResponse",
    "TransactionList",
    # "PortfolioSummary",
    # "PositionSummary",
    "TransactionType",
    "PortfolioWithValueResponse",

    # Chat schemas
    "ChatSessionCreate",
    "ChatSessionUpdate",
    "ChatSessionResponse",
    "ChatMessageCreate",
    "ChatMessageResponse",
    "ChatSessionList",
    "ChatMessageList"
]
