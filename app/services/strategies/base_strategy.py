# app/services/strategies/base_strategy.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseStrategy(ABC):

    def __init__(self, parameters: Dict = None):
        self.parameters = parameters or {}

    @abstractmethod
    def analyze(self, candles: List[Dict]) -> Optional[Dict]:
        pass

    def get_closes(self, candles: List[Dict]) -> List[float]:
        return [c["close"] for c in candles]

    def get_volumes(self, candles: List[Dict]) -> List[float]:
        return [c["volume"] for c in candles]
