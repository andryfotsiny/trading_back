# app/services/strategies/builtin/liquidity_sweep.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.rsi import get_latest_rsi


class LiquiditySweepStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        lookback = self.parameters.get("lookback", 20)
        wick_ratio = self.parameters.get("wick_ratio", 0.6)

        if len(candles) < lookback + 5:
            return None

        closes = self.get_closes(candles)
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        opens = [c["open"] for c in candles]

        recent_highs = highs[-(lookback+3):-3]
        recent_lows = lows[-(lookback+3):-3]
        resistance = max(recent_highs)
        support = min(recent_lows)

        curr = candles[-1]
        prev = candles[-2]
        curr_close = curr["close"]
        curr_open = curr["open"]
        curr_high = curr["high"]
        curr_low = curr["low"]
        body = abs(curr_close - curr_open)
        total_range = curr_high - curr_low

        if total_range == 0:
            return None

        upper_wick = curr_high - max(curr_close, curr_open)
        lower_wick = min(curr_close, curr_open) - curr_low

        rsi = get_latest_rsi(closes)
        action = None
        confidence = 0.5

        swept_high = curr_high > resistance and curr_close < resistance
        if swept_high and upper_wick / total_range >= wick_ratio:
            if curr_close < curr_open:
                action = "SELL"
                confidence = 0.65
                sweep_depth = (curr_high - resistance) / resistance
                if sweep_depth > 0.001:
                    confidence += 0.1
                if rsi > 55:
                    confidence += 0.1

        swept_low = curr_low < support and curr_close > support
        if swept_low and lower_wick / total_range >= wick_ratio:
            if curr_close > curr_open:
                action = "BUY"
                confidence = 0.65
                sweep_depth = (support - curr_low) / support
                if sweep_depth > 0.001:
                    confidence += 0.1
                if rsi < 45:
                    confidence += 0.1

        if not action:
            return None

        return {
            "action": action,
            "price": curr_close,
            "confidence": min(round(confidence, 2), 0.95),
            "indicators": {
                "resistance": round(resistance, 2),
                "support": round(support, 2),
                "swept_high": swept_high,
                "swept_low": swept_low,
                "upper_wick_ratio": round(upper_wick / total_range, 2),
                "lower_wick_ratio": round(lower_wick / total_range, 2),
                "rsi": rsi,
            },
        }
