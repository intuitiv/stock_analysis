from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.portfolio_service import PortfolioService
from app.services.market_data_service import MarketDataService # For PortfolioService dependency
from app.schemas import portfolio_schemas as schemas # Alias for clarity
from app.core.security import get_current_active_user
from app.models.user import User as UserModel

router = APIRouter()

# Dependency for PortfolioService
from app.core.dependencies import get_portfolio_service, get_market_data_service


# --- Portfolio Endpoints ---
@router.post("/", response_model=schemas.PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_new_portfolio(
    portfolio_in: schemas.PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    return await portfolio_service.create_portfolio(db=db, portfolio_in=portfolio_in, user_id=current_user.id)

@router.get("/", response_model=List[schemas.PortfolioResponse])
async def read_user_portfolios(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    return await portfolio_service.get_user_portfolios(db=db, user_id=current_user.id)

@router.get("/{portfolio_id}", response_model=schemas.PortfolioWithValueResponse) # Use detailed response
async def read_portfolio_details(
    portfolio_id: int = Path(..., description="The ID of the portfolio to retrieve"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    # Note: PortfolioService.__init__ needs MarketDataService.
    # The get_portfolio_service factory in main.py should handle this.
    # If PortfolioService is directly instantiated here, ensure MDS is passed.
    portfolio = await portfolio_service.get_portfolio_with_details(db=db, portfolio_id=portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return portfolio

@router.put("/{portfolio_id}", response_model=schemas.PortfolioResponse)
async def update_existing_portfolio(
    portfolio_id: int,
    portfolio_in: schemas.PortfolioUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    updated_portfolio = await portfolio_service.update_portfolio(db=db, portfolio_id=portfolio_id, portfolio_in=portfolio_in, user_id=current_user.id)
    if not updated_portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return updated_portfolio

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    success = await portfolio_service.delete_portfolio(db=db, portfolio_id=portfolio_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return None # FastAPI will return 204 No Content

# --- Portfolio Position Endpoints ---
@router.post("/{portfolio_id}/positions", response_model=schemas.PositionResponse, status_code=status.HTTP_201_CREATED) # Changed PortfolioPositionResponse to PositionResponse
async def add_new_position(
    portfolio_id: int,
    position_in: schemas.PositionCreate, # Changed PortfolioPositionCreate to PositionCreate
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    # The position_in object (type PositionCreate) already contains all necessary fields.
    # portfolio_id is passed as a separate argument to the service.
    return await portfolio_service.add_position_to_portfolio(db=db, portfolio_id=portfolio_id, position_in=position_in, user_id=current_user.id)

@router.put("/positions/{position_id}", response_model=schemas.PositionResponse) # Changed PortfolioPositionResponse to PositionResponse
async def update_existing_position(
    position_id: int,
    position_in: schemas.PositionUpdate, # Changed PortfolioPositionUpdate to PositionUpdate
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    updated_position = await portfolio_service.update_portfolio_position(db=db, position_id=position_id, position_in=position_in, user_id=current_user.id)
    if not updated_position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found or access denied")
    return updated_position

@router.delete("/positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_existing_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    success = await portfolio_service.remove_position_from_portfolio(db=db, position_id=position_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found or access denied")
    return None

# --- Transaction Endpoints ---
@router.post("/{portfolio_id}/transactions", response_model=schemas.TransactionResponse, status_code=status.HTTP_201_CREATED)
async def record_new_transaction(
    portfolio_id: int,
    transaction_in: schemas.TransactionCreate, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    # portfolio_id from path is used by the service method
    return await portfolio_service.record_transaction(db=db, portfolio_id=portfolio_id, transaction_in=transaction_in, user_id=current_user.id)

@router.get("/{portfolio_id}/transactions", response_model=List[schemas.TransactionResponse])
async def list_portfolio_transactions(
    portfolio_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service) 
):
    return await portfolio_service.get_portfolio_transactions(db=db, portfolio_id=portfolio_id, user_id=current_user.id, skip=skip, limit=limit)

# TODO: Endpoints for specific transaction GET, PUT, DELETE if needed.
