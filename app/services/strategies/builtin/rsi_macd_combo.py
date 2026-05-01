# app/services/strategies/builtin/rsi_macd_combo.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy
from app.services.strategies.indicators.rsi import get_latest_rsi, calculate_rsi
from app.services.strategies.indicators.macd import calculate_macd
from app.services.strategies.indicators.bollinger import get_latest_bollinger
import pandas as pd


class RSIMACDComboStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        rsi_period = self.parameters.get("rsi_period", 14)
        rsi_oversold = self.parameters.get("rsi_oversold", 35)
        rsi_overbought = self.parameters.get("rsi_overbought", 65)
        fast = self.parameters.get("fast_period", 12)
        slow = self.parameters.get("slow_period", 26)
        signal_p = self.parameters.get("signal_period", 9)
        use_bollinger = self.parameters.get("use_bollinger", True)
        closes = self.get_closes(candles)

        if len(closes) < slow + signal_p + 2:
            return None

        rsi = get_latest_rsi(closes, rsi_period)
        rsi_prev = get_latest_rsi(closes[:-1], rsi_period)
        macd_data = calculate_macd(closes, fast, slow, signal_p)
        macd_line = macd_data["macd"]
        signal_line = macd_data["signal"]

        curr_macd = macd_line[-1]
        prev_macd = macd_line[-2]
        curr_signal = signal_line[-1]
        prev_signal = signal_line[-2]

        if pd.isna(curr_macd) or pd.isna(curr_signal):
            return None

        macd_cross_up = prev_macd <= prev_signal and curr_macd > curr_signal
        macd_cross_down = prev_macd >= prev_signal and curr_macd < curr_signal
        rsi_bullish = rsi < rsi_oversold or (rsi_prev < rsi_oversold and rsi > rsi_oversold)
        rsi_bearish = rsi > rsi_overbought or (rsi_prev > rsi_overbought and rsi < rsi_overbought)

        buy_signals = 0
        sell_signals = 0

        if macd_cross_up:
            buy_signals += 1
        if macd_cross_down:
            sell_signals += 1
        if rsi_bullish:
            buy_signals += 1
        if rsi_bearish:
            sell_signals += 1

        if use_bollinger:
            bollinger = get_latest_bollinger(closes)
            current_price = closes[-1]
            if current_price <= bollinger.get("lower", 0):
                buy_signals += 1
            if current_price >= bollinger.get("upper", float("inf")):
                sell_signals += 1

        action = None
        if buy_signals >= 2:
            action = "BUY"
        elif sell_signals >= 2:
            action = "SELL"

        if not action:
            return None

        total = max(buy_signals, sell_signals)
        max_possible = 3 if use_bollinger else 2
        confidence = round(total / max_possible, 2)

        return {
            "action": action,
            "price": closes[-1],
            "confidence": confidence,
            "indicators": {
                "rsi": rsi,
                "macd": round(float(curr_macd), 6),
                "macd_signal": round(float(curr_signal), 6),
                "macd_cross_up": macd_cross_up,
                "macd_cross_down": macd_cross_down,
                "rsi_bullish": rsi_bullish,
                "rsi_bearish": rsi_bearish,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
            },
        }
