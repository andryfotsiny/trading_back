# app/services/ai/market_briefing.py
from typing import Dict
from app.services.ai.factory import create_ai_client


async def generate_briefing(symbol: str, indicators: Dict) -> str:
    client = create_ai_client()
    return await client.market_briefing(symbol, indicators)
