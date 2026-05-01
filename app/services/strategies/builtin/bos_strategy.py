# app/services/strategies/builtin/bos_strategy.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.rsi import get_latest_rsi


class BOSStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        lookback = self.parameters.get("lookback", 20)
        confirmation = self.parameters.get("confirmation_candles", 2)

        if len(candles) < lookback + confirmation + 5:
            return None

        closes = self.get_closes(candles)
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]

        swing_highs = []
        swing_lows = []
        for i in range(2, len(candles) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append({"index": i, "price": highs[i]})
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append({"index": i, "price": lows[i]})

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return None

        current_price = closes[-1]
        prev_price = closes[-2]
        rsi = get_latest_rsi(closes)

        last_high = swing_highs[-1]["price"]
        prev_high = swing_highs[-2]["price"] if len(swing_highs) >= 2 else last_high
        last_low = swing_lows[-1]["price"]
        prev_low = swing_lows[-2]["price"] if len(swing_lows) >= 2 else last_low

        bullish_bos = current_price > last_high and prev_price <= last_high
        bearish_bos = current_price < last_low and prev_price >= last_low

        higher_highs = last_high > prev_high
        lower_lows = last_low < prev_low

        action = None
        confidence = 0.5

        if bullish_bos:
            action = "BUY"
            confidence = 0.6
            if higher_highs:
                confidence += 0.15
            if rsi < 60:
                confidence += 0.1

        elif bearish_bos:
            action = "SELL"
            confidence = 0.6
            if lower_lows:
                confidence += 0.15
            if rsi > 40:
                confidence += 0.1

        if not action:
            return None

        return {
            "action": action,
            "price": current_price,
            "confidence": min(round(confidence, 2), 0.95),
            "indicators": {
                "last_swing_high": round(last_high, 2),
                "last_swing_low": round(last_low, 2),
                "bullish_bos": bullish_bos,
                "bearish_bos": bearish_bos,
                "higher_highs": higher_highs,
                "lower_lows": lower_lows,
                "rsi": rsi,
            },
        }
