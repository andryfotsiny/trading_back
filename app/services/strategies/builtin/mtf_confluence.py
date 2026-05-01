# app/services/strategies/builtin/mtf_confluence.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.rsi import get_latest_rsi
from app.services.strategies.indicators.macd import calculate_macd
from app.services.strategies.indicators.moving_average import get_latest_sma, get_latest_ema
import pandas as pd


class MTFConfluenceStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        closes = self.get_closes(candles)
        if len(closes) < 60:
            return None

        htf_closes = closes[::4] if len(closes) >= 100 else closes[::2]
        ltf_closes = closes

        htf_sma_fast = get_latest_sma(htf_closes, 10)
        htf_sma_slow = get_latest_sma(htf_closes, 20)
        htf_trend = "bullish" if htf_sma_fast > htf_sma_slow else "bearish"

        htf_ema = get_latest_ema(htf_closes, 20)
        htf_price = htf_closes[-1]
        htf_above_ema = htf_price > htf_ema

        ltf_rsi = get_latest_rsi(ltf_closes)
        ltf_rsi_prev = get_latest_rsi(ltf_closes[:-1])
        macd_data = calculate_macd(ltf_closes, 12, 26, 9)
        macd_line = macd_data["macd"]
        signal_line = macd_data["signal"]

        if pd.isna(macd_line[-1]) or pd.isna(signal_line[-1]):
            return None

        macd_cross_up = macd_line[-2] <= signal_line[-2] and macd_line[-1] > signal_line[-1]
        macd_cross_down = macd_line[-2] >= signal_line[-2] and macd_line[-1] < signal_line[-1]
        rsi_oversold_exit = ltf_rsi_prev < 35 and ltf_rsi > 35
        rsi_overbought_exit = ltf_rsi_prev > 65 and ltf_rsi < 65

        action = None
        confidence = 0

        if htf_trend == "bullish" and htf_above_ema:
            signals = 0
            if macd_cross_up:
                signals += 1
            if rsi_oversold_exit:
                signals += 1
            if ltf_rsi < 45:
                signals += 1
            if signals >= 2:
                action = "BUY"
                confidence = round(0.4 + (signals * 0.15), 2)

        elif htf_trend == "bearish" and not htf_above_ema:
            signals = 0
            if macd_cross_down:
                signals += 1
            if rsi_overbought_exit:
                signals += 1
            if ltf_rsi > 55:
                signals += 1
            if signals >= 2:
                action = "SELL"
                confidence = round(0.4 + (signals * 0.15), 2)

        if not action:
            return None

        return {
            "action": action,
            "price": closes[-1],
            "confidence": min(confidence, 0.95),
            "indicators": {
                "htf_trend": htf_trend,
                "htf_above_ema": htf_above_ema,
                "ltf_rsi": ltf_rsi,
                "ltf_macd_cross_up": macd_cross_up,
                "ltf_macd_cross_down": macd_cross_down,
            },
        }
