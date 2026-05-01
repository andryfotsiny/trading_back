# app/services/strategies/indicators/bollinger.py
import pandas as pd
from typing import List, Dict


def calculate_bollinger(closes: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
    series = pd.Series(closes)
    middle = series.rolling(window=period, min_periods=period).mean()
    std = series.rolling(window=period, min_periods=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return {
        "upper": upper.tolist(),
        "middle": middle.tolist(),
        "lower": lower.tolist(),
    }


def get_latest_bollinger(closes: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
    result = calculate_bollinger(closes, period, std_dev)
    latest = {}
    for key in ["upper", "middle", "lower"]:
        for val in reversed(result[key]):
            if pd.notna(val):
                latest[key] = round(val, 6)
                break
    return latest
