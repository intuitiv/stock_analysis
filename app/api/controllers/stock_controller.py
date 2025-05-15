from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.services.market_data_service import MarketDataService
from app.core.config import settings
# from app.core.security import get_current_active_user # If endpoints need auth
# from app.models.user import User # If using user context

router = APIRouter()

# Dependency for MarketDataService
from app.core.dependencies import get_market_data_service

@router.get("/{symbol}/profile", summary="Get company profile for a stock symbol")
async def get_stock_profile_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    provider: Optional[str] = Query(None, description="Specific market data provider to use"),
    market_service: MarketDataService = Depends(get_market_data_service)
) -> Dict[str, Any]:
    """
    Retrieves company profile information for the given stock symbol.
    """
    try:
        profile = await market_service.get_company_profile(symbol.upper(), provider_name=provider)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile not found for symbol: {symbol}")
        return profile
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile for {symbol}: {str(e)}")

@router.get("/{symbol}/quote", summary="Get current quote for a stock symbol")
async def get_stock_quote_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    provider: Optional[str] = Query(None, description="Specific market data provider to use"),
    market_service: MarketDataService = Depends(get_market_data_service)
) -> Dict[str, Any]:
    """
    Retrieves the latest quote for the given stock symbol.
    """
    try:
        quote = await market_service.get_current_quote(symbol.upper(), provider_name=provider)
        if not quote:
            raise HTTPException(status_code=404, detail=f"Quote not found for symbol: {symbol}")
        return quote
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quote for {symbol}: {str(e)}")

@router.get("/{symbol}/historical", summary="Get historical price data for a stock symbol")
async def get_historical_data_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    start_date_str: Optional[str] = Query(None, description="Start date (YYYY-MM-DD). Defaults to 1 year ago."),
    end_date_str: Optional[str] = Query(None, description="End date (YYYY-MM-DD). Defaults to today."),
    interval: str = Query("1d", description="Data interval (e.g., '1m', '5m', '1h', '1d', '1wk', '1mo')"),
    provider: Optional[str] = Query(None, description="Specific market data provider to use"),
    market_service: MarketDataService = Depends(get_market_data_service)
) -> List[Dict[str, Any]]:
    """
    Retrieves historical OHLCV data for the given stock symbol.
    """
    try:
        end_date = datetime.utcnow() if not end_date_str else datetime.strptime(end_date_str, "%Y-%m-%d")
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = end_date - timedelta(days=settings.DEFAULT_HISTORICAL_DATA_PERIOD_DAYS) # e.g., 365
        
        # Ensure start_date is not after end_date
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date cannot be after end date.")

        data = await market_service.get_price_data(symbol.upper(), start_date, end_date, interval, provider_name=provider)
        if not data:
            # Return 204 or empty list if no data found, rather than 404, as the symbol might be valid but have no data in range
            return [] 
        return data
    except ValueError as ve: # Handles date parsing errors or invalid provider
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data for {symbol}: {str(e)}")

@router.get("/{symbol}/financials/{statement_type}", summary="Get financial statements for a stock symbol")
async def get_financial_statements_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    statement_type: str = Path(..., description="Type of financial statement ('income_statement', 'balance_sheet', 'cash_flow')"),
    period: str = Query("annual", description="Period type ('annual' or 'quarterly')"),
    limit: int = Query(5, ge=1, le=20, description="Number of past periods to retrieve"),
    provider: Optional[str] = Query(None, description="Specific market data provider to use"),
    market_service: MarketDataService = Depends(get_market_data_service)
) -> List[Dict[str, Any]]:
    """
    Retrieves financial statements for the given stock symbol.
    """
    valid_statement_types = ["income_statement", "balance_sheet", "cash_flow"]
    if statement_type.lower() not in valid_statement_types:
        raise HTTPException(status_code=400, detail=f"Invalid statement type. Choose from: {', '.join(valid_statement_types)}")
    if period.lower() not in ["annual", "quarterly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Choose 'annual' or 'quarterly'.")

    try:
        statements = await market_service.get_financial_statements(
            symbol.upper(), statement_type.lower(), period.lower(), limit, provider_name=provider
        )
        if not statements:
            return [] # No data found for the criteria
        return statements
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching financial statements for {symbol}: {str(e)}")

@router.get("/{symbol}/ratios", summary="Get key financial ratios for a stock symbol")
async def get_key_ratios_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    provider: Optional[str] = Query(None, description="Specific market data provider to use"),
    market_service: MarketDataService = Depends(get_market_data_service)
) -> Dict[str, Any]:
    """
    Retrieves key financial ratios for the given stock symbol.
    """
    try:
        ratios = await market_service.get_key_financial_ratios(symbol.upper(), provider_name=provider)
        if not ratios:
            raise HTTPException(status_code=404, detail=f"Key financial ratios not found for symbol: {symbol}")
        return ratios
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching key ratios for {symbol}: {str(e)}")

# Note: News endpoint is in market_controller.py but can also be adapted here if needed for /stocks/{symbol}/news
