# app/api/routes/strategies/crud.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.strategy import Strategy
from app.core.dependencies import get_current_user
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse
from app.services.strategies.builtin import STRATEGY_MAP

router = APIRouter()


@router.get("/types")
def list_strategy_types():
    return {"available": list(STRATEGY_MAP.keys())}


@router.post("/", response_model=StrategyResponse, status_code=201)
def create_strategy(
    data: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.strategy_type not in STRATEGY_MAP:
        raise HTTPException(status_code=400, detail=f"Type inconnu. Disponibles: {list(STRATEGY_MAP.keys())}")
    strategy = Strategy(
        user_id=current_user.id,
        name=data.name,
        strategy_type=data.strategy_type,
        symbol=data.symbol,
        timeframe=data.timeframe,
        parameters=data.parameters,
        risk_per_trade=data.risk_per_trade,
        stop_loss_pct=data.stop_loss_pct,
        take_profit_pct=data.take_profit_pct,
        max_open_trades=data.max_open_trades,
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


@router.get("/", response_model=List[StrategyResponse])
def list_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Strategy).filter(Strategy.user_id == current_user.id).all()


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategie non trouvee")
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy(
    strategy_id: int,
    data: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategie non trouvee")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(strategy, key, value)
    db.commit()
    db.refresh(strategy)
    return strategy


@router.delete("/{strategy_id}")
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategie non trouvee")
    db.delete(strategy)
    db.commit()
    return {"detail": "Supprimee"}
