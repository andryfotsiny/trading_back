# app/services/risk/position_sizer.py
from typing import Dict


def calculate_position_size(
    capital: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss_price: float,
) -> Dict:
    risk_amount = capital * risk_per_trade
    price_diff = abs(entry_price - stop_loss_price)
    if price_diff == 0:
        return {"quantity": 0, "risk_amount": 0, "position_value": 0}
    quantity = risk_amount / price_diff
    position_value = quantity * entry_price
    return {
        "quantity": round(quantity, 8),
        "risk_amount": round(risk_amount, 2),
        "position_value": round(position_value, 2),
        "entry_price": entry_price,
        "stop_loss_price": stop_loss_price,
        "risk_pct": risk_per_trade,
    }


def calculate_stop_loss(entry_price: float, side: str, stop_loss_pct: float) -> float:
    if side == "BUY":
        return round(entry_price * (1 - stop_loss_pct), 8)
    return round(entry_price * (1 + stop_loss_pct), 8)


def calculate_take_profit(entry_price: float, side: str, take_profit_pct: float) -> float:
    if side == "BUY":
        return round(entry_price * (1 + take_profit_pct), 8)
    return round(entry_price * (1 - take_profit_pct), 8)
