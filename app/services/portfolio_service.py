"""Portfolio service for managing user portfolios, positions, and transactions."""
from typing import List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException, status
from datetime import datetime

from app.models.user import User as UserModel
from app.models.stock import Stock as StockModel
from app.models.portfolio import Portfolio as PortfolioModel, Position as PositionModel, Transaction as TransactionModel, TransactionType
from app.schemas.portfolio_schemas import PortfolioCreate, PortfolioUpdate, PositionCreate, PositionUpdate, TransactionCreate, PortfolioResponse
from app.services.market_data_service import MarketDataService
from app.core.database import get_db

class PortfolioService:
    """Service for managing user portfolios"""

    def __init__(self, session_factory: Callable[[], Session], market_data_service: Optional[MarketDataService] = None):
        """Initialize portfolio service with session factory and optional market data service."""
        self.session_factory = session_factory
        self.market_data_service = market_data_service

    def get_db(self) -> Session:
        """Get database session from factory"""
        return self.session_factory()

    async def create_portfolio(self, portfolio_in: PortfolioCreate, user_id: int) -> PortfolioModel:
        """Create a new portfolio for a user"""
        db = self.get_db()
        try:
            db_portfolio = PortfolioModel(**portfolio_in.dict(), user_id=user_id)
            db.add(db_portfolio)
            db.commit()
            db.refresh(db_portfolio)
            return db_portfolio
        finally:
            db.close()

    async def get_portfolio_by_id(self, portfolio_id: int, user_id: int) -> Optional[PortfolioModel]:
        """Get a portfolio by ID, ensuring it belongs to the user"""
        db = self.get_db()
        try:
            return db.query(PortfolioModel).filter(
                PortfolioModel.id == portfolio_id,
                PortfolioModel.user_id == user_id
            ).first()
        finally:
            db.close()

    async def get_user_portfolios(self, user_id: int) -> List[PortfolioModel]:
        """Get all portfolios belonging to a user"""
        db = self.get_db()
        try:
            return db.query(PortfolioModel).filter(PortfolioModel.user_id == user_id).all()
        finally:
            db.close()

    async def update_portfolio(self, portfolio_id: int, portfolio_in: PortfolioUpdate, user_id: int) -> Optional[PortfolioModel]:
        """Update a portfolio's details"""
        db = self.get_db()
        try:
            db_portfolio = await self.get_portfolio_by_id(portfolio_id, user_id)
            if not db_portfolio:
                return None
            
            update_data = portfolio_in.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_portfolio, key, value)
            
            db_portfolio.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_portfolio)
            return db_portfolio
        finally:
            db.close()

    async def delete_portfolio(self, portfolio_id: int, user_id: int) -> bool:
        """Delete a portfolio and all associated positions/transactions"""
        db = self.get_db()
        try:
            db_portfolio = await self.get_portfolio_by_id(portfolio_id, user_id)
            if not db_portfolio:
                return False
            db.delete(db_portfolio)
            db.commit()
            return True
        finally:
            db.close()

    async def add_position_to_portfolio(self, portfolio_id: int, position_in: PositionCreate, user_id: int) -> Optional[PositionModel]:
        """Add a new position to a portfolio"""
        db = self.get_db()
        try:
            portfolio = await self.get_portfolio_by_id(portfolio_id, user_id)
            if not portfolio:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Portfolio not found or access denied"
                )

            stock = db.query(StockModel).filter(StockModel.symbol == position_in.stock_symbol.upper()).first()
            if not stock:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Stock symbol {position_in.stock_symbol} not found"
                )

            existing_position = db.query(PositionModel).filter(
                PositionModel.portfolio_id == portfolio_id,
                PositionModel.stock_id == stock.id
            ).first()

            if existing_position:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Position for {stock.symbol} already exists in this portfolio. Use transactions to update."
                )

            db_position = PositionModel(
                portfolio_id=portfolio_id,
                stock_id=stock.id,
                quantity=position_in.quantity,
                average_buy_price=position_in.average_buy_price
            )
            db.add(db_position)
            db.commit()
            db.refresh(db_position)
            return db_position
        finally:
            db.close()

    # Rest of the methods follow the same pattern: get db session, try operation, finally close session
    # Implementation of other methods remains largely the same, just wrapped in session management

    async def close(self) -> None:
        """Close any open resources"""
        # No long-lived resources to close in this service
        pass
