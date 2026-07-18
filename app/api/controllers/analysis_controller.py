from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.analysis_service import AnalysisService
from app.chaetra.brain import CHAETRA # For direct CHAETRA interaction if needed
from app.core.config import settings
# from app.core.security import get_current_active_user # If endpoints need auth
# from app.models.user import User # If using user context

router = APIRouter()

# Dependency for AnalysisService
from app.core.dependencies import get_analysis_service
# Dependency for CHAETRA (if direct interaction is needed for some endpoints)
# from app.main import get_chaetra_brain # Import from main


@router.get("/{symbol}/technical", summary="Get technical analysis for a stock symbol")
async def get_technical_analysis_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    start_date_str: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for historical data. Defaults according to service."),
    end_date_str: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for historical data. Defaults to today."),
    interval: str = Query("1d", description="Data interval (e.g., '1m', '1h', '1d')"),
    # Allow passing indicator configs as JSON string or comma-separated list of names
    indicators: Optional[str] = Query(None, description="Comma-separated list of indicator names (e.g., 'SMA_20,RSI_14,MACD_12_26_9') or JSON list of configs."),
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> Dict[str, Any]:
    """
    Retrieves technical analysis for the given stock symbol, including indicators,
    chart patterns, support/resistance levels, and trend analysis.
    """
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None

        indicators_config: Optional[List[Dict[str, Any]]] = None
        if indicators:
            # Try to parse as JSON list of dicts first
            try:
                import json
                parsed_indicators = json.loads(indicators)
                if isinstance(parsed_indicators, list) and all(isinstance(i, dict) for i in parsed_indicators):
                    indicators_config = parsed_indicators
                else: # Assume comma-separated names
                    raise ValueError("Not a list of dicts")
            except (json.JSONDecodeError, ValueError): # Fallback to parsing comma-separated names
                indicators_config = []
                for ind_str in indicators.split(','):
                    parts = ind_str.strip().upper().split('_')
                    name = parts[0]
                    config = {"name": name}
                    if name == "SMA" or name == "EMA" or name == "RSI":
                        if len(parts) > 1 and parts[1].isdigit(): config["period"] = int(parts[1])
                    elif name == "MACD":
                        if len(parts) == 4 and all(p.isdigit() for p in parts[1:]):
                            config["params"] = tuple(map(int, parts[1:]))
                    elif name == "BBANDS":
                        if len(parts) > 1 and parts[1].isdigit(): config["period"] = int(parts[1])
                        if len(parts) > 2 and parts[2].replace('.', '', 1).isdigit(): config["stddev"] = float(parts[2])
                    indicators_config.append(config)
        
        report = await analysis_service.get_technical_analysis_report(
            symbol.upper(), start_date, end_date, interval, indicators_config
        )
        if report.get("error"):
            raise HTTPException(status_code=404, detail=report["error"])
        return report
    except ValueError as ve: # Handles date parsing errors
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching technical analysis for {symbol}: {str(e)}")


@router.get("/{symbol}/fundamental", summary="Get fundamental analysis for a stock symbol")
async def get_fundamental_analysis_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> Dict[str, Any]:
    """
    Retrieves fundamental analysis for the given stock symbol, including company overview,
    financial statement analysis, and valuation.
    """
    try:
        report = await analysis_service.get_fundamental_analysis_report(symbol.upper())
        if report.get("error"):
            raise HTTPException(status_code=404, detail=report["error"])
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fundamental analysis for {symbol}: {str(e)}")


@router.get("/sentiment", summary="Get sentiment analysis for symbols or topics")
async def get_sentiment_analysis_endpoint(
    symbols: Optional[str] = Query(None, description="Comma-separated list of stock symbols (e.g., 'AAPL,MSFT')"),
    topics: Optional[str] = Query(None, description="Comma-separated list of topics (e.g., 'AI,EV,inflation')"),
    social_query: Optional[str] = Query(None, description="Query for social media sentiment (e.g., 'Tesla stock sentiment')"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> Dict[str, Any]:
    """
    Retrieves sentiment analysis based on news and (placeholder) social media data
    for the given symbols or topics.
    """
    if not symbols and not topics and not social_query:
        raise HTTPException(status_code=400, detail="At least one of 'symbols', 'topics', or 'social_query' must be provided.")
    
    symbol_list = [s.strip().upper() for s in symbols.split(',')] if symbols else None
    topic_list = [t.strip().lower() for t in topics.split(',')] if topics else None
    
    try:
        report = await analysis_service.get_sentiment_analysis_report(
            symbols=symbol_list, 
            topics=topic_list, 
            social_query=social_query
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sentiment analysis: {str(e)}")


@router.get("/{symbol}/comprehensive", summary="Get comprehensive analysis for a stock symbol")
async def get_comprehensive_analysis_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
    # Add more query params to customize parts of the comprehensive report if needed
) -> Dict[str, Any]:
    """
    Retrieves a comprehensive analysis report for the given stock symbol,
    combining technical, fundamental, sentiment, and CHAETRA synthesis.
    """
    try:
        report = await analysis_service.get_comprehensive_stock_analysis(symbol.upper())
        if report.get("technical_analysis", {}).get("error") or \
           report.get("fundamental_analysis", {}).get("error"):
           # Partial error, decide if to return partial data or 404/500
           # For now, return what we have, client can check for errors in sub-reports
           pass
        if not report.get("technical_analysis") and not report.get("fundamental_analysis"): # Complete failure
            raise HTTPException(status_code=404, detail=f"Could not retrieve sufficient data for comprehensive analysis of {symbol}")
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching comprehensive analysis for {symbol}: {str(e)}")

# Placeholder for direct CHAETRA query endpoint if needed for more advanced/custom analyses
# @router.post("/chaetra/query", summary="Query CHAETRA brain directly")
# async def query_chaetra_endpoint(
#     query_text: str = Body(..., embed=True),
#     context: Optional[Dict[str, Any]] = Body({}, embed=True),
#     # This endpoint would require careful input validation and structuring
#     chaetra_brain: CHAETRA = Depends(CHAETRA.get_instance) # Assuming singleton setup
# ):
#     try:
#         intent = await chaetra_brain.understand_query_intent(query_text, context.get("chat_context"))
#         if not intent.get("can_handle", True): # Check if CHAETRA can handle
#             raise HTTPException(status_code=400, detail=intent.get("error_message", "Query cannot be handled."))
        
#         # NAETRA layer would be responsible for fetching data based on intent
#         # This is a simplified direct call, assuming data might be in context or intent implies general knowledge query
#         # For data-driven analysis, use the /comprehensive or specific analysis endpoints
#         input_data_for_chaetra = context.get("input_data", {}) # User might provide some data
        
#         response = await chaetra_brain.process_data_and_generate_analysis(
#             input_data=input_data_for_chaetra,
#             query_intent=intent,
#             request_context=context.get("request_context", {})
#         )
#         return response
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error querying CHAETRA: {str(e)}")
