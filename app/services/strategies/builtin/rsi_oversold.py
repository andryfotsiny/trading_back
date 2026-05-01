# app/services/strategies/builtin/rsi_oversold.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.rsi import get_latest_rsi


class RSIOversoldStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        period = self.parameters.get("rsi_period", 14)
        oversold = self.parameters.get("oversold", 30)
        overbought = self.parameters.get("overbought", 70)
        closes = self.get_closes(candles)

        if len(closes) < period + 1:
            return None

        rsi = get_latest_rsi(closes, period)
        prev_closes = closes[:-1]
        prev_rsi = get_latest_rsi(prev_closes, period)

        action = None
        if prev_rsi <= oversold and rsi > oversold:
            action = "BUY"
        elif prev_rsi >= overbought and rsi < overbought:
            action = "SELL"

        if not action:
            return None

        return {
            "action": action,
            "price": closes[-1],
            "confidence": round(abs(rsi - 50) / 50, 2),
            "indicators": {"rsi": rsi, "prev_rsi": prev_rsi},
        }
