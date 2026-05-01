# app/schemas/portfolio.py
from pydantic import BaseModel
from datetime import datetime


class PortfolioResponse(BaseModel):
    total_balance: float
    available_balance: float
    in_positions: float
    total_pnl: float
    total_pnl_pct: float
    updated_at: datetime

    class Config:
        from_attributes = True
