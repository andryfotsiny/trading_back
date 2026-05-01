# app/schemas/exchange.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExchangeAccountCreate(BaseModel):
    exchange_name: str
    api_key: str
    api_secret: str
    is_testnet: bool = True


class ExchangeAccountResponse(BaseModel):
    id: int
    exchange_name: str
    is_testnet: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
