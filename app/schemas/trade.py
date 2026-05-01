# app/schemas/trade.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TradeResponse(BaseModel):
    id: int
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    pnl: Optional[float]
    pnl_pct: Optional[float]
    status: str
    strategy_name: Optional[str]
    is_paper: bool
    opened_at: datetime
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True
