"""
Portfolio, Position, and Transaction database models.
"""

import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin

class TransactionType(enum.Enum):
    """Enum for transaction types (BUY or SELL)."""
    BUY = "BUY"
    SELL = "SELL"

class Portfolio(Base, TimestampMixin, UUIDMixin):
    """Portfolio model representing a user's collection of stock positions."""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, index=True, nullable=False, default="Default Portfolio")
    description = Column(String, nullable=True)
    currency = Column(String, nullable=False, default="USD") # Default currency

    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}', user_id={self.user_id})>"

class Position(Base, TimestampMixin, UUIDMixin):
    """Position model representing a holding of a specific stock in a portfolio."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True) # Link to Stock model
    
    quantity = Column(Float, nullable=False, default=0.0)
    average_price = Column(Float, nullable=False, default=0.0) # Average cost basis

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    stock = relationship("Stock") # Add back_populates in Stock model if needed
    transactions = relationship("Transaction", back_populates="position", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Position(id={self.id}, stock_id={self.stock_id}, quantity={self.quantity}, portfolio_id={self.portfolio_id})>"

class Transaction(Base, TimestampMixin, UUIDMixin):
    """Transaction model representing a buy or sell action for a stock position."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True, index=True) # Can be null if it's a cash transaction or pre-position
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True) # Link to Stock model

    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False) # Price per share at the time of transaction
    transaction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fees = Column(Float, nullable=True, default=0.0) # Optional transaction fees
    notes = Column(String, nullable=True) # Optional notes for the transaction

    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    position = relationship("Position", back_populates="transactions")
    stock = relationship("Stock") # Add back_populates in Stock model if needed

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.transaction_type.value}', stock_id={self.stock_id}, quantity={self.quantity})>"
