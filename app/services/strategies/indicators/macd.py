# app/services/strategies/indicators/macd.py
import pandas as pd
from typing import List, Dict


def calculate_macd(
    closes: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Dict[str, List[float]]:
    series = pd.Series(closes)
    ema_fast = series.ewm(span=fast_period, adjust=False).mean()
    ema_slow = series.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd": macd_line.tolist(),
        "signal": signal_line.tolist(),
        "histogram": histogram.tolist(),
    }


def get_latest_macd(
    closes: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Dict[str, float]:
    result = calculate_macd(closes, fast_period, slow_period, signal_period)
    return {
        "macd": round(result["macd"][-1], 6),
        "signal": round(result["signal"][-1], 6),
        "histogram": round(result["histogram"][-1], 6),
    }
