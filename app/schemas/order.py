# app/schemas/order.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrderCreate(BaseModel):
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None


class OrderResponse(BaseModel):
    id: int
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    filled_quantity: float
    filled_price: Optional[float]
    fee: float
    created_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True
