"""
Models package initialization.
Exports all SQLAlchemy models for easy access and Alembic migrations.
"""

from app.core.database import Base # Base for all models

# Import all models to ensure they are registered with SQLAlchemy's metadata
from .user import User
from .stock import Stock
from .portfolio import Portfolio, Position, Transaction
from .analysis import Analysis, AnalysisInput, AnalysisResult, AnalysisRun
from .analysis_output import (
    TechnicalIndicator, FundamentalRatio, SentimentScore,
    PricePrediction, PatternRecognition, AnomalyDetection,
    TradingSignal, RiskAssessment, PortfolioOptimization,
    MarketTrend, EconomicIndicator, NewsSentiment,
    SocialMediaSentiment, AnalystRating, SECFilingAnalysis,
    EarningsCallAnalysis, CustomAnalysisOutput
)
from .chat import ChatSession, ChatMessage

# You can optionally define __all__ to control what `from app.models import *` imports
__all__ = [
    "Base",
    "User",
    "Stock",
    "Portfolio",
    "Position",
    "Transaction",
    "Analysis",
    "AnalysisInput",
    "AnalysisResult",
    "AnalysisRun",
    "TechnicalIndicator",
    "FundamentalRatio",
    "SentimentScore",
    "PricePrediction",
    "PatternRecognition",
    "AnomalyDetection",
    "TradingSignal",
    "RiskAssessment",
    "PortfolioOptimization",
    "MarketTrend",
    "EconomicIndicator",
    "NewsSentiment",
    "SocialMediaSentiment",
    "AnalystRating",
    "SECFilingAnalysis",
    "EarningsCallAnalysis",
    "CustomAnalysisOutput",
    "ChatSession",
    "ChatMessage",
]
