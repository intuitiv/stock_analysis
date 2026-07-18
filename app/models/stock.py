"""
Stock model for managing stock information.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin

class Stock(Base, TimestampMixin, UUIDMixin):
    """Stock model representing a tradable stock/security."""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, unique=True, nullable=False)
    name = Column(String, index=True)
    exchange = Column(String, index=True)
    currency = Column(String, default="USD")
    
    # Basic stock information
    sector = Column(String, index=True)
    industry = Column(String, index=True)
    market_cap = Column(Float)
    pe_ratio = Column(Float)
    dividend_yield = Column(Float)
    
    # Latest price information
    current_price = Column(Float)
    price_updated_at = Column(DateTime(timezone=True))
    
    # Stock metadata
    is_active = Column(Boolean, default=True)
    description = Column(String)
    website = Column(String)
    country = Column(String)
    
    # Additional data storage (flexible)
    extra_data = Column(JSON)

    # Relationships
    # These will be created by the related models
    positions = relationship("Position", back_populates="stock")
    transactions = relationship("Transaction", back_populates="stock")

    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"

    @property
    def last_price(self) -> float:
        """Get the last known price of the stock."""
        return self.current_price if self.current_price is not None else 0.0

    @property
    def market_value(self) -> float:
        """Calculate total market value based on current price."""
        return self.last_price * self.total_shares if self.last_price else 0.0

    def update_price(self, price: float) -> None:
        """Update the current price and timestamp."""
        self.current_price = price
        self.price_updated_at = func.now()
