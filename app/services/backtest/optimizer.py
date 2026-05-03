# app/services/backtest/optimizer.py
from typing import List, Dict
from app.services.backtest.engine import BacktestEngine
from app.services.strategies.builtin import STRATEGY_MAP


def optimize_strategy(
    strategy_type: str,
    candles: List[Dict],
    capital: float = 1000,
    sl_values: List[float] = None,
    tp_values: List[float] = None,
    risk_values: List[float] = None,
) -> List[Dict]:
    sl_range = sl_values or [0.01, 0.015, 0.02, 0.025, 0.03, 0.04]
    tp_range = tp_values or [0.02, 0.03, 0.04, 0.05, 0.06, 0.08]
    risk_range = risk_values or [0.02]

    results = []
    for sl in sl_range:
        for tp in tp_range:
            if tp <= sl:
                continue
            for risk in risk_range:
                engine = BacktestEngine(
                    strategy_type=strategy_type,
                    initial_capital=capital,
                    risk_per_trade=risk,
                    stop_loss_pct=sl,
                    take_profit_pct=tp,
                )
                result = engine.run(candles)
                if result["total_trades"] > 0:
                    results.append({
                        "strategy": strategy_type,
                        "sl_pct": sl,
                        "tp_pct": tp,
                        "risk_pct": risk,
                        "total_trades": result["total_trades"],
                        "winning_trades": result["winning_trades"],
                        "losing_trades": result["losing_trades"],
                        "win_rate": result["win_rate"],
                        "total_pnl": result["total_pnl"],
                        "final_capital": result["final_capital"],
                        "max_drawdown": result["max_drawdown"],
                        "sharpe_ratio": result.get("sharpe_ratio"),
                        "profit_factor": result.get("profit_factor", 0),
                    })

    results.sort(key=lambda x: x["total_pnl"], reverse=True)
    return results


def optimize_all_strategies(
    candles: List[Dict],
    capital: float = 1000,
    sl_values: List[float] = None,
    tp_values: List[float] = None,
) -> List[Dict]:
    all_results = []
    for strategy_type in STRATEGY_MAP.keys():
        results = optimize_strategy(strategy_type, candles, capital, sl_values, tp_values)
        all_results.extend(results)

    all_results.sort(key=lambda x: x["total_pnl"], reverse=True)
    return all_results
