import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import pandas_ta as ta # Import pandas-ta

from app.core.config import settings # For default indicator parameters

class TechnicalAnalyzer:
    def __init__(self):
        # Default parameters can be loaded from settings or passed during analysis
        self.default_sma_periods = settings.DEFAULT_SMA_PERIODS # e.g., [20, 50, 200]
        self.default_ema_periods = settings.DEFAULT_EMA_PERIODS # e.g., [12, 26]
        self.default_rsi_period = settings.DEFAULT_RSI_PERIOD # e.g., 14
        self.default_macd_params = settings.DEFAULT_MACD_PARAMS # e.g., (12, 26, 9)
        self.default_bbands_period = settings.DEFAULT_BBANDS_PERIOD # e.g., 20
        self.default_bbands_stddev = settings.DEFAULT_BBANDS_STDDEV # e.g., 2

    def _prepare_dataframe(self, price_data: List[Dict[str, Any]]) -> Optional[pd.DataFrame]:
        if not price_data or len(price_data) < max(self.default_sma_periods + self.default_ema_periods + [self.default_rsi_period, self.default_macd_params[1], self.default_bbands_period]): # Ensure enough data
            return None
        
        df = pd.DataFrame(price_data)
        if 'timestamp' not in df.columns or df['timestamp'].isnull().all():
            return None # Timestamps are crucial

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)

        # Ensure required OHLCV columns are present and numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col not in df.columns:
                return None # Missing essential data
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.dropna(subset=['open', 'high', 'low', 'close', 'volume'], inplace=True) # Drop rows where essential data is missing
        if df.empty:
            return None
            
        return df

    async def calculate_indicators(
        self, 
        price_data: List[Dict[str, Any]], 
        requested_indicators: Optional[List[Dict[str, Any]]] = None # e.g., [{'name': 'SMA', 'period': 50}, {'name': 'RSI'}]
    ) -> Dict[str, Any]:
        df = self._prepare_dataframe(price_data)
        if df is None:
            return {"error": "Insufficient or malformed price data for technical analysis."}

        # Ensure DataFrame has the ta strategy applied for pandas_ta
        df.ta.strategy("common") # Applies a common set of indicators, can be customized

        results = {"timestamps": df.index.strftime('%Y-%m-%dT%H:%M:%S%z').tolist()}
        
        indicators_to_calc = requested_indicators if requested_indicators else self._get_default_indicator_configs()

        for indicator_config in indicators_to_calc:
            name = indicator_config.get("name", "").upper()
            try:
                if name == "SMA":
                    period = int(indicator_config.get("period", self.default_sma_periods[0]))
                    sma_series = df.ta.sma(length=period, close=df['close'])
                    if sma_series is not None: results[f"SMA_{period}"] = sma_series.replace({np.nan:None}).tolist()
                elif name == "EMA":
                    period = int(indicator_config.get("period", self.default_ema_periods[0]))
                    ema_series = df.ta.ema(length=period, close=df['close'])
                    if ema_series is not None: results[f"EMA_{period}"] = ema_series.replace({np.nan:None}).tolist()
                elif name == "RSI":
                    period = int(indicator_config.get("period", self.default_rsi_period))
                    rsi_series = df.ta.rsi(length=period, close=df['close'])
                    if rsi_series is not None: results["RSI"] = rsi_series.replace({np.nan:None}).tolist()
                elif name == "MACD":
                    fast, slow, signal = map(int, indicator_config.get("params", self.default_macd_params))
                    macd_df = df.ta.macd(fast=fast, slow=slow, signal=signal, close=df['close'])
                    if macd_df is not None:
                        results["MACD"] = {
                            "macd": macd_df[f'MACD_{fast}_{slow}_{signal}'].replace({np.nan:None}).tolist(),
                            "signal": macd_df[f'MACDs_{fast}_{slow}_{signal}'].replace({np.nan:None}).tolist(),
                            "hist": macd_df[f'MACDh_{fast}_{slow}_{signal}'].replace({np.nan:None}).tolist()
                        }
                elif name == "BBANDS":
                    period = int(indicator_config.get("period", self.default_bbands_period))
                    stddev = float(indicator_config.get("stddev", self.default_bbands_stddev))
                    bbands_df = df.ta.bbands(length=period, std=stddev, close=df['close'])
                    if bbands_df is not None:
                        results["BBANDS"] = {
                            "upper": bbands_df[f'BBU_{period}_{stddev}'].replace({np.nan:None}).tolist(),
                            "middle": bbands_df[f'BBM_{period}_{stddev}'].replace({np.nan:None}).tolist(),
                            "lower": bbands_df[f'BBL_{period}_{stddev}'].replace({np.nan:None}).tolist()
                        }
                elif name == "OBV":
                    obv_series = df.ta.obv(close=df['close'], volume=df['volume'])
                    if obv_series is not None: results["OBV"] = obv_series.replace({np.nan:None}).tolist()
                elif name == "STOCH":
                    # pandas-ta stoch: k, d, slow_k, slow_d, fast_k_period, fast_d_period, slow_k_period, slow_d_period
                    # talib STOCH: slowk, slowd (fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)
                    # For simplicity, using pandas-ta defaults or simple mapping
                    k = int(indicator_config.get("k", 14)) # fastk_period in talib
                    d = int(indicator_config.get("d", 3))  # slowk_period in talib (used for STOCH's %K)
                    smooth_k = int(indicator_config.get("smooth_k", 3)) # slowd_period in talib (used for STOCH's %D)
                    
                    stoch_df = df.ta.stoch(high=df['high'], low=df['low'], close=df['close'], k=k, d=d, smooth_k=smooth_k)
                    if stoch_df is not None:
                        results["STOCH"] = {
                            "k": stoch_df[f'STOCHk_{k}_{d}_{smooth_k}'].replace({np.nan:None}).tolist(), # This is %K
                            "d": stoch_df[f'STOCHd_{k}_{d}_{smooth_k}'].replace({np.nan:None}).tolist()  # This is %D
                        }
            except Exception as e:
                results[name if name else "unknown_indicator_error"] = f"Error calculating {name} with pandas_ta: {str(e)}"
                print(f"Error calculating indicator {name}: {e}")
        
        return results

    def _get_default_indicator_configs(self) -> List[Dict[str, Any]]:
        # Construct default indicator configurations from settings
        configs = []
        for period in self.default_sma_periods:
            configs.append({"name": "SMA", "period": period})
        for period in self.default_ema_periods:
            configs.append({"name": "EMA", "period": period})
        configs.append({"name": "RSI", "period": self.default_rsi_period})
        configs.append({"name": "MACD", "params": self.default_macd_params})
        configs.append({"name": "BBANDS", "period": self.default_bbands_period, "stddev": self.default_bbands_stddev})
        configs.append({"name": "OBV"})
        configs.append({"name": "STOCH"}) # Uses default STOCH params if not specified
        return configs

    async def identify_chart_patterns(self, price_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        df = self._prepare_dataframe(price_data)
        if df is None:
            return [{"error": "Insufficient data for chart pattern analysis."}]

        patterns = []
        # pandas-ta candlestick pattern recognition
        # Example: Engulfing Pattern
        # df.ta.cdl_pattern(name="all") can find all patterns
        # For specific patterns:
        engulfing_series = df.ta.cdl_pattern(name="engulfing")
        if engulfing_series is not None and not engulfing_series.empty:
            engulfing_signals = engulfing_series[engulfing_series != 0]
            for idx_timestamp, signal_val in engulfing_signals.items():
                patterns.append({
                    "name": "Engulfing Pattern",
                    "type": "candlestick",
                    "signal": "bullish" if signal_val > 0 else "bearish", # pandas-ta: 100 for bullish, -100 for bearish
                    "timestamp": idx_timestamp.strftime('%Y-%m-%dT%H:%M:%S%z'),
                    "price_at_signal": df.loc[idx_timestamp, 'close']
                })
        
        # Example: Doji
        doji_series = df.ta.cdl_pattern(name="doji")
        if doji_series is not None and not doji_series.empty:
            doji_signals = doji_series[doji_series != 0] # Doji is 100
            for idx_timestamp, signal_val in doji_signals.items():
                 patterns.append({
                    "name": "Doji",
                    "type": "candlestick",
                    "signal": "neutral/reversal_potential", # Doji itself is neutral
                    "timestamp": idx_timestamp.strftime('%Y-%m-%dT%H:%M:%S%z'),
                    "price_at_signal": df.loc[idx_timestamp, 'close']
                })
        
        # Add more patterns as needed. pandas-ta supports many via df.ta.cdl_pattern(name="pattern_name")
        # e.g., "hammer", "shootingstar"
        # For more complex patterns (Head & Shoulders, Triangles), custom logic or specialized libraries are needed.
        # advanced_patterns = self._detect_advanced_patterns(df)
        # patterns.extend(advanced_patterns)
        
        return patterns
    
    # Placeholder for more advanced pattern detection logic
    # def _detect_advanced_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
    #     # Implement logic for Head & Shoulders, Triangles, Flags, etc.
    #     # This can be quite complex, involving peak/trough detection, trendline analysis.
    #     return []

    async def get_support_resistance(self, price_data: List[Dict[str, Any]], window: int = 20) -> Dict[str, List[float]]:
        df = self._prepare_dataframe(price_data)
        if df is None or len(df) < window:
            return {"support": [], "resistance": []}

        # Simple method: rolling min/max
        # More advanced: pivot points, Fibonacci retracements, clustering
        support_levels = df['low'].rolling(window=window, center=True).min().dropna().tolist()
        resistance_levels = df['high'].rolling(window=window, center=True).max().dropna().tolist()
        
        # Further processing: cluster nearby levels, validate significance
        # For now, returning raw rolling levels
        return {
            "support": sorted(list(set(support_levels))), # Unique sorted
            "resistance": sorted(list(set(resistance_levels)))
        }

    async def get_trend_analysis(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        df = self._prepare_dataframe(price_data)
        df = self._prepare_dataframe(price_data)
        if df is None:
            return {"trend": "undetermined", "strength": 0, "details": "Insufficient data for trend analysis."}

        sma_short_period = int(self.default_sma_periods[0] if self.default_sma_periods else 20)
        sma_long_period = int(self.default_sma_periods[-1] if self.default_sma_periods else 200)

        if len(df) < sma_long_period:
            return {"trend": "undetermined", "strength": 0, "details": f"Insufficient data for {sma_long_period}-period SMA"}

        sma_short = df.ta.sma(length=sma_short_period, close=df['close'])
        sma_long = df.ta.sma(length=sma_long_period, close=df['close'])
        adx_series = df.ta.adx(length=14, high=df['high'], low=df['low'], close=df['close']) # ADX for trend strength

        if sma_short is None or sma_long is None or adx_series is None:
            return {"trend": "undetermined", "strength": 0, "details": "SMA or ADX calculation failed."}

        current_close = df['close'].iloc[-1]
        current_sma_short = sma_short.iloc[-1]
        current_sma_long = sma_long.iloc[-1]
        current_adx = adx_series[f'ADX_14'].iloc[-1] # ADX column name from pandas-ta

        if pd.isna(current_sma_short) or pd.isna(current_sma_long):
            return {"trend": "undetermined", "strength": 0, "details": "SMA calculation resulted in NaN"}

        trend = "sideways"
        strength = 0.3 # Default for sideways

        if current_close > current_sma_short and current_sma_short > current_sma_long:
            trend = "strong_uptrend"
            strength = 0.7 + min(0.3, (current_adx / 100.0) * 0.6) if pd.notna(current_adx) and current_adx > 25 else 0.7
        elif current_close > current_sma_long and current_sma_short > current_sma_long : # General uptrend
            trend = "uptrend"
            strength = 0.5 + min(0.2, (current_adx / 100.0) * 0.4) if pd.notna(current_adx) and current_adx > 20 else 0.5
        elif current_close < current_sma_short and current_sma_short < current_sma_long:
            trend = "strong_downtrend"
            strength = 0.7 + min(0.3, (current_adx / 100.0) * 0.6) if pd.notna(current_adx) and current_adx > 25 else 0.7
        elif current_close < current_sma_long and current_sma_short < current_sma_long: # General downtrend
            trend = "downtrend"
            strength = 0.5 + min(0.2, (current_adx / 100.0) * 0.4) if pd.notna(current_adx) and current_adx > 20 else 0.5
        
        if trend == "sideways" and pd.notna(current_adx) and current_adx < 20: # Low ADX confirms sideways
            strength = 0.2 
        elif trend == "sideways" and pd.notna(current_adx) and current_adx >= 20: # ADX picking up but SMAs not aligned
            strength = 0.4


        return {
            "trend": trend,
            "strength": round(min(1.0, max(0.0, strength)), 2),
            "details": {
                "close": float(current_close) if pd.notna(current_close) else None,
                f"sma_{sma_short_period}": float(round(current_sma_short,2)) if pd.notna(current_sma_short) else None,
                f"sma_{sma_long_period}": float(round(current_sma_long,2)) if pd.notna(current_sma_long) else None,
                "adx_14": float(round(current_adx,2)) if pd.notna(current_adx) else None
            }
        }
