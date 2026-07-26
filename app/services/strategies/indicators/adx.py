from typing import List, Dict
from app.services.strategies.indicators.atr import calculate_true_ranges


def _wilder_smooth(values: List[float], period: int) -> List[float]:
    if len(values) < period:
        return []
    smoothed = [sum(values[:period])]
    for v in values[period:]:
        smoothed.append(smoothed[-1] - smoothed[-1] / period + v)
    return smoothed


def calculate_adx(candles: List[Dict], period: int = 14) -> Dict[str, float]:
    if len(candles) < period * 2 + 1:
        return {"adx": 0.0, "plus_di": 0.0, "minus_di": 0.0}

    plus_dm = []
    minus_dm = []
    for i in range(1, len(candles)):
        up_move = candles[i]["high"] - candles[i - 1]["high"]
        down_move = candles[i - 1]["low"] - candles[i]["low"]
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)

    tr = calculate_true_ranges(candles)

    smoothed_tr = _wilder_smooth(tr, period)
    smoothed_plus_dm = _wilder_smooth(plus_dm, period)
    smoothed_minus_dm = _wilder_smooth(minus_dm, period)

    if not smoothed_tr or not smoothed_plus_dm or not smoothed_minus_dm:
        return {"adx": 0.0, "plus_di": 0.0, "minus_di": 0.0}

    dx_values = []
    for i in range(len(smoothed_tr)):
        if smoothed_tr[i] == 0:
            dx_values.append(0.0)
            continue
        plus_di = 100 * smoothed_plus_dm[i] / smoothed_tr[i]
        minus_di = 100 * smoothed_minus_dm[i] / smoothed_tr[i]
        di_sum = plus_di + minus_di
        dx = 100 * abs(plus_di - minus_di) / di_sum if di_sum > 0 else 0.0
        dx_values.append(dx)

    if len(dx_values) < period:
        return {"adx": 0.0, "plus_di": 0.0, "minus_di": 0.0}

    adx = sum(dx_values[:period]) / period
    for dx in dx_values[period:]:
        adx = (adx * (period - 1) + dx) / period

    last_plus_di = 100 * smoothed_plus_dm[-1] / smoothed_tr[-1] if smoothed_tr[-1] > 0 else 0.0
    last_minus_di = 100 * smoothed_minus_dm[-1] / smoothed_tr[-1] if smoothed_tr[-1] > 0 else 0.0

    return {
        "adx": round(adx, 4),
        "plus_di": round(last_plus_di, 4),
        "minus_di": round(last_minus_di, 4),
    }


def get_latest_adx(candles: List[Dict], period: int = 14) -> float:
    return calculate_adx(candles, period)["adx"]
