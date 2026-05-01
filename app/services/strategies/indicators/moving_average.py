# app/services/strategies/indicators/moving_average.py
import pandas as pd
from typing import List


def calculate_sma(closes: List[float], period: int = 20) -> List[float]:
    series = pd.Series(closes)
    return series.rolling(window=period, min_periods=period).mean().tolist()


def calculate_ema(closes: List[float], period: int = 20) -> List[float]:
    series = pd.Series(closes)
    return series.ewm(span=period, adjust=False).mean().tolist()


def get_latest_sma(closes: List[float], period: int = 20) -> float:
    sma = calculate_sma(closes, period)
    for val in reversed(sma):
        if pd.notna(val):
            return round(val, 6)
    return 0.0


def get_latest_ema(closes: List[float], period: int = 20) -> float:
    ema = calculate_ema(closes, period)
    return round(ema[-1], 6)
