# app/services/strategies/builtin/scalp_reversion.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.bollinger import get_latest_bollinger
from app.services.strategies.indicators.rsi import get_latest_rsi


class ScalpReversionStrategy(BaseStrategy):
    """Mean-reversion scalp: complement de scalp_momentum (breakout).

    Achete un retour vers la moyenne quand le prix casse la bande de
    Bollinger basse ET que le RSI confirme un exces de vente (et inversement
    pour la vente). Concu pour les marches en range (ADX faible), ou le
    breakout perd systematiquement (cf. filtre ADX cote swing).
    """

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        bb_period = self.parameters.get("bb_period", 20)
        bb_std = self.parameters.get("bb_std", 2.0)
        rsi_period = self.parameters.get("rsi_period", 14)
        rsi_oversold = self.parameters.get("rsi_oversold", 30)
        rsi_overbought = self.parameters.get("rsi_overbought", 70)

        min_len = max(bb_period, rsi_period) + 1
        if len(candles) < min_len:
            return None

        closes = self.get_closes(candles)
        current_close = closes[-1]

        bb = get_latest_bollinger(closes, bb_period, bb_std)
        if "lower" not in bb or "upper" not in bb:
            return None
        rsi = get_latest_rsi(closes, rsi_period)

        action = None
        if current_close <= bb["lower"] and rsi <= rsi_oversold:
            action = "BUY"
        elif current_close >= bb["upper"] and rsi >= rsi_overbought:
            action = "SELL"

        if not action:
            return None

        band_width = bb["upper"] - bb["lower"]
        distance = abs(current_close - bb["middle"])
        confidence = round(min(distance / band_width, 1.0), 2) if band_width else 0.3

        return {
            "action": action,
            "price": current_close,
            "confidence": max(confidence, 0.3),
            "indicators": {
                "bb_upper": round(bb["upper"], 2),
                "bb_middle": round(bb["middle"], 2),
                "bb_lower": round(bb["lower"], 2),
                "rsi": rsi,
            },
        }
