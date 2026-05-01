# app/services/strategies/strategy_runner.py
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.db.models.strategy import Strategy
from app.db.models.signal import Signal
from app.services.exchange.factory import create_exchange
from app.services.strategies.signal_engine import run_strategy


async def execute_strategy(db: Session, strategy: Strategy) -> Optional[Dict]:
    exchange = create_exchange()
    try:
        candles = await exchange.get_ohlcv(strategy.symbol, strategy.timeframe, 100)
    finally:
        await exchange.close()

    result = run_strategy(strategy.strategy_type, candles, strategy.parameters)

    if result:
        signal = Signal(
            strategy_id=strategy.id,
            symbol=strategy.symbol,
            action=result["action"],
            price=result["price"],
            confidence=result["confidence"],
            indicators=result["indicators"],
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)
        return {
            "strategy": strategy.name,
            "signal_id": signal.id,
            "action": result["action"],
            "price": result["price"],
            "confidence": result["confidence"],
            "indicators": result["indicators"],
        }

    return None


async def run_active_strategies(db: Session) -> list:
    strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
    results = []
    for strategy in strategies:
        result = await execute_strategy(db, strategy)
        results.append({
            "strategy": strategy.name,
            "symbol": strategy.symbol,
            "result": result,
        })
    return results
