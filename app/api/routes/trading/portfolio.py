# app/api/routes/trading/portfolio.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.risk.risk_manager import RiskManager
from app.services.risk.position_sizer import calculate_position_size, calculate_stop_loss, calculate_take_profit

router = APIRouter()


@router.get("/risk-check")
def risk_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rm = RiskManager(capital=1000)
    check = rm.can_open_trade(db, current_user.id)
    return check


@router.get("/risk-summary")
def risk_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rm = RiskManager(capital=1000)
    return rm.get_risk_summary(db, current_user.id)


@router.get("/simulate-trade")
def simulate_trade(
    price: float = Query(...),
    side: str = Query(default="BUY"),
    capital: float = Query(default=1000),
    risk_pct: float = Query(default=0.02),
    sl_pct: float = Query(default=0.01),
    tp_pct: float = Query(default=0.02),
    current_user: User = Depends(get_current_user),
):
    rm = RiskManager(
        capital=capital,
        risk_per_trade=risk_pct,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    return rm.prepare_trade(price, side)
