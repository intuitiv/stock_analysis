"""
NAETRA Services Package

This package provides various services for:
- Market Data (data collection from various providers)
- Analysis (technical and fundamental analysis)
- ML (machine learning predictions and pattern recognition)
- Portfolio Management
- User Management
"""

from .market_data_service import MarketDataService
from .analysis_service import AnalysisService
from .portfolio_service import PortfolioService
from .user_service import UserService
from .chat_service import ChatService

# Analysis sub-package exports
from .analysis.technical import TechnicalAnalyzer
from .analysis.fundamental import FundamentalAnalyzer
from .analysis.sentiment import SentimentAnalyzer

# Market data sub-package exports
from .market_data.alpha_vantage import AlphaVantageProvider
from .market_data.yahoo_finance import YahooFinanceProvider
from .market_data.sec_edgar import SECEdgarProvider

# ML sub-package exports
# from .ml.prediction import PredictionModel # PredictionModel class does not exist in prediction.py
# from .ml.pattern_recognition import PatternRecognizer # PatternRecognizer class does not exist in pattern_recognition.py

__all__ = [
    # Main services
    'MarketDataService',
    'AnalysisService',
    'PortfolioService',
    'UserService',
    'ChatService',
    
    # Analysis
    'TechnicalAnalyzer',
    'FundamentalAnalyzer',
    'SentimentAnalyzer',
    
    # Market Data Providers
    'AlphaVantageProvider',
    'YahooFinanceProvider',
    'SECEdgarProvider',
    
    # ML Components
    # 'PredictionModel', # Corresponding import is commented out
    # 'PatternRecognizer', # Corresponding import is commented out
]
