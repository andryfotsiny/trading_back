# app/services/strategies/indicators/atr.py
from typing import List, Dict


def calculate_true_ranges(candles: List[Dict]) -> List[float]:
    ranges = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i - 1]["close"]
        ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    return ranges


def calculate_atr(candles: List[Dict], period: int = 14) -> float:
    ranges = calculate_true_ranges(candles)
    if len(ranges) < period:
        return 0.0
    return round(sum(ranges[-period:]) / period, 8)


def get_atr_pct(candles: List[Dict], period: int = 14) -> float:
    atr = calculate_atr(candles, period)
    if not atr or not candles:
        return 0.0
    last_close = candles[-1]["close"]
    if last_close <= 0:
        return 0.0
    return round(atr / last_close, 8)
