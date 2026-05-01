# app/services/strategies/builtin/dca_bot.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.rsi import get_latest_rsi
from app.services.strategies.indicators.moving_average import get_latest_sma


class DCABotStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        dip_threshold = self.parameters.get("dip_threshold", 0.02)
        rsi_threshold = self.parameters.get("rsi_threshold", 40)
        sma_period = self.parameters.get("sma_period", 20)
        closes = self.get_closes(candles)

        if len(closes) < sma_period + 1:
            return None

        current_price = closes[-1]
        sma = get_latest_sma(closes, sma_period)
        rsi = get_latest_rsi(closes)

        below_sma = current_price < sma
        price_dip = (sma - current_price) / sma if sma > 0 else 0
        rsi_low = rsi < rsi_threshold

        if below_sma and (price_dip >= dip_threshold or rsi_low):
            confidence = round(min((price_dip * 10) + (0.3 if rsi_low else 0), 1.0), 2)
            return {
                "action": "BUY",
                "price": current_price,
                "confidence": max(confidence, 0.4),
                "indicators": {
                    "rsi": rsi,
                    "sma": round(sma, 2),
                    "price_vs_sma": round(price_dip * 100, 2),
                    "below_sma": below_sma,
                    "rsi_low": rsi_low,
                },
            }

        return None
