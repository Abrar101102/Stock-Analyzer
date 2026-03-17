import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalysisService:
    """
    Computes technical indicators from OHLCV price data.
    Uses the `ta` library for indicator calculations.
    """

    def compute_indicators(self, price_data: List[Dict]) -> pd.DataFrame:
        """
        Takes raw OHLCV data and returns a DataFrame with all indicators computed.
        
        :param price_data: List of dicts with keys: date, open, high, low, close, volume
        :return: DataFrame with indicator columns added
        """
        if not price_data:
            raise ValueError("No price data provided")

        df = pd.DataFrame(price_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        # --- Moving Averages ---
        df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
        df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
        df['sma_200'] = SMAIndicator(close=df['close'], window=200).sma_indicator()
        df['ema_12'] = EMAIndicator(close=df['close'], window=12).ema_indicator()
        df['ema_26'] = EMAIndicator(close=df['close'], window=26).ema_indicator()

        # --- RSI ---
        df['rsi_14'] = RSIIndicator(close=df['close'], window=14).rsi()

        # --- MACD ---
        macd = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
        df['macd_line'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()

        # --- Bollinger Bands ---
        bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()

        # --- VWAP ---
        try:
            vwap = VolumeWeightedAveragePrice(
                high=df['high'], low=df['low'], close=df['close'], volume=df['volume']
            )
            df['vwap'] = vwap.volume_weighted_average_price()
        except Exception as e:
            logger.warning(f"VWAP computation failed: {e}")
            df['vwap'] = None

        # --- Support / Resistance (pivot-based) ---
        df['support_level'] = self._compute_support(df)
        df['resistance_level'] = self._compute_resistance(df)

        # Replace NaN with None for DB storage
        df = df.where(pd.notnull(df), None)

        return df

    @staticmethod
    def _compute_support(df: pd.DataFrame, window: int = 20) -> pd.Series:
        """Simple rolling min of lows as support"""
        return df['low'].rolling(window=window, min_periods=1).min()

    @staticmethod
    def _compute_resistance(df: pd.DataFrame, window: int = 20) -> pd.Series:
        """Simple rolling max of highs as resistance"""
        return df['high'].rolling(window=window, min_periods=1).max()

    def get_signals(self, df: pd.DataFrame) -> Dict:
        """
        Generate buy/sell signals from the latest row of indicator data.
        """
        if df.empty:
            return {}

        latest = df.iloc[-1]
        signals = {}

        # RSI signals
        if latest.get('rsi_14') is not None:
            if latest['rsi_14'] < 30:
                signals['rsi'] = 'oversold'
            elif latest['rsi_14'] > 70:
                signals['rsi'] = 'overbought'
            else:
                signals['rsi'] = 'neutral'

        # MACD signal
        if latest.get('macd_histogram') is not None:
            signals['macd'] = 'bullish' if latest['macd_histogram'] > 0 else 'bearish'

        # Bollinger Band signal
        if latest.get('close') and latest.get('bb_lower') and latest.get('bb_upper'):
            if latest['close'] <= latest['bb_lower']:
                signals['bollinger'] = 'oversold'
            elif latest['close'] >= latest['bb_upper']:
                signals['bollinger'] = 'overbought'
            else:
                signals['bollinger'] = 'neutral'

        # SMA crossover signal
        if latest.get('sma_50') and latest.get('sma_200'):
            signals['sma_cross'] = 'golden_cross' if latest['sma_50'] > latest['sma_200'] else 'death_cross'

        return signals