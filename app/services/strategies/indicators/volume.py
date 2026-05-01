# app/services/strategies/indicators/volume.py
import pandas as pd
from typing import List, Dict


def calculate_volume_sma(volumes: List[float], period: int = 20) -> List[float]:
    series = pd.Series(volumes)
    return series.rolling(window=period, min_periods=period).mean().tolist()


def get_volume_analysis(volumes: List[float], period: int = 20) -> Dict:
    series = pd.Series(volumes)
    avg = series.rolling(window=period, min_periods=period).mean()
    current = float(volumes[-1])
    avg_val = float(avg.iloc[-1]) if pd.notna(avg.iloc[-1]) else 0.0
    ratio = float(current / avg_val) if avg_val > 0 else 0.0
    return {
        "current_volume": current,
        "avg_volume": round(avg_val, 2),
        "ratio": round(ratio, 2),
        "above_average": bool(ratio > 1.0),
    }