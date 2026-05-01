# app/services/strategies/builtin/bollinger_bounce.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.bollinger import calculate_bollinger
import pandas as pd


class BollingerBounceStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        period = self.parameters.get("period", 20)
        std_dev = self.parameters.get("std_dev", 2.0)
        closes = self.get_closes(candles)

        if len(closes) < period + 1:
            return None

        bands = calculate_bollinger(closes, period, std_dev)
        upper = bands["upper"]
        lower = bands["lower"]
        middle = bands["middle"]

        curr_price = closes[-1]
        prev_price = closes[-2]
        curr_lower = lower[-1]
        prev_lower = lower[-2]
        curr_upper = upper[-1]
        prev_upper = upper[-2]

        if pd.isna(curr_lower) or pd.isna(curr_upper):
            return None

        action = None
        if prev_price <= prev_lower and curr_price > curr_lower:
            action = "BUY"
        elif prev_price >= prev_upper and curr_price < curr_upper:
            action = "SELL"

        if not action:
            return None

        band_width = float(curr_upper - curr_lower)
        distance = float(abs(curr_price - float(middle[-1])))
        confidence = round(min(distance / band_width * 2, 1.0), 2) if band_width > 0 else 0.5

        return {
            "action": action,
            "price": curr_price,
            "confidence": confidence,
            "indicators": {
                "upper": round(float(curr_upper), 2),
                "middle": round(float(middle[-1]), 2),
                "lower": round(float(curr_lower), 2),
            },
        }
