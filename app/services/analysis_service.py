"""Service for performing various types of market analysis."""
from typing import Dict, Any, Optional, List
import asyncio
import logging
from datetime import datetime, timedelta

from app.services.market_data_service import MarketDataService
from app.services.analysis.technical import TechnicalAnalyzer
from app.services.analysis.fundamental import FundamentalAnalyzer
from app.services.analysis.sentiment import SentimentAnalyzer
from app.chaetra.brain import CHAETRA
from app.core.config import settings

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(
        self,
        market_data_service: MarketDataService,
        technical_analyzer: TechnicalAnalyzer,
        fundamental_analyzer: FundamentalAnalyzer,
        sentiment_analyzer: SentimentAnalyzer,
        chaetra_brain: Optional[CHAETRA] = None
    ):
        """Initialize the analysis service with required components."""
        self.market_data_service = market_data_service
        self.technical_analyzer = technical_analyzer
        self.fundamental_analyzer = fundamental_analyzer
        self.sentiment_analyzer = sentiment_analyzer
        self.chaetra_brain = chaetra_brain

    async def get_technical_analysis_report(
        self, 
        symbol: str, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None, 
        interval: str = "1d",
        indicators_config: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate a technical analysis report for a stock."""
        logger.info(f"Generating technical analysis report for {symbol}")
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=settings.TECHNICAL_ANALYSIS_DEFAULT_HISTORY_DAYS)
        
        price_data = await self.market_data_service.get_price_data(symbol, start_date, end_date, interval)
        if not price_data:
            return {"error": f"Could not fetch price data for {symbol}."}

        indicators_task = self.technical_analyzer.calculate_indicators(price_data, indicators_config)
        patterns_task = self.technical_analyzer.identify_chart_patterns(price_data)
        support_resistance_task = self.technical_analyzer.get_support_resistance(price_data)
        trend_task = self.technical_analyzer.get_trend_analysis(price_data)
        
        indicators, patterns, support_resistance, trend = await asyncio.gather(
            indicators_task, patterns_task, support_resistance_task, trend_task
        )
        
        return {
            "symbol": symbol,
            "interval": interval,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "indicators": indicators,
            "chart_patterns": patterns,
            "support_resistance": support_resistance,
            "trend_analysis": trend
        }

    async def get_fundamental_analysis_report(self, symbol: str) -> Dict[str, Any]:
        """Generate a fundamental analysis report for a stock."""
        logger.info(f"Generating fundamental analysis report for {symbol}")
        report = await self.fundamental_analyzer.get_full_fundamental_report(symbol)
        if not report.get("company_overview") and not report.get("financial_statement_analysis"):
            return {"error": f"Could not fetch fundamental data for {symbol}."}
        return report

    async def get_sentiment_analysis_report(
        self, 
        symbols: Optional[List[str]] = None, 
        topics: Optional[List[str]] = None,
        social_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a sentiment analysis report for stocks or topics."""
        target_name = ", ".join(symbols) if symbols else (", ".join(topics) if topics else social_query or "general market")
        logger.info(f"Generating sentiment analysis report for: {target_name}")
        
        report = await self.sentiment_analyzer.get_combined_sentiment_report(
            symbols=symbols, 
            topics=topics, 
            social_query=social_query
        )
        return report

    async def get_comprehensive_stock_analysis(
        self, 
        symbol: str,
        technical_interval: str = "1d",
        technical_history_days: int = settings.TECHNICAL_ANALYSIS_DEFAULT_HISTORY_DAYS
    ) -> Dict[str, Any]:
        """Generate a comprehensive analysis combining technical, fundamental, and sentiment data."""
        logger.info(f"Generating comprehensive analysis for {symbol}")
        
        end_date = datetime.utcnow()
        start_date_tech = end_date - timedelta(days=technical_history_days)

        # Fetch all data concurrently
        tech_task = self.get_technical_analysis_report(symbol, start_date_tech, end_date, technical_interval)
        fund_task = self.get_fundamental_analysis_report(symbol)
        sent_task = self.get_sentiment_analysis_report(symbols=[symbol])
        
        technical_report, fundamental_report, sentiment_report = await asyncio.gather(
            tech_task, fund_task, sent_task
        )

        comprehensive_report = {
            "symbol": symbol,
            "generated_at": datetime.utcnow().isoformat(),
            "technical_analysis": technical_report,
            "fundamental_analysis": fundamental_report,
            "sentiment_analysis": sentiment_report,
            "chaetra_synthesis": None
        }

        if self.chaetra_brain:
            try:
                # Prepare input data for CHAETRA
                chaetra_input_data = {
                    "price_summary": {
                        "current_price": technical_report.get("trend_analysis", {}).get("details", {}).get("close"),
                        "trend": technical_report.get("trend_analysis", {}).get("trend")
                    },
                    "key_technicals": {
                        "rsi": technical_report.get("indicators", {}).get("RSI", [{}])[-1].get("value"),
                        "macd_signal_diff": (
                            technical_report.get("indicators", {}).get("MACD", {}).get("macd", [0])[-1] -
                            technical_report.get("indicators", {}).get("MACD", {}).get("signal", [0])[-1]
                        ),
                        "patterns": [p.get("name") for p in technical_report.get("chart_patterns", [])[:3]]
                    },
                    "fundamental_summary": {
                        "pe_ratio": fundamental_report.get("company_overview", {}).get("pe_ratio"),
                        "eps": fundamental_report.get("company_overview", {}).get("eps_trailing_ttm"),
                        "revenue_growth_yoy": fundamental_report.get("financial_statement_analysis", {})
                            .get("analysis_summary", {}).get("income_statement_trends", {})
                            .get("totalRevenue_growth_yoy")
                    },
                    "news_sentiment_overall": sentiment_report.get("overall_combined_label")
                }
                
                query_intent = {
                    "query_type": "comprehensive_stock_assessment",
                    "entities": {"symbols": [symbol]},
                    "user_goal": "get_overall_outlook_and_suggestion"
                }
                
                request_context = {
                    "symbol": symbol,
                    "user_risk_profile": "moderate"
                }

                chaetra_analysis = await self.chaetra_brain.process_data_and_generate_analysis(
                    input_data=chaetra_input_data,
                    query_intent=query_intent,
                    request_context=request_context
                )
                comprehensive_report["chaetra_synthesis"] = chaetra_analysis
            except Exception as e:
                logger.error(f"Error during CHAETRA synthesis for {symbol}: {e}")
                comprehensive_report["chaetra_synthesis"] = {"error": str(e)}
        
        return comprehensive_report
