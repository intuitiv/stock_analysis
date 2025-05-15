"""
Pydantic schemas for portfolio-related operations.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator, condecimal
from datetime import datetime
from enum import Enum
from decimal import Decimal # Ensure Decimal is imported

class TransactionType(str, Enum):
    """Transaction type enumeration."""
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND" # Added Dividend
    DEPOSIT = "DEPOSIT"   # Added Deposit
    WITHDRAWAL = "WITHDRAWAL" # Added Withdrawal
    FEE = "FEE" # Added Fee

# Base schemas
class PortfolioBase(BaseModel):
    """Base schema for portfolio data."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    currency: str = Field("USD", max_length=3)

class PositionBase(BaseModel):
    """Base schema for position data."""
    stock_symbol: str # Changed from stock_id to stock_symbol for creation/base
    # portfolio_id: int # portfolio_id is usually implicit or path param
    quantity: condecimal(ge=Decimal('0.0')) = Field(..., description="Number of shares")
    average_buy_price: condecimal(ge=Decimal('0.0')) = Field(..., description="Average cost basis per share")


class TransactionBase(BaseModel):
    """Base schema for transaction data."""
    # portfolio_id: int # Usually a path parameter
    stock_symbol: Optional[str] = None # Optional for cash transactions
    transaction_type: TransactionType
    quantity: Optional[condecimal(gt=Decimal('0.0'))] = Field(None, description="Number of shares, required for BUY/SELL")
    price_per_unit: Optional[condecimal(gt=Decimal('0.0'))] = Field(None, description="Price per share, required for BUY/SELL")
    total_amount: Optional[condecimal(gt=Decimal('0.0'))] = Field(None, description="Total amount for DIVIDEND/DEPOSIT/WITHDRAWAL/FEE")
    fees: condecimal(ge=Decimal('0.0')) = Field(Decimal('0.0'), description="Transaction fees")
    notes: Optional[str] = None
    transaction_date: datetime = Field(default_factory=datetime.utcnow)


# Create schemas (for creating new records)
class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio."""
    pass

class PositionCreate(PositionBase): # Used by PortfolioService.add_position_to_portfolio
    """Schema for creating a new position."""
    # average_buy_price is required here as it's the initial buy
    pass


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    pass

# Update schemas (for updating existing records)
class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    # is_active: Optional[bool] = None # Active status usually not updated directly by user

class PositionUpdate(BaseModel): # Used by PortfolioService.update_portfolio_position
    """Schema for updating a position (typically via transactions, but direct update might be allowed)."""
    quantity: Optional[condecimal(ge=Decimal('0.0'))] = None
    average_buy_price: Optional[condecimal(ge=Decimal('0.0'))] = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    quantity: Optional[condecimal(gt=Decimal('0.0'))] = None
    price_per_unit: Optional[condecimal(gt=Decimal('0.0'))] = None
    total_amount: Optional[condecimal(gt=Decimal('0.0'))] = None
    fees: Optional[condecimal(ge=Decimal('0.0'))] = None
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None


# Response schemas (for API responses)
class StockSimpleResponse(BaseModel): # For embedding stock info in PositionResponse
    id: int
    symbol: str
    company_name: Optional[str] = None
    class Config:
        from_attributes = True

class PositionResponse(PositionBase): # Renamed from PositionBase to PositionResponse
    """Schema for position responses."""
    id: int
    # uuid: str # Assuming uuid is in DB model but not always exposed
    stock: StockSimpleResponse # Embed simple stock info
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Calculated fields for detailed view
    current_price: Optional[condecimal(ge=Decimal('0.0'))] = None
    current_value: Optional[condecimal(ge=Decimal('0.0'))] = None
    total_cost: Optional[condecimal(ge=Decimal('0.0'))] = None
    gain_loss: Optional[condecimal(ge=Decimal('0.0'))] = None # Can be negative
    gain_loss_percentage: Optional[condecimal(ge=Decimal('0.0'))] = None # Can be negative

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True # For Decimal

class PortfolioResponse(PortfolioBase):
    """Schema for portfolio responses."""
    id: int
    user_id: int
    # uuid: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    # is_active: bool = True # Active status might be implicit

    class Config:
        from_attributes = True

class TransactionResponse(TransactionBase):
    """Schema for transaction responses."""
    id: int
    # position_id: Optional[int] # Position is linked via stock_id and portfolio_id
    # uuid: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    stock_symbol: Optional[str] = None # Include symbol for clarity

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True # For Decimal

# Schema for portfolio with detailed positions and calculated values
class PortfolioWithValueResponse(PortfolioResponse):
    positions: List[PositionResponse] = [] # Use the detailed PositionResponse
    total_portfolio_value: Optional[condecimal(ge=Decimal('0.0'))] = None
    total_portfolio_cost: Optional[condecimal(ge=Decimal('0.0'))] = None
    total_portfolio_gain_loss: Optional[condecimal(ge=Decimal('0.0'))] = None # Can be negative
    overall_gain_loss_percentage: Optional[condecimal(ge=Decimal('0.0'))] = None # Can be negative

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True # For Decimal


# List schemas (for listing multiple items)
class PortfolioList(BaseModel):
    """Schema for list of portfolios."""
    items: List[PortfolioResponse]
    total: int

class PositionList(BaseModel):
    """Schema for list of positions."""
    items: List[PositionResponse]
    total: int

class TransactionList(BaseModel):
    """Schema for list of transactions."""
    items: List[TransactionResponse]
    total: int

# Summary schemas (for aggregated data) - These might be deprecated if PortfolioWithValueResponse covers it
# class PortfolioSummary(BaseModel):
#     """Schema for portfolio summary data."""
#     total_value: Decimal
#     total_cost: Decimal
#     total_gain_loss: Decimal
#     gain_loss_percentage: Decimal
#     positions_count: int
#     last_updated: datetime

# class PositionSummary(BaseModel):
#     """Schema for position summary data."""
#     current_value: Decimal
#     total_cost: Decimal
#     gain_loss: Decimal
#     gain_loss_percentage: Decimal
#     last_updated: datetime
