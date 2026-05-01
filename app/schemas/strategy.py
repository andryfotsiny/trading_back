# app/schemas/strategy.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class StrategyCreate(BaseModel):
    name: str
    strategy_type: str
    symbol: str
    timeframe: str = "1h"
    parameters: Dict[str, Any] = {}
    risk_per_trade: float = 0.02
    stop_loss_pct: float = 0.01
    take_profit_pct: float = 0.02
    max_open_trades: int = 3


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    risk_per_trade: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    max_open_trades: Optional[int] = None
    is_active: Optional[bool] = None


class StrategyResponse(BaseModel):
    id: int
    name: str
    strategy_type: str
    symbol: str
    timeframe: str
    parameters: Dict[str, Any]
    risk_per_trade: float
    stop_loss_pct: float
    take_profit_pct: float
    max_open_trades: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
