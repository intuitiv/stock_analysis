"""Portfolio-related schema definitions."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator

class PortfolioBase(BaseModel):
    """Base portfolio schema."""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_active: bool = True
    user_id: int

class PortfolioCreate(PortfolioBase):
    """Create portfolio schema."""
    pass

class PortfolioUpdate(BaseModel):
    """Update portfolio schema."""
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class Portfolio(PortfolioBase):
    """Portfolio response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    total_value: Decimal = Field(default=Decimal('0.00'))
    total_profit_loss: Decimal = Field(default=Decimal('0.00'))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v)
        }

class PortfolioResponse(Portfolio):
    """Comprehensive portfolio response schema."""
    positions: List['Position'] = []
    transactions: List['Transaction'] = []

    class Config:
        """Pydantic config."""
        from_attributes = True

class PositionBase(BaseModel):
    """Base position schema."""
    portfolio_id: int
    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: Decimal = Field(..., gt=0)
    entry_price: Decimal = Field(..., gt=0)
    target_price: Optional[Decimal] = Field(None, gt=0)
    stop_loss: Optional[Decimal] = Field(None, gt=0)
    notes: Optional[str] = None

class PositionCreate(PositionBase):
    """Create position schema."""
    pass

class PositionUpdate(BaseModel):
    """Update position schema."""
    quantity: Optional[Decimal] = Field(None, gt=0)
    target_price: Optional[Decimal] = Field(None, gt=0)
    stop_loss: Optional[Decimal] = Field(None, gt=0)
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Position(PositionBase):
    """Position response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    current_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    profit_loss: Optional[Decimal] = None
    profit_loss_percentage: Optional[Decimal] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v)
        }

    @validator('profit_loss_percentage')
    def round_percentage(cls, v):
        """Round percentage to 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v

class TransactionCreate(BaseModel):
    """Create transaction schema."""
    portfolio_id: int
    symbol: str = Field(..., min_length=1, max_length=10)
    transaction_type: str = Field(..., pattern='^(buy|sell)$')
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    fees: Optional[Decimal] = Field(default=Decimal('0.00'), ge=0)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Transaction(TransactionCreate):
    """Transaction response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    total_value: Decimal

    class Config:
        """Pydantic config."""
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v)
        }

class WatchlistItemBase(BaseModel):
    """Base watchlist item schema."""
    user_id: int
    symbol: str = Field(..., min_length=1, max_length=10)
    notes: Optional[str] = None
    alert_price: Optional[Decimal] = Field(None, gt=0)

class WatchlistItemCreate(WatchlistItemBase):
    """Create watchlist item schema."""
    pass

class WatchlistItem(WatchlistItemBase):
    """Watchlist item response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    current_price: Optional[Decimal] = None
    price_change: Optional[Decimal] = None
    price_change_percentage: Optional[Decimal] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v)
        }

    @validator('price_change_percentage')
    def round_percentage(cls, v):
        """Round percentage to 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v

__all__ = [
    'PortfolioBase',
    'PortfolioCreate',
    'PortfolioUpdate',
    'Portfolio',
    'PortfolioResponse',
    'PositionBase',
    'PositionCreate',
    'PositionUpdate',
    'Position',
    'TransactionCreate',
    'Transaction',
    'WatchlistItemBase',
    'WatchlistItemCreate',
    'WatchlistItem'
]
