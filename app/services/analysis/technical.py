"""
Technical analysis utilities
"""
import logging
from typing import Dict, List, Optional
from pandas import DataFrame

logger = logging.getLogger(__name__)

# Try to import pandas_ta, but make it optional
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    logger.warning("pandas_ta not installed. Some technical indicators will be unavailable.")
    HAS_PANDAS_TA = False

class TechnicalAnalyzer:
    """Technical analysis tools"""

    @staticmethod
    def get_indicators(data: DataFrame, indicators: List[str]) -> Dict[str, DataFrame]:
        """Calculate technical indicators"""
        if not HAS_PANDAS_TA:
            logger.error("pandas_ta is required for technical analysis")
            return {}

        result = {}
        for indicator in indicators:
            try:
                if hasattr(ta, indicator):
                    indicator_func = getattr(ta, indicator)
                    result[indicator] = indicator_func(data)
                else:
                    logger.warning(f"Indicator {indicator} not found in pandas_ta")
            except Exception as e:
                logger.error(f"Error calculating {indicator}: {str(e)}")

        return result

    @staticmethod
    def get_basic_analysis(data: DataFrame) -> Dict[str, DataFrame]:
        """Get basic technical analysis"""
        if not HAS_PANDAS_TA:
            return {
                "sma": data.rolling(window=20).mean(),
                "ema": data.ewm(span=20, adjust=False).mean()
            }

        # Use pandas_ta if available
        return {
            "sma": ta.sma(data, length=20),
            "ema": ta.ema(data, length=20),
            "rsi": ta.rsi(data, length=14)
        }
