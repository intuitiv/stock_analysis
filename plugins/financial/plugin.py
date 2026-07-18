"""Financial analysis plugin for CHAETRA."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.chaetra.utils.validation import Validator, ValidationRule
from app.chaetra.utils.metrics import Counter, Histogram, metrics_collector
from app.chaetra.utils.errors import ValidationError
from app.chaetra.utils.logging import CHAETRALogger

logger = CHAETRALogger("financial_plugin")

class FinancialAnalysis:
    """Financial analysis tools."""
    
    @staticmethod
    def calculate_metrics(data: pd.DataFrame) -> Dict[str, float]:
        """Calculate key financial metrics."""
        metrics = {}
        
        # Price metrics
        metrics['daily_return'] = data['close'].pct_change().mean()
        metrics['volatility'] = data['close'].pct_change().std()
        
        # Volume metrics
        metrics['avg_volume'] = data['volume'].mean()
        metrics['volume_change'] = data['volume'].pct_change().mean()
        
        # Technical indicators
        metrics['sma_20'] = data['close'].rolling(window=20).mean().iloc[-1]
        metrics['sma_50'] = data['close'].rolling(window=50).mean().iloc[-1]
        metrics['rsi'] = FinancialAnalysis._calculate_rsi(data['close'])
        
        return metrics
    
    @staticmethod
    def _calculate_rsi(prices: pd.Series, periods: int = 14) -> float:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        rs = gain / loss
        return rs.iloc[-1]

class FinancialPlugin:
    """Financial analysis plugin implementation."""
    
    name: str = "financial_analysis"
    version: str = "1.0.0"
    description: str = "Financial analysis plugin for CHAETRA"
    domain: str = "finance"
    
    def __init__(self):
        self.config = {}
        self.market_client = None
        self._setup_metrics()
        self._setup_validators()
        
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin."""
        self.config = config
        self._setup_market_client()
        
    def get_tools(self) -> Dict[str, Any]:
        """Get domain-specific tools provided by this plugin."""
        return {
            "technical_indicators": {
                "sma": self._calculate_sma,
                "rsi": self._calculate_rsi
            },
            "fundamental_analysis": self._perform_fundamental_analysis
        }
        
    def get_prompts(self) -> Dict[str, str]:
        """Get domain-specific prompt templates."""
        return {
            "technical_analysis": """
                Analyze the technical indicators for {symbol}:
                - Calculate {indicator} over the last {timeframe}
                - Compare with historical patterns
                - Provide trading suggestions based on indicator signals
            """,
            "fundamental_analysis": """
                Perform fundamental analysis for {symbol}:
                - Review financial statements
                - Assess market position
                - Evaluate growth metrics
                - Consider industry trends
            """
        }
        
    def get_validators(self) -> Dict[str, Any]:
        """Get domain-specific validators."""
        return {
            "market_data": [
                ValidationRule(
                    field="symbol",
                    rule_type="required"
                ),
                ValidationRule(
                    field="timeframe",
                    rule_type="regex",
                    params={"pattern": r"^(1D|5D|1M|3M|6M|1Y|YTD)$"},
                    message="Invalid timeframe format"
                )
            ],
            "financial_data": [
                ValidationRule(
                    field="revenue",
                    rule_type="type",
                    params={"type": float},
                    message="Revenue must be a float"
                ),
                ValidationRule(
                    field="profit_margin",
                    rule_type="range",
                    params={"min": 0.0, "max": 1.0},
                    message="Profit margin must be between 0 and 1"
                )
            ]
        }
        
    def _setup_market_client(self) -> None:
        """Setup market data client based on configuration."""
        provider = self.config.get("market_data_provider")
        if provider == "alpha_vantage":
            from app.services.market_data.alpha_vantage import AlphaVantageClient
            self.market_client = AlphaVantageClient(
                api_key=self.config["api_key"],
                cache_ttl=self.config.get("cache_ttl", 3600)
            )
        elif provider == "yahoo_finance":
            from app.services.market_data.yahoo_finance import YahooFinanceClient
            self.market_client = YahooFinanceClient(
                api_key=self.config["api_key"],
                cache_ttl=self.config.get("cache_ttl", 3600)
            )
        elif provider == "finnhub":
            from app.services.market_data.finnhub import FinnhubClient
            self.market_client = FinnhubClient(
                api_key=self.config["api_key"],
                cache_ttl=self.config.get("cache_ttl", 3600)
            )
        else:
            raise ValidationError(
                "Invalid market data provider",
                details={"provider": provider}
            )
            
    def _setup_metrics(self) -> None:
        """Setup metrics for this plugin."""
        self.request_counter = Counter(
            "financial_requests_total",
            "Total financial analysis requests"
        )
        self.error_counter = Counter(
            "financial_errors_total",
            "Total errors in financial analysis"
        )
        self.response_time = Histogram(
            "financial_response_time_seconds",
            "Response time for financial analysis requests"
        )
        
        metrics_collector.register_metric(self.request_counter)
        metrics_collector.register_metric(self.error_counter)
        metrics_collector.register_metric(self.response_time)
        
    def _setup_validators(self) -> None:
        """Setup validators for this plugin."""
        validator = Validator()
        
        validator.add_rule(ValidationRule(
            field="symbol",
            rule_type="required"
        ))
        validator.add_rule(ValidationRule(
            field="timeframe",
            rule_type="regex",
            params={"pattern": r"^(1D|5D|1M|3M|6M|1Y|YTD)$"},
            message="Invalid timeframe format"
        ))
        
        self.validator = validator
        
    def _calculate_sma(self, data: pd.DataFrame, window: int = 20) -> float:
        """Calculate Simple Moving Average."""
        return data['close'].rolling(window=window).mean().iloc[-1]
        
    def _calculate_rsi(self, data: pd.DataFrame, periods: int = 14) -> float:
        """Calculate Relative Strength Index."""
        return FinancialAnalysis._calculate_rsi(data['close'], periods)
        
    def _perform_fundamental_analysis(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Perform fundamental analysis."""
        try:
            # Example implementation
            revenue = data.get("revenue", 0.0)
            profit_margin = data.get("profit_margin", 0.0)
            debt_to_equity = data.get("debt_to_equity", 0.0)
            
            return {
                "revenue_growth": revenue * 0.1,
                "profitability_score": profit_margin * 0.8,
                "financial_health": 1.0 / (1.0 + debt_to_equity)
            }
        except Exception as e:
            logger.error("Error in fundamental analysis", error=e)
            self.error_counter.increment(1)
            raise
        
    async def _fetch_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Fetch market data for analysis."""
        try:
            start_time = datetime.now()
            data = await self.market_client.get_historical_data(symbol, timeframe)
            self.response_time.observe(time.time() - start_time.timestamp())
            return data
        except Exception as e:
            logger.error("Error fetching market data", error=e)
            self.error_counter.increment(1)
            raise
