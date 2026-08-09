# app/services/strategies/builtin/donchian_trend.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.moving_average import get_latest_sma
from app.services.strategies.indicators.adx import calculate_adx


class DonchianTrendStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        donchian_period = self.parameters.get("donchian_period", 20)
        ma_period = self.parameters.get("ma_period", 50)
        adx_period = self.parameters.get("adx_period", 14)
        adx_threshold = self.parameters.get("adx_threshold", 20)

        min_len = max(donchian_period + 1, ma_period + 1, adx_period * 2 + 1)
        if len(candles) < min_len:
            return None

        closes = self.get_closes(candles)
        current_close = closes[-1]

        channel_candles = candles[-(donchian_period + 1):-1]
        channel_high = max(c["high"] for c in channel_candles)
        channel_low = min(c["low"] for c in channel_candles)

        ma = get_latest_sma(closes, ma_period)
        adx_result = calculate_adx(candles, adx_period)
        adx = adx_result["adx"]

        if adx <= adx_threshold:
            return None

        action = None
        if current_close > channel_high and current_close > ma:
            action = "BUY"
        elif current_close < channel_low and current_close < ma:
            action = "SELL"

        if not action:
            return None

        min_taker_buy_ratio = self.parameters.get("min_taker_buy_ratio")
        taker_buy_ratio = None
        if min_taker_buy_ratio is not None:
            last_candle = candles[-1]
            volume = last_candle.get("volume")
            taker_buy_volume = last_candle.get("taker_buy_volume")
            if volume and taker_buy_volume is not None:
                taker_buy_ratio = taker_buy_volume / volume
                if action == "BUY" and taker_buy_ratio < min_taker_buy_ratio:
                    return None
                if action == "SELL" and taker_buy_ratio > (1 - min_taker_buy_ratio):
                    return None

        confidence = round(min((adx - adx_threshold) / 50, 1.0), 2)

        return {
            "action": action,
            "price": current_close,
            "confidence": max(confidence, 0.3),
            "indicators": {
                "channel_high": round(channel_high, 2),
                "channel_low": round(channel_low, 2),
                "ma": round(ma, 2),
                "adx": adx,
                "plus_di": adx_result["plus_di"],
                "minus_di": adx_result["minus_di"],
                "taker_buy_ratio": round(taker_buy_ratio, 4) if taker_buy_ratio is not None else None,
            },
        }
