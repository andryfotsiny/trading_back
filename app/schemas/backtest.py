# app/schemas/backtest.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class BacktestRequest(BaseModel):
    strategy_type: str
    symbol: str
    timeframe: str = "1h"
    start_date: datetime
    end_date: datetime
    initial_capital: float = 1000.0
    parameters: Dict[str, Any] = {}


class BacktestResponse(BaseModel):
    id: int
    strategy_type: str
    symbol: str
    timeframe: str
    initial_capital: float
    final_capital: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: Optional[float]
    parameters: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
