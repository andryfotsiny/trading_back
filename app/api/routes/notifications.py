# app/api/routes/notifications.py
from fastapi import APIRouter, Depends, Query
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.notifications.telegram_notifier import notifier

router = APIRouter()


@router.post("/test")
async def test_notification(
    message: str = Query(default="Test du bot trading!"),
    current_user: User = Depends(get_current_user),
):
    result = await notifier.send_message(f"🤖 {message}")
    return result


@router.post("/test-signal")
async def test_signal_notification(
    current_user: User = Depends(get_current_user),
):
    result = await notifier.notify_signal(
        symbol="BTC/USDT",
        action="BUY",
        price=66300.0,
        strategy="sma_crossover",
        confidence=0.85,
    )
    return result


@router.post("/test-trade")
async def test_trade_notification(
    current_user: User = Depends(get_current_user),
):
    result = await notifier.notify_trade_open(
        symbol="BTC/USDT",
        side="BUY",
        price=66300.0,
        quantity=0.03,
        sl=65637.0,
        tp=67626.0,
    )
    return result
