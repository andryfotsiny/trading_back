# app/services/risk/stop_loss.py
from typing import Dict, Optional


def check_stop_loss(current_price: float, entry_price: float, stop_loss_price: float, side: str) -> bool:
    if side == "BUY":
        return current_price <= stop_loss_price
    return current_price >= stop_loss_price


def check_take_profit(current_price: float, entry_price: float, take_profit_price: float, side: str) -> bool:
    if side == "BUY":
        return current_price >= take_profit_price
    return current_price <= take_profit_price


def check_trade_exit(
    current_price: float,
    entry_price: float,
    side: str,
    stop_loss_price: float,
    take_profit_price: float,
) -> Optional[Dict]:
    if check_stop_loss(current_price, entry_price, stop_loss_price, side):
        pnl = (stop_loss_price - entry_price) * (1 if side == "BUY" else -1)
        return {
            "exit_reason": "stop_loss",
            "exit_price": stop_loss_price,
            "pnl_per_unit": round(pnl, 8),
        }
    if check_take_profit(current_price, entry_price, take_profit_price, side):
        pnl = (take_profit_price - entry_price) * (1 if side == "BUY" else -1)
        return {
            "exit_reason": "take_profit",
            "exit_price": take_profit_price,
            "pnl_per_unit": round(pnl, 8),
        }
    return None
