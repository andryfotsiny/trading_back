# app/api/routes/backtest/run.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.backtest_result import BacktestResult
from app.core.dependencies import get_current_user
from app.services.backtest.engine import BacktestEngine
from app.services.backtest.data_loader import load_from_exchange
from app.services.strategies.builtin import STRATEGY_MAP

router = APIRouter()


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