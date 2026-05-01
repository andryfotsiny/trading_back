# app/services/risk/trailing_stop.py


def calculate_trailing_stop(
    side: str,
    entry_price: float,
    current_price: float,
    current_sl: float,
    trailing_pct: float = 0.02,
) -> dict:
    if side == "BUY":
        new_sl = current_price * (1 - trailing_pct)
        if new_sl > current_sl and current_price > entry_price:
            return {"new_sl": round(new_sl, 6), "updated": True}
    elif side == "SELL":
        new_sl = current_price * (1 + trailing_pct)
        if new_sl < current_sl and current_price < entry_price:
            return {"new_sl": round(new_sl, 6), "updated": True}

    return {"new_sl": current_sl, "updated": False}


def calculate_partial_tp(
    side: str,
    entry_price: float,
    current_price: float,
    take_profit: float,
    partial_levels: list = None,
) -> dict:
    if partial_levels is None:
        partial_levels = [
            {"pct_of_tp": 0.5, "close_pct": 0.5},
            {"pct_of_tp": 1.0, "close_pct": 1.0},
        ]

    if side == "BUY":
        tp_distance = take_profit - entry_price
        current_profit_pct = (current_price - entry_price) / tp_distance if tp_distance > 0 else 0
    else:
        tp_distance = entry_price - take_profit
        current_profit_pct = (entry_price - current_price) / tp_distance if tp_distance > 0 else 0

    for level in partial_levels:
        if current_profit_pct >= level["pct_of_tp"]:
            return {
                "should_close": True,
                "close_pct": level["close_pct"],
                "reason": f"partial_tp_{int(level['pct_of_tp']*100)}",
                "profit_pct": round(current_profit_pct, 4),
            }

    return {"should_close": False, "close_pct": 0, "reason": None, "profit_pct": round(current_profit_pct, 4)}
