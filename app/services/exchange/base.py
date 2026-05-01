# app/services/exchange/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseExchange(ABC):

    @abstractmethod
    async def get_balance(self) -> Dict:
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        pass

    @abstractmethod
    async def get_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List:
        pass

    @abstractmethod
    async def create_order(self, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> Dict:
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: str = None) -> List:
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> Dict:
        pass
