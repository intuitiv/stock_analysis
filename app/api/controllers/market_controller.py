import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.services.market_data_service import MarketDataService
# from app.services.analysis_service import AnalysisService # If market overview needs some analysis
from app.core.config import settings
# from app.core.security import get_current_active_user # If endpoints need auth
# from app.models.user import User # If using user context

router = APIRouter()

# Dependency for MarketDataService
# This would typically be initialized once and provided via FastAPI's dependency injection system.
# For simplicity here, we might instantiate it directly or use a global instance if not using Depends properly.
# A better approach is to have a factory or a singleton provider for services.
# Example:
# def get_market_service():
#     # This should return a singleton instance or a new one per request based on design
#     from app.main import market_data_service_instance # Assuming it's created in main
#     return market_data_service_instance
from app.core.dependencies import get_market_data_service


@router.get("/search", summary="Search for stock symbols")
async def search_symbols_endpoint(
    query: str = Query(..., min_length=1, description="Search query for stock symbols"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
    provider: Optional[str] = Query(None, description="Specific market data provider to use (e.g., 'alpha_vantage')"),
    market_service: MarketDataService = Depends(get_market_data_service) 
) -> List[Dict[str, Any]]:
    """
    Search for stock symbols across configured market data providers.
    """
    try:
        results = await market_service.search_symbols(query, limit, provider_name=provider)
        if not results and provider is None: # If default provider failed, try others if any configured
            for p_name in market_service.providers.keys():
                if p_name != market_service.default_provider_name:
                    results = await market_service.search_symbols(query, limit, provider_name=p_name)
                    if results: break
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No symbols found for query: {query}")
        return results
    except ValueError as ve: # Catch errors from _get_provider if invalid provider name
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching symbols: {str(e)}")


@router.get("/overview", summary="Get general market overview")
async def get_market_overview_endpoint(
    market_service: MarketDataService = Depends(get_market_data_service)
    # analysis_service: AnalysisService = Depends(get_analysis_service) # If needed
) -> Dict[str, Any]:
    """
    Provides a general overview of the market.
    This might include major indices performance, top movers, overall sentiment.
    (Implementation will depend on available data from providers for general market info)
    """
    # This is a placeholder. Real implementation would fetch data for major indices,
    # news sentiment for "market" topic, etc.
    # For now, let's try to get quotes for a few major indices as an example.
    major_indices = settings.MARKET_OVERVIEW_INDICES # e.g., ["^GSPC", "^IXIC", "^DJI"]
    
    def map_index_symbol(symbol: str, provider: str) -> str:
        """Map index symbols to provider-specific formats."""
        index_map = {
            "alpha_vantage": {
                "^GSPC": "VOO",    # S&P 500 ETF (Vanguard S&P 500)
                "^IXIC": "NDAQ",   # NASDAQ - Working
                "^DJI": "DIA"      # Dow Jones ETF (SPDR Dow Jones)
            }
        }
        return index_map.get(provider, {}).get(symbol, symbol)

    async def fetch_index_quote(symbol: str):
        # Try default provider first
        quote = await market_service.get_current_quote(symbol=symbol)
        
        # If default provider fails, try other providers
        if not quote:
            for provider_name in market_service.providers.keys():
                if provider_name != market_service.default_provider_name:
                    try:
                        mapped_symbol = map_index_symbol(symbol, provider_name)
                        quote = await market_service.get_current_quote(
                            symbol=mapped_symbol,
                            provider_name=provider_name
                        )
                        if quote:
                            break
                    except Exception as e:
                        print(f"Provider {provider_name} failed for {symbol} ({mapped_symbol}): {e}")
                        continue

        if quote:
            return {
                "symbol": symbol,  # Return original symbol for consistency
                "name": settings.INDEX_NAMES.get(symbol, symbol),
                "price": quote.get("price"),
                "change": quote.get("change"),
                "change_percent": quote.get("change_percent")
            }
        return {"symbol": symbol, "error": "Data not available"}

    indices_data = []
    for idx_symbol in major_indices:
        data = await fetch_index_quote(idx_symbol)
        indices_data.append(data)
        if len(major_indices) > 1 and idx_symbol != major_indices[-1]: # Add delay if not the last symbol
            await asyncio.sleep(1) # Wait for 1 second before the next call
    
    # General market news sentiment
    # news_sentiment = await analysis_service.get_sentiment_analysis_report(topics=["market", "economy"])
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "major_indices": indices_data,
        # "market_sentiment": news_sentiment.get("overall_combined_label", "neutral"),
        # "top_gainers": [], # Placeholder - requires scanning many stocks
        # "top_losers": [],  # Placeholder
        "market_status_note": "Market overview is a simplified example. More data sources needed for comprehensive view."
    }

@router.get("/news", summary="Get general market or specific stock news")
async def get_general_market_news_endpoint(
    symbols: Optional[str] = Query(None, description="Comma-separated list of stock symbols for targeted news"),
    topics: Optional[str] = Query(None, description="Comma-separated list of topics (e.g., 'earnings,ipo')"),
    limit: int = Query(10, ge=1, le=50, description="Number of news articles to return"),
    provider: Optional[str] = Query(None, description="Specific market data provider to use"),
    market_service: MarketDataService = Depends(get_market_data_service)
) -> List[Dict[str, Any]]:
    """
    Fetches general market news or news related to specific symbols/topics.
    """
    symbol_list = [s.strip().upper() for s in symbols.split(',')] if symbols else None
    topic_list = [t.strip().lower() for t in topics.split(',')] if topics else None
    
    try:
        news_items = await market_service.get_market_news(
            symbols=symbol_list, 
            topics=topic_list, 
            limit=limit, 
            provider_name=provider
        )
        if not news_items:
            # Consider returning 204 No Content if appropriate, or just empty list
            return [] 
        return news_items
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market news: {str(e)}")

# Additional endpoints could include:
# - /sectors : Sector performance
# - /movers : Top gainers/losers (would require more complex data processing)
# - /economic_calendar : Upcoming economic events
