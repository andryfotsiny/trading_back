# app/services/execution/order_manager.py
from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.models.trade import Trade
from app.db.models.order import Order


def get_open_trades(db: Session, user_id: int) -> List[Dict]:
    trades = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.status == "open",
    ).all()
    return [
        {
            "id": t.id,
            "symbol": t.symbol,
            "side": t.side,
            "entry_price": t.entry_price,
            "quantity": t.quantity,
            "stop_loss": t.stop_loss,
            "take_profit": t.take_profit,
            "strategy_name": t.strategy_name,
            "is_paper": t.is_paper,
            "opened_at": t.opened_at.isoformat() if t.opened_at else None,
        }
        for t in trades
    ]


def get_trade_history(db: Session, user_id: int, limit: int = 50) -> List[Dict]:
    trades = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.status == "closed",
    ).order_by(Trade.closed_at.desc()).limit(limit).all()
    return [
        {
            "id": t.id,
            "symbol": t.symbol,
            "side": t.side,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "quantity": t.quantity,
            "pnl": t.pnl,
            "pnl_pct": t.pnl_pct,
            "strategy_name": t.strategy_name,
            "is_paper": t.is_paper,
            "opened_at": t.opened_at.isoformat() if t.opened_at else None,
            "closed_at": t.closed_at.isoformat() if t.closed_at else None,
        }
        for t in trades
    ]


def get_orders_for_trade(db: Session, trade_id: int) -> List[Dict]:
    orders = db.query(Order).filter(Order.trade_id == trade_id).all()
    return [
        {
            "id": o.id,
            "side": o.side,
            "order_type": o.order_type,
            "quantity": o.quantity,
            "price": o.price,
            "status": o.status,
            "filled_price": o.filled_price,
            "executed_at": o.executed_at.isoformat() if o.executed_at else None,
        }
        for o in orders
    ]
