# app/services/strategies/builtin/macd_crossover.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.macd import calculate_macd


class MACDCrossoverStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        fast = self.parameters.get("fast_period", 12)
        slow = self.parameters.get("slow_period", 26)
        signal_p = self.parameters.get("signal_period", 9)
        closes = self.get_closes(candles)

        if len(closes) < slow + signal_p:
            return None

        result = calculate_macd(closes, fast, slow, signal_p)
        macd_line = result["macd"]
        signal_line = result["signal"]

        curr_macd = macd_line[-1]
        prev_macd = macd_line[-2]
        curr_signal = signal_line[-1]
        prev_signal = signal_line[-2]

        action = None
        if prev_macd <= prev_signal and curr_macd > curr_signal:
            action = "BUY"
        elif prev_macd >= prev_signal and curr_macd < curr_signal:
            action = "SELL"

        if not action:
            return None

        return {
            "action": action,
            "price": closes[-1],
            "confidence": round(min(abs(curr_macd - curr_signal) / closes[-1] * 1000, 1.0), 2),
            "indicators": {
                "macd": round(curr_macd, 6),
                "signal": round(curr_signal, 6),
                "histogram": round(curr_macd - curr_signal, 6),
            },
        }
