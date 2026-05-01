# app/api/routes/backtest/results.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.backtest_result import BacktestResult
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("/")
def list_backtests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = db.query(BacktestResult).filter(
        BacktestResult.user_id == current_user.id
    ).order_by(BacktestResult.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "strategy_type": r.strategy_type,
            "symbol": r.symbol,
            "timeframe": r.timeframe,
            "initial_capital": r.initial_capital,
            "final_capital": r.final_capital,
            "total_trades": r.total_trades,
            "winning_trades": r.winning_trades,
            "losing_trades": r.losing_trades,
            "win_rate": r.win_rate,
            "total_pnl": r.total_pnl,
            "max_drawdown": r.max_drawdown,
            "sharpe_ratio": r.sharpe_ratio,
            "parameters": r.parameters or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in results
    ]


@router.get("/{backtest_id}")
def get_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bt = db.query(BacktestResult).filter(
        BacktestResult.id == backtest_id,
        BacktestResult.user_id == current_user.id,
    ).first()
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest non trouve")
    return {
        "id": bt.id,
        "strategy_type": bt.strategy_type,
        "symbol": bt.symbol,
        "timeframe": bt.timeframe,
        "initial_capital": bt.initial_capital,
        "final_capital": bt.final_capital,
        "total_trades": bt.total_trades,
        "winning_trades": bt.winning_trades,
        "losing_trades": bt.losing_trades,
        "win_rate": bt.win_rate,
        "total_pnl": bt.total_pnl,
        "max_drawdown": bt.max_drawdown,
        "sharpe_ratio": bt.sharpe_ratio,
        "parameters": bt.parameters or {},
        "trades_detail": bt.trades_detail,
        "created_at": bt.created_at.isoformat() if bt.created_at else None,
    }


@router.delete("/{backtest_id}")
def delete_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bt = db.query(BacktestResult).filter(
        BacktestResult.id == backtest_id,
        BacktestResult.user_id == current_user.id,
    ).first()
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest non trouve")
    db.delete(bt)
    db.commit()
    return {"detail": "Supprime"}
