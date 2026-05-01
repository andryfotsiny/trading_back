# app/services/backtest/engine.py
from typing import List, Dict, Optional
from app.services.strategies.signal_engine import run_strategy
from app.services.risk.position_sizer import calculate_position_size, calculate_stop_loss, calculate_take_profit
from app.services.backtest.performance import calculate_performance


class BacktestEngine:

    def __init__(
        self,
        strategy_type: str,
        initial_capital: float = 1000,
        risk_per_trade: float = 0.02,
        stop_loss_pct: float = 0.01,
        take_profit_pct: float = 0.02,
        max_open_trades: int = 3,
        parameters: Dict = None,
    ):
        self.strategy_type = strategy_type
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_open_trades = max_open_trades
        self.parameters = parameters or {}
        self.open_positions = []
        self.closed_trades = []

    def run(self, candles: List[Dict]) -> Dict:
        min_candles = 50

        for i in range(min_candles, len(candles)):
            window = candles[:i + 1]
            current = candles[i]
            price = current["close"]

            self._check_exits(price, current)

            if len(self.open_positions) >= self.max_open_trades:
                continue

            signal = run_strategy(self.strategy_type, window, self.parameters)
            if not signal:
                continue

            self._open_position(signal, current)

        for pos in list(self.open_positions):
            last_price = candles[-1]["close"]
            self._close_position(pos, last_price, "end_of_backtest")

        performance = calculate_performance(self.closed_trades, self.initial_capital)
        performance["trades_detail"] = self.closed_trades
        return performance

    def _open_position(self, signal: Dict, candle: Dict):
        entry_price = signal["price"]
        side = signal["action"]
        sl = calculate_stop_loss(entry_price, side, self.stop_loss_pct)
        tp = calculate_take_profit(entry_price, side, self.take_profit_pct)
        pos_info = calculate_position_size(self.capital, self.risk_per_trade, entry_price, sl)

        if pos_info["quantity"] <= 0:
            return

        position = {
            "side": side,
            "entry_price": entry_price,
            "quantity": pos_info["quantity"],
            "stop_loss": sl,
            "take_profit": tp,
            "risk_amount": pos_info["risk_amount"],
            "timestamp": candle["timestamp"],
        }
        self.open_positions.append(position)

    def _check_exits(self, current_price: float, candle: Dict):
        for pos in list(self.open_positions):
            exit_price = None
            reason = None

            if pos["side"] == "BUY":
                if candle["low"] <= pos["stop_loss"]:
                    exit_price = pos["stop_loss"]
                    reason = "stop_loss"
                elif candle["high"] >= pos["take_profit"]:
                    exit_price = pos["take_profit"]
                    reason = "take_profit"
            else:
                if candle["high"] >= pos["stop_loss"]:
                    exit_price = pos["stop_loss"]
                    reason = "stop_loss"
                elif candle["low"] <= pos["take_profit"]:
                    exit_price = pos["take_profit"]
                    reason = "take_profit"

            if exit_price:
                self._close_position(pos, exit_price, reason)

    def _close_position(self, position: Dict, exit_price: float, reason: str):
        if position not in self.open_positions:
            return
        self.open_positions.remove(position)

        if position["side"] == "BUY":
            pnl = (exit_price - position["entry_price"]) * position["quantity"]
        else:
            pnl = (position["entry_price"] - exit_price) * position["quantity"]

        pnl_pct = pnl / (position["entry_price"] * position["quantity"]) * 100
        self.capital += pnl

        self.closed_trades.append({
            "side": position["side"],
            "entry_price": position["entry_price"],
            "exit_price": round(exit_price, 2),
            "quantity": position["quantity"],
            "pnl": round(pnl, 4),
            "pnl_pct": round(pnl_pct, 2),
            "reason": reason,
        })
