# app/services/ai/base.py
from abc import ABC, abstractmethod
from typing import Dict


class BaseAIClient(ABC):

    @abstractmethod
    async def analyze_sentiment(self, text: str) -> Dict:
        pass

    @abstractmethod
    async def market_briefing(self, symbol: str, indicators: Dict) -> str:
        pass
