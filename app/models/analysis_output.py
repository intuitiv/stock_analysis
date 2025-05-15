"""
Models for various types of analysis outputs.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin

class OutputType(enum.Enum):
    """Types of analysis outputs."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    PREDICTION = "prediction"
    PATTERN = "pattern"
    ANOMALY = "anomaly"
    SIGNAL = "signal"
    RISK = "risk"
    OPTIMIZATION = "optimization"
    TREND = "trend"
    ECONOMIC = "economic"
    NEWS = "news"
    SOCIAL = "social"
    ANALYST = "analyst"
    SEC = "sec"
    EARNINGS = "earnings"
    CUSTOM = "custom"

class BaseAnalysisOutput(Base, TimestampMixin, UUIDMixin):
    """Base model for all analysis outputs."""
    __tablename__ = "analysis_outputs"

    id = Column(Integer, primary_key=True, index=True)
    output_type = Column(SQLEnum(OutputType), nullable=False)
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    confidence_score = Column(Float)
    data = Column(JSON, nullable=False)
    output_metadata = Column(JSON)

    __mapper_args__ = {
        'polymorphic_on': output_type,
        'polymorphic_identity': 'base'
    }

class TechnicalIndicator(BaseAnalysisOutput):
    """Technical analysis indicator output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.TECHNICAL}

class FundamentalRatio(BaseAnalysisOutput):
    """Fundamental analysis ratio output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.FUNDAMENTAL}

class SentimentScore(BaseAnalysisOutput):
    """Sentiment analysis score output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.SENTIMENT}

class PricePrediction(BaseAnalysisOutput):
    """Price prediction output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.PREDICTION}

class PatternRecognition(BaseAnalysisOutput):
    """Pattern recognition output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.PATTERN}

class AnomalyDetection(BaseAnalysisOutput):
    """Anomaly detection output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.ANOMALY}

class TradingSignal(BaseAnalysisOutput):
    """Trading signal output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.SIGNAL}

class RiskAssessment(BaseAnalysisOutput):
    """Risk assessment output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.RISK}

class PortfolioOptimization(BaseAnalysisOutput):
    """Portfolio optimization output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.OPTIMIZATION}

class MarketTrend(BaseAnalysisOutput):
    """Market trend analysis output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.TREND}

class EconomicIndicator(BaseAnalysisOutput):
    """Economic indicator output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.ECONOMIC}

class NewsSentiment(BaseAnalysisOutput):
    """News sentiment analysis output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.NEWS}

class SocialMediaSentiment(BaseAnalysisOutput):
    """Social media sentiment analysis output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.SOCIAL}

class AnalystRating(BaseAnalysisOutput):
    """Analyst rating output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.ANALYST}

class SECFilingAnalysis(BaseAnalysisOutput):
    """SEC filing analysis output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.SEC}

class EarningsCallAnalysis(BaseAnalysisOutput):
    """Earnings call analysis output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.EARNINGS}

class CustomAnalysisOutput(BaseAnalysisOutput):
    """Custom analysis output."""
    __mapper_args__ = {'polymorphic_identity': OutputType.CUSTOM}
