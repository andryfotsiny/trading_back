# app/api/routes/trading/positions.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.execution.order_executor import OrderExecutor
from app.services.exchange.factory import create_exchange

router = APIRouter()


@router.post("/real/buy")
async def real_buy(
    symbol: str = Query(default="BTC/USDT"),
    capital: float = Query(default=1000),
    risk_pct: float = Query(default=0.02),
    sl_pct: float = Query(default=0.01),
    tp_pct: float = Query(default=0.02),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    executor = OrderExecutor(db, current_user.id, capital)
    exchange = create_exchange()
    try:
        ticker = await exchange.get_ticker(symbol)
        price = ticker["last"]
    finally:
        await exchange.close()

    result = await executor.open_trade(
        symbol=symbol,
        side="BUY",
        entry_price=price,
        strategy_name="manual",
        risk_per_trade=risk_pct,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    return result


@router.post("/real/sell")
async def real_sell(
    symbol: str = Query(default="BTC/USDT"),
    capital: float = Query(default=1000),
    risk_pct: float = Query(default=0.02),
    sl_pct: float = Query(default=0.01),
    tp_pct: float = Query(default=0.02),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    executor = OrderExecutor(db, current_user.id, capital)
    exchange = create_exchange()
    try:
        ticker = await exchange.get_ticker(symbol)
        price = ticker["last"]
    finally:
        await exchange.close()

    result = await executor.open_trade(
        symbol=symbol,
        side="SELL",
        entry_price=price,
        strategy_name="manual",
        risk_per_trade=risk_pct,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    return result


@router.get("/real/open-orders")
async def real_open_orders(
    symbol: str = Query(default="BTC/USDT"),
    current_user: User = Depends(get_current_user),
):
    exchange = create_exchange()
    try:
        orders = await exchange.get_open_orders(symbol)
        return orders
    finally:
        await exchange.close()
