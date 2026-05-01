# app/services/backtest/performance.py
from typing import List, Dict
import math


def calculate_performance(trades: List[Dict], initial_capital: float) -> Dict:
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "total_pnl_pct": 0,
            "final_capital": initial_capital,
            "max_drawdown": 0,
            "sharpe_ratio": None,
            "avg_win": 0,
            "avg_loss": 0,
            "profit_factor": 0,
        }

    winning = [t for t in trades if t["pnl"] > 0]
    losing = [t for t in trades if t["pnl"] < 0]
    total_pnl = sum(t["pnl"] for t in trades)
    final_capital = initial_capital + total_pnl

    gross_profit = sum(t["pnl"] for t in winning) if winning else 0
    gross_loss = abs(sum(t["pnl"] for t in losing)) if losing else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    capital_curve = [initial_capital]
    for t in trades:
        capital_curve.append(capital_curve[-1] + t["pnl"])

    peak = initial_capital
    max_dd = 0
    for val in capital_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        if dd > max_dd:
            max_dd = dd

    returns = [t["pnl"] / initial_capital for t in trades]
    avg_return = sum(returns) / len(returns) if returns else 0
    std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 0
    sharpe = (avg_return / std_return * math.sqrt(252)) if std_return > 0 else None

    return {
        "total_trades": len(trades),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "win_rate": round(len(winning) / len(trades), 4),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl / initial_capital * 100, 2),
        "final_capital": round(final_capital, 2),
        "max_drawdown": round(max_dd, 4),
        "sharpe_ratio": round(sharpe, 4) if sharpe else None,
        "avg_win": round(gross_profit / len(winning), 2) if winning else 0,
        "avg_loss": round(gross_loss / len(losing), 2) if losing else 0,
        "profit_factor": round(profit_factor, 2),
    }
