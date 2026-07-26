from typing import List, Dict
from app.services.strategies.signal_engine import run_strategy
from app.services.risk.position_sizer import calculate_position_size, calculate_stop_loss, calculate_take_profit
from app.services.risk.trailing_stop import calculate_trailing_stop
from app.services.backtest.performance import calculate_performance
from app.services.bot_runner import calculate_ma50, is_trend_favorable, resolve_risk_levels


class RealisticBacktestEngine:

    def __init__(
        self,
        strategy_type: str,
        initial_capital: float = 1000,
        risk_per_trade: float = 0.02,
        stop_loss_pct: float = 0.01,
        take_profit_pct: float = 0.02,
        parameters: Dict = None,
    ):
        self.strategy_type = strategy_type
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.parameters = parameters or {}
        self.position = None
        self.closed_trades = []

    def run(self, candles: List[Dict]) -> Dict:
        min_candles = 50

        for i in range(min_candles, len(candles)):
            window = candles[:i + 1]
            current = candles[i]
            price = current["close"]

            if self.position:
                self._update_position(price, current)
                continue

            signal = run_strategy(self.strategy_type, window, self.parameters)
            if not signal:
                continue

            ma50 = calculate_ma50(window)
            if not is_trend_favorable(signal["action"], price, ma50):
                continue

            self._open_position(signal, current, window)

        if self.position:
            self._close_position(candles[-1]["close"], "end_of_backtest")

        performance = calculate_performance(self.closed_trades, self.initial_capital)
        performance["trades_detail"] = self.closed_trades
        return performance

    def _open_position(self, signal: Dict, candle: Dict, window: List[Dict]):
        entry_price = signal["price"]
        side = signal["action"]
        sl_pct, tp_pct = resolve_risk_levels(window, self, self.parameters)
        sl = calculate_stop_loss(entry_price, side, sl_pct)
        tp = calculate_take_profit(entry_price, side, tp_pct)
        pos_info = calculate_position_size(self.capital, self.risk_per_trade, entry_price, sl)

        if pos_info["quantity"] <= 0:
            return

        self.position = {
            "side": side,
            "entry_price": entry_price,
            "quantity": pos_info["quantity"],
            "stop_loss": sl,
            "take_profit": tp,
            "risk_amount": pos_info["risk_amount"],
            "risk_pct": abs(entry_price - sl) / entry_price if entry_price else 0.01,
            "timestamp": candle["timestamp"],
        }

    def _update_position(self, price: float, candle: Dict):
        pos = self.position
        trailing_pct = self.parameters.get("trailing_pct", 0.02)
        activation_pct = self.parameters.get("trailing_activation_pct", pos["risk_pct"])
        trailing = calculate_trailing_stop(
            pos["side"], pos["entry_price"], price, pos["stop_loss"], trailing_pct, activation_pct
        )
        if trailing["updated"]:
            pos["stop_loss"] = trailing["new_sl"]

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

        if exit_price is not None:
            self._close_position(exit_price, reason)

    def _close_position(self, exit_price: float, reason: str):
        pos = self.position
        if pos["side"] == "BUY":
            pnl = (exit_price - pos["entry_price"]) * pos["quantity"]
        else:
            pnl = (pos["entry_price"] - exit_price) * pos["quantity"]
        notional = pos["entry_price"] * pos["quantity"]
        pnl_pct = (pnl / notional * 100) if notional else 0

        self.capital += pnl
        self.closed_trades.append({
            "side": pos["side"],
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "quantity": pos["quantity"],
            "pnl": round(pnl, 4),
            "pnl_pct": round(pnl_pct, 2),
            "reason": reason,
        })
        self.position = None
