# app/schemas/dashboard.py
from pydantic import BaseModel
from typing import List, Optional


class DashboardStats(BaseModel):
    total_balance: float
    total_pnl: float
    total_pnl_pct: float
    open_trades: int
    total_trades: int
    win_rate: float
    active_strategies: int
