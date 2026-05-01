# app/services/strategies/builtin/sma_crossover.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.moving_average import calculate_sma
import pandas as pd


class SMACrossoverStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        fast_period = self.parameters.get("fast_period", 10)
        slow_period = self.parameters.get("slow_period", 20)
        closes = self.get_closes(candles)

        if len(closes) < slow_period + 1:
            return None

        fast_sma = calculate_sma(closes, fast_period)
        slow_sma = calculate_sma(closes, slow_period)

        curr_fast = fast_sma[-1]
        prev_fast = fast_sma[-2]
        curr_slow = slow_sma[-1]
        prev_slow = slow_sma[-2]

        if pd.isna(curr_fast) or pd.isna(curr_slow) or pd.isna(prev_fast) or pd.isna(prev_slow):
            return None

        action = None
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            action = "BUY"
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            action = "SELL"

        if not action:
            return None

        return {
            "action": action,
            "price": closes[-1],
            "confidence": round(min(abs(curr_fast - curr_slow) / closes[-1] * 100, 1.0), 2),
            "indicators": {
                "fast_sma": round(float(curr_fast), 2),
                "slow_sma": round(float(curr_slow), 2),
            },
        }
