# app/services/strategies/builtin/scalp_momentum.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy


class ScalpMomentumStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        breakout_period = self.parameters.get("breakout_period", 10)
        min_taker_buy_ratio = self.parameters.get("min_taker_buy_ratio", 0.55)

        min_len = breakout_period + 1
        if len(candles) < min_len:
            return None

        closes = self.get_closes(candles)
        current_close = closes[-1]

        window_candles = candles[-(breakout_period + 1):-1]
        window_high = max(c["high"] for c in window_candles)
        window_low = min(c["low"] for c in window_candles)

        last_candle = candles[-1]
        volume = last_candle.get("volume")
        taker_buy_volume = last_candle.get("taker_buy_volume")
        taker_buy_ratio = taker_buy_volume / volume if volume else None

        action = None
        if current_close > window_high:
            action = "BUY"
        elif current_close < window_low:
            action = "SELL"

        if not action:
            return None

        if taker_buy_ratio is not None:
            if action == "BUY" and taker_buy_ratio < min_taker_buy_ratio:
                return None
            if action == "SELL" and taker_buy_ratio > (1 - min_taker_buy_ratio):
                return None

        distance = abs(current_close - (window_high if action == "BUY" else window_low))
        confidence = round(min(distance / current_close * 100, 1.0), 2) if current_close else 0.3

        return {
            "action": action,
            "price": current_close,
            "confidence": max(confidence, 0.3),
            "indicators": {
                "window_high": round(window_high, 2),
                "window_low": round(window_low, 2),
                "taker_buy_ratio": round(taker_buy_ratio, 4) if taker_buy_ratio is not None else None,
            },
        }
