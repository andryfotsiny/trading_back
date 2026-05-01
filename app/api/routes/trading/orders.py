# app/api/routes/trading/orders.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.trade import Trade
from app.core.dependencies import get_current_user
from app.services.execution.paper_executor import PaperExecutor
from app.services.execution.order_manager import get_open_trades, get_trade_history, get_orders_for_trade
from app.services.exchange.factory import create_exchange

router = APIRouter()


@router.post("/open")
async def open_paper_trade(
    symbol: str = Query(...),
    side: str = Query(default="BUY"),
    strategy_name: str = Query(default=None),
    capital: float = Query(default=1000),
    risk_pct: float = Query(default=0.02),
    sl_pct: float = Query(default=0.01),
    tp_pct: float = Query(default=0.02),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exchange = create_exchange()
    try:
        ticker = await exchange.get_ticker(symbol)
        price = ticker["last"]
    finally:
        await exchange.close()

    executor = PaperExecutor(db, current_user.id, capital)
    result = executor.open_trade(
        symbol=symbol,
        side=side,
        entry_price=price,
        strategy_name=strategy_name,
        risk_per_trade=risk_pct,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    return result


@router.post("/close/{trade_id}")
async def close_paper_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade_obj = db.query(Trade).filter_by(id=trade_id, user_id=current_user.id).first()
    if not trade_obj:
        return {"error": "Trade non trouve"}

    exchange = create_exchange()
    try:
        ticker = await exchange.get_ticker(trade_obj.symbol)
        price = ticker["last"]
    finally:
        await exchange.close()

    executor = PaperExecutor(db, current_user.id)
    return executor.close_trade(trade_id, price, reason="manual")


@router.post("/check-exits")
async def check_exits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    open_trades = db.query(Trade).filter(
        Trade.user_id == current_user.id,
        Trade.status == "open",
    ).all()

    if not open_trades:
        return {"message": "Aucun trade ouvert", "closed": []}

    symbols = list(set(t.symbol for t in open_trades))
    exchange = create_exchange()
    try:
        prices = {}
        for s in symbols:
            ticker = await exchange.get_ticker(s)
            prices[s] = ticker["last"]
    finally:
        await exchange.close()

    executor = PaperExecutor(db, current_user.id)
    closed = executor.check_open_trades(prices)
    return {"prices": prices, "closed": closed}


@router.get("/open-trades")
def list_open_trades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_open_trades(db, current_user.id)


@router.get("/history")
def trade_history(
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_trade_history(db, current_user.id, limit)


@router.get("/orders/{trade_id}")
def trade_orders(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_orders_for_trade(db, trade_id)
