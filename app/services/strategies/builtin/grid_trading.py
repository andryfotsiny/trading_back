# app/services/strategies/builtin/grid_trading.py
from typing import List, Dict, Optional
from app.services.strategies.base_strategy import BaseStrategy


class GridTradingStrategy(BaseStrategy):

    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        grid_levels = self.parameters.get("grid_levels", 10)
        grid_range_pct = self.parameters.get("grid_range_pct", 0.05)
        closes = self.get_closes(candles)

        if len(closes) < 20:
            return None

        current_price = closes[-1]
        recent_high = max(closes[-20:])
        recent_low = min(closes[-20:])
        mid_price = (recent_high + recent_low) / 2
        grid_upper = mid_price * (1 + grid_range_pct)
        grid_lower = mid_price * (1 - grid_range_pct)
        grid_step = (grid_upper - grid_lower) / grid_levels

        prev_price = closes[-2]
        action = None

        for i in range(grid_levels + 1):
            level = grid_lower + (i * grid_step)
            if prev_price > level and current_price <= level:
                action = "BUY"
                break
            if prev_price < level and current_price >= level:
                action = "SELL"
                break

        if not action:
            return None

        distance_from_mid = abs(current_price - mid_price) / mid_price
        confidence = round(min(distance_from_mid * 10, 1.0), 2)

        return {
            "action": action,
            "price": current_price,
            "confidence": max(confidence, 0.3),
            "indicators": {
                "grid_upper": round(grid_upper, 2),
                "grid_lower": round(grid_lower, 2),
                "grid_step": round(grid_step, 2),
                "mid_price": round(mid_price, 2),
                "levels": grid_levels,
            },
        }
