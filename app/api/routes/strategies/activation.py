# app/api/routes/strategies/activation.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.strategy import Strategy
from app.core.dependencies import get_current_user
from app.services.strategies.strategy_runner import execute_strategy, run_active_strategies
from app.services.strategies.signal_engine import run_strategy, run_all_strategies
from app.services.exchange.factory import create_exchange

router = APIRouter()


@router.post("/{strategy_id}/activate")
def activate_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategie non trouvee")
    strategy.is_active = True
    db.commit()
    return {"detail": f"{strategy.name} activee"}


@router.post("/{strategy_id}/deactivate")
def deactivate_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategie non trouvee")
    strategy.is_active = False
    db.commit()
    return {"detail": f"{strategy.name} desactivee"}


@router.post("/{strategy_id}/run")
async def run_single_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategie non trouvee")
    result = await execute_strategy(db, strategy)
    return {"strategy": strategy.name, "result": result or "Aucun signal"}


@router.post("/run-all")
async def run_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = await run_active_strategies(db)
    return {"results": results}


@router.post("/test/{strategy_type}/{base}/{quote}")
async def test_strategy(
    strategy_type: str,
    base: str,
    quote: str,
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    exchange = create_exchange()
    try:
        candles = await exchange.get_ohlcv(symbol, "1h", 100)
    finally:
        await exchange.close()
    result = run_strategy(strategy_type, candles)
    return {"strategy": strategy_type, "symbol": symbol, "signal": result or "Aucun signal"}


@router.post("/test-all/{base}/{quote}")
async def test_all_strategies(
    base: str,
    quote: str,
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    exchange = create_exchange()
    try:
        candles = await exchange.get_ohlcv(symbol, "1h", 100)
    finally:
        await exchange.close()
    results = run_all_strategies(candles)
    return {"symbol": symbol, "results": results}
