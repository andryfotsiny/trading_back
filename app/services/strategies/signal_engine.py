# app/services/strategies/signal_engine.py
from typing import List, Dict, Optional
from app.services.strategies.builtin import STRATEGY_MAP


def run_strategy(strategy_type: str, candles: List[Dict], parameters: Dict = None) -> Optional[Dict]:
    strategy_class = STRATEGY_MAP.get(strategy_type)
    if not strategy_class:
        return None
    strategy = strategy_class(parameters or {})
    return strategy.analyze(candles)


def run_all_strategies(candles: List[Dict], parameters: Dict = None) -> List[Dict]:
    results = []
    for name, strategy_class in STRATEGY_MAP.items():
        strategy = strategy_class(parameters or {})
        signal = strategy.analyze(candles)
        results.append({
            "strategy": name,
            "signal": signal,
        })
    return results
