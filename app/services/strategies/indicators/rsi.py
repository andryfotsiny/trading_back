# app/services/strategies/indicators/rsi.py
import pandas as pd
from typing import List


def calculate_rsi(closes: List[float], period: int = 14) -> List[float]:
    series = pd.Series(closes)
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.tolist()


def get_latest_rsi(closes: List[float], period: int = 14) -> float:
    rsi = calculate_rsi(closes, period)
    for val in reversed(rsi):
        if pd.notna(val):
            return round(val, 2)
    return 0.0
