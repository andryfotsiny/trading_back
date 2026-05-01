# app/schemas/signal.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class SignalResponse(BaseModel):
    id: int
    strategy_id: int
    symbol: str
    action: str
    price: float
    confidence: float
    indicators: Dict[str, Any]
    executed: bool
    created_at: datetime

    class Config:
        from_attributes = True
