# app/api/routes/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.trade import Trade
from app.db.models.strategy import Strategy
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    open_trades = db.query(Trade).filter(Trade.user_id == current_user.id, Trade.status == "open").count()
    closed_trades = db.query(Trade).filter(Trade.user_id == current_user.id, Trade.status == "closed").all()
    active_strategies = db.query(Strategy).filter(Strategy.user_id == current_user.id, Strategy.is_active == True).count()
    total_strategies = db.query(Strategy).filter(Strategy.user_id == current_user.id).count()

    total_pnl = sum(t.pnl or 0 for t in closed_trades)
    tp_trades = [t for t in closed_trades if (t.pnl or 0) > 0]
    sl_trades = [t for t in closed_trades if (t.pnl or 0) < 0]
    win_rate = len(tp_trades) / len(closed_trades) if closed_trades else 0

    return {
        "open_trades": open_trades,
        "closed_trades": len(closed_trades),
        "total_pnl": round(total_pnl, 4),
        "win_rate": round(win_rate, 4),
        "tp_count": len(tp_trades),
        "sl_count": len(sl_trades),
        "active_strategies": active_strategies,
        "total_strategies": total_strategies,
    }


@router.get("/strategy-stats")
def get_strategy_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    closed = db.query(Trade).filter(
        Trade.user_id == current_user.id,
        Trade.status == "closed",
        Trade.strategy_name.isnot(None),
    ).all()

    stats = {}
    for trade in closed:
        name = trade.strategy_name
        if name not in stats:
            stats[name] = {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0, "trades": []}
        stats[name]["total"] += 1
        stats[name]["pnl"] += trade.pnl or 0
        if (trade.pnl or 0) > 0:
            stats[name]["wins"] += 1
        else:
            stats[name]["losses"] += 1
        stats[name]["trades"].append({
            "id": trade.id,
            "side": trade.side,
            "entry": trade.entry_price,
            "exit": trade.exit_price,
            "pnl": trade.pnl,
            "symbol": trade.symbol,
        })

    result = []
    for name, data in stats.items():
        win_rate = data["wins"] / data["total"] if data["total"] > 0 else 0
        result.append({
            "strategy": name,
            "total_trades": data["total"],
            "wins": data["wins"],
            "losses": data["losses"],
            "win_rate": round(win_rate, 4),
            "total_pnl": round(data["pnl"], 4),
            "avg_pnl": round(data["pnl"] / data["total"], 4) if data["total"] > 0 else 0,
        })

    result.sort(key=lambda x: x["win_rate"], reverse=True)
    return result
