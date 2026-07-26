# app/api/routes/backtest/run.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.db.models.user import User
from app.db.models.strategy import Strategy
from app.db.models.backtest_result import BacktestResult
from app.core.dependencies import get_current_user
from app.services.backtest.engine import BacktestEngine
from app.services.backtest.data_loader import load_from_exchange
from app.services.strategies.builtin import STRATEGY_MAP
from app.services.strategies.timeframe import resolve_timeframe
from app.services.exchange.factory import create_exchange
import logging

router = APIRouter()
logger = logging.getLogger("backtest_route")


@router.post("/run/{strategy_type}/{base}/{quote}")
async def run_backtest(
    strategy_type: str,
    base: str,
    quote: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=500, le=1000),
    capital: float = Query(default=1000),
    risk_pct: float = Query(default=0.02),
    sl_pct: float = Query(default=0.01),
    tp_pct: float = Query(default=0.02),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if strategy_type not in STRATEGY_MAP:
        return {"error": f"Type inconnu. Disponibles: {list(STRATEGY_MAP.keys())}"}

    symbol = f"{base.upper()}/{quote.upper()}"
    candles = await load_from_exchange(symbol, timeframe, limit)

    if len(candles) < 50:
        return {"error": "Pas assez de donnees (minimum 50 candles)"}

    engine = BacktestEngine(
        strategy_type=strategy_type,
        initial_capital=capital,
        risk_per_trade=risk_pct,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    result = engine.run(candles)

    start_dt = datetime.fromtimestamp(candles[0]["timestamp"] / 1000, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(candles[-1]["timestamp"] / 1000, tz=timezone.utc)

    bt = BacktestResult(
        user_id=current_user.id,
        strategy_type=strategy_type,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_dt,
        end_date=end_dt,
        initial_capital=capital,
        final_capital=result["final_capital"],
        total_trades=result["total_trades"],
        winning_trades=result["winning_trades"],
        losing_trades=result["losing_trades"],
        win_rate=result["win_rate"],
        total_pnl=result["total_pnl"],
        max_drawdown=result["max_drawdown"],
        sharpe_ratio=result.get("sharpe_ratio"),
        parameters={"risk_pct": risk_pct, "sl_pct": sl_pct, "tp_pct": tp_pct},
        trades_detail=result["trades_detail"],
    )
    db.add(bt)
    db.commit()
    db.refresh(bt)

    result["backtest_id"] = bt.id
    result["symbol"] = symbol
    result["strategy_type"] = strategy_type
    return result


def _save_backtest(db, user_id, strategy_type, symbol, timeframe, candles, capital, risk_pct, sl_pct, tp_pct, parameters):
    engine = BacktestEngine(
        strategy_type=strategy_type,
        initial_capital=capital,
        risk_per_trade=risk_pct,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
        parameters=parameters,
    )
    result = engine.run(candles)

    start_dt = datetime.fromtimestamp(candles[0]["timestamp"] / 1000, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(candles[-1]["timestamp"] / 1000, tz=timezone.utc)

    bt = BacktestResult(
        user_id=user_id,
        strategy_type=strategy_type,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_dt,
        end_date=end_dt,
        initial_capital=capital,
        final_capital=result["final_capital"],
        total_trades=result["total_trades"],
        winning_trades=result["winning_trades"],
        losing_trades=result["losing_trades"],
        win_rate=result["win_rate"],
        total_pnl=result["total_pnl"],
        max_drawdown=result["max_drawdown"],
        sharpe_ratio=result.get("sharpe_ratio"),
        parameters={"risk_pct": risk_pct, "sl_pct": sl_pct, "tp_pct": tp_pct},
        trades_detail=result["trades_detail"],
    )
    db.add(bt)
    db.commit()


async def run_all_backtests(user_id: int, symbol: str, limit: int, capital: float):
    db = SessionLocal()
    try:
        strategies = db.query(Strategy).filter(
            Strategy.user_id == user_id,
            Strategy.is_active == True,
        ).all()

        exchange = create_exchange()
        try:
            for strategy in strategies:
                try:
                    timeframe = await resolve_timeframe(exchange, strategy)
                    candles = await load_from_exchange(symbol, timeframe, limit)
                    if len(candles) < 50:
                        logger.warning(f"Pas assez de candles pour {strategy.name} ({timeframe})")
                        continue
                    _save_backtest(
                        db, user_id, strategy.strategy_type, symbol, timeframe, candles, capital,
                        strategy.risk_per_trade, strategy.stop_loss_pct, strategy.take_profit_pct,
                        strategy.parameters,
                    )
                    logger.info(f"OK {strategy.name} ({timeframe})")
                except Exception as e:
                    logger.error(f"Erreur backtest {strategy.name}: {e}")
                    continue
        finally:
            await exchange.close()
    finally:
        db.close()


@router.post("/run-all/{base}/{quote}")
async def run_backtest_all(
    base: str,
    quote: str,
    background_tasks: BackgroundTasks,
    limit: int = Query(default=500, le=1000),
    capital: float = Query(default=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    strategies = db.query(Strategy).filter(
        Strategy.user_id == current_user.id,
        Strategy.is_active == True,
    ).all()
    if not strategies:
        return {"error": "Aucune strategie active"}

    background_tasks.add_task(run_all_backtests, current_user.id, symbol, limit, capital)
    return {"status": "started", "symbol": symbol, "strategies_count": len(strategies)}