from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException, status
from datetime import datetime

from app.models.user import User as UserModel
from app.models.stock import Stock as StockModel
from app.models.portfolio import Portfolio as PortfolioModel, Position as PositionModel, Transaction as TransactionModel, TransactionType # Changed PortfolioPosition to Position
from app.schemas.portfolio_schemas import PortfolioCreate, PortfolioUpdate, PositionCreate, PositionUpdate, TransactionCreate, PortfolioResponse # PortfolioWithValueResponse is not defined yet
from app.services.market_data_service import MarketDataService
from app.core.database import get_db # Assuming get_db for session dependency

class PortfolioService:
    # def __init__(self, db: Session = Depends(get_db), market_data_service: MarketDataService = Depends(MarketDataService)):
    #     self.db = db
    #     self.market_data_service = market_data_service
    # The above __init__ is for when PortfolioService itself is a FastAPI dependency.
    # If methods are called with db session passed in, then __init__ might just take market_data_service.

    def __init__(self, market_data_service: MarketDataService): # Simpler init for now
        self.market_data_service = market_data_service

    async def create_portfolio(self, db: Session, portfolio_in: PortfolioCreate, user_id: int) -> PortfolioModel:
        db_portfolio = PortfolioModel(**portfolio_in.dict(), user_id=user_id)
        db.add(db_portfolio)
        db.commit()
        db.refresh(db_portfolio)
        return db_portfolio

    async def get_portfolio_by_id(self, db: Session, portfolio_id: int, user_id: int) -> Optional[PortfolioModel]:
        return db.query(PortfolioModel).filter(PortfolioModel.id == portfolio_id, PortfolioModel.user_id == user_id).first()

    async def get_user_portfolios(self, db: Session, user_id: int) -> List[PortfolioModel]:
        return db.query(PortfolioModel).filter(PortfolioModel.user_id == user_id).all()

    async def update_portfolio(self, db: Session, portfolio_id: int, portfolio_in: PortfolioUpdate, user_id: int) -> Optional[PortfolioModel]:
        db_portfolio = await self.get_portfolio_by_id(db, portfolio_id, user_id)
        if not db_portfolio:
            return None
        
        update_data = portfolio_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_portfolio, key, value)
        
        db_portfolio.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_portfolio)
        return db_portfolio

    async def delete_portfolio(self, db: Session, portfolio_id: int, user_id: int) -> bool:
        db_portfolio = await self.get_portfolio_by_id(db, portfolio_id, user_id)
        if not db_portfolio:
            return False
        db.delete(db_portfolio) # Assumes cascade delete for positions and transactions is set up in models
        db.commit()
        return True

    async def add_position_to_portfolio(self, db: Session, portfolio_id: int, position_in: PositionCreate, user_id: int) -> Optional[PositionModel]: # Changed PortfolioPositionCreate to PositionCreate
        portfolio = await self.get_portfolio_by_id(db, portfolio_id, user_id)
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found or access denied")

        stock = db.query(StockModel).filter(StockModel.symbol == position_in.stock_symbol.upper()).first()
        if not stock:
            # Optionally, try to fetch stock info and create it if it doesn't exist
            # stock_profile = await self.market_data_service.get_company_profile(position_in.stock_symbol.upper())
            # if stock_profile and stock_profile.get('symbol'):
            #     stock = StockModel(symbol=stock_profile['symbol'], company_name=stock_profile.get('name'), ...)
            #     db.add(stock); db.commit(); db.refresh(stock)
            # else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock symbol {position_in.stock_symbol} not found")

        # Check if position for this stock already exists
        existing_position = db.query(PositionModel).filter(
            PositionModel.portfolio_id == portfolio_id,
            PositionModel.stock_id == stock.id
        ).first()

        if existing_position:
            # Update existing position (e.g., average down/up) - this logic can be complex
            # For simplicity, let's assume new shares are added and avg price is recalculated
            # This should ideally be driven by a transaction, not direct position creation
            # For now, let's prevent duplicate positions and suggest using transactions or updating.
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Position for {stock.symbol} already exists in this portfolio. Use transactions to update.")

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

    async def update_portfolio_position(self, db: Session, position_id: int, position_in: PositionUpdate, user_id: int) -> Optional[PositionModel]: # Changed PortfolioPositionUpdate to PositionUpdate
        # Ensure the position belongs to one of the user's portfolios
        db_position = db.query(PositionModel).join(PortfolioModel).filter(
            PositionModel.id == position_id,
            PortfolioModel.user_id == user_id
        ).first()

        if not db_position:
            return None
        
        update_data = position_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_position, key, value)
        
        db_position.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_position)
        return db_position

    async def remove_position_from_portfolio(self, db: Session, position_id: int, user_id: int) -> bool:
        db_position = db.query(PositionModel).join(PortfolioModel).filter(
            PositionModel.id == position_id,
            PortfolioModel.user_id == user_id
        ).first()
        
        if not db_position:
            return False
        
        # Consider if there are related transactions that need handling or if quantity must be zero
        if db_position.quantity > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete position with non-zero quantity. Please record sell transactions first.")

        db.delete(db_position)
        db.commit()
        return True

    async def record_transaction(self, db: Session, portfolio_id: int, transaction_in: TransactionCreate, user_id: int) -> Optional[TransactionModel]:
        portfolio = await self.get_portfolio_by_id(db, portfolio_id, user_id)
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found or access denied")

        stock_id: Optional[int] = None
        if transaction_in.stock_symbol:
            stock = db.query(StockModel).filter(StockModel.symbol == transaction_in.stock_symbol.upper()).first()
            if not stock:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock symbol {transaction_in.stock_symbol} not found")
            stock_id = stock.id
        
        # Validate transaction data based on type
        if transaction_in.transaction_type in [TransactionType.BUY, TransactionType.SELL]:
            if not stock_id or transaction_in.quantity is None or transaction_in.price_per_unit is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="BUY/SELL transactions require stock_symbol, quantity, and price_per_unit.")
            transaction_in.total_amount = (transaction_in.quantity * transaction_in.price_per_unit) + (transaction_in.fees or 0)
        elif transaction_in.transaction_type == TransactionType.DIVIDEND:
            if not stock_id or transaction_in.total_amount is None:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="DIVIDEND transactions require stock_symbol and total_amount.")
        elif transaction_in.transaction_type in [TransactionType.DEPOSIT, TransactionType.WITHDRAWAL, TransactionType.FEE]:
            if transaction_in.total_amount is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{transaction_in.transaction_type.value} transactions require total_amount.")


        db_transaction = TransactionModel(
            portfolio_id=portfolio_id,
            stock_id=stock_id,
            **transaction_in.dict(exclude={"stock_symbol"}) # Exclude stock_symbol as we use stock_id
        )
        db.add(db_transaction)
        
        # Update portfolio position based on transaction (simplified)
        if transaction_in.transaction_type == TransactionType.BUY and stock_id:
            position = db.query(PositionModel).filter(PositionModel.portfolio_id == portfolio_id, PositionModel.stock_id == stock_id).first()
            if position:
                new_total_cost = (position.average_buy_price * position.quantity) + (transaction_in.quantity * transaction_in.price_per_unit)
                position.quantity += transaction_in.quantity
                position.average_buy_price = new_total_cost / position.quantity
                position.updated_at = datetime.utcnow()
            else: # Create new position
                new_pos = PositionModel(
                    portfolio_id=portfolio_id, stock_id=stock_id, 
                    quantity=transaction_in.quantity, average_buy_price=transaction_in.price_per_unit
                )
                db.add(new_pos)
        elif transaction_in.transaction_type == TransactionType.SELL and stock_id:
            position = db.query(PositionModel).filter(PositionModel.portfolio_id == portfolio_id, PositionModel.stock_id == stock_id).first()
            if not position or position.quantity < transaction_in.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough shares to sell.")
            position.quantity -= transaction_in.quantity
            position.updated_at = datetime.utcnow()
            if position.quantity == 0:
                # Optionally delete position if quantity is zero, or keep it for history
                # db.delete(position) 
                pass


        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    async def get_portfolio_transactions(self, db: Session, portfolio_id: int, user_id: int, skip: int = 0, limit: int = 100) -> List[TransactionModel]:
        portfolio = await self.get_portfolio_by_id(db, portfolio_id, user_id)
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found or access denied")
        return db.query(TransactionModel).filter(TransactionModel.portfolio_id == portfolio_id).order_by(TransactionModel.transaction_date.desc()).offset(skip).limit(limit).all()

    async def get_portfolio_with_details(self, db: Session, portfolio_id: int, user_id: int) -> Optional[PortfolioModel]: # Changed return type, PortfolioWithValueResponse not defined
        # Use joinedload to eager load positions and their stocks
        portfolio = db.query(PortfolioModel).options(
            joinedload(PortfolioModel.positions).joinedload(PositionModel.stock)
        ).filter(PortfolioModel.id == portfolio_id, PortfolioModel.user_id == user_id).first()

        if not portfolio:
            return None

        # Calculate total portfolio value and other metrics
        total_value = 0.0
        # These would require fetching current prices for all stocks in positions
        # For simplicity, this calculation is omitted here but would be crucial in a real app.
        # Example:
        # for pos in portfolio.positions:
        #     quote = await self.market_data_service.get_current_quote(pos.stock.symbol)
        #     if quote and quote.get('price'):
        #         total_value += pos.quantity * quote['price']
        
        # Convert to Pydantic response model
        # This requires PositionResponse to correctly handle the stock relationship
        # For now, returning the ORM model directly, or use PortfolioResponse
        # return PortfolioWithValueResponse.from_orm(portfolio) # total_value etc. would be None for now
        return portfolio # Or convert to PortfolioResponse if that's sufficient for now
