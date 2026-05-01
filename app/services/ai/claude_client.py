# app/services/ai/claude_client.py
import httpx
from typing import Dict
from app.services.ai.base import BaseAIClient
from app.core.config import settings


class ClaudeClient(BaseAIClient):

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.CLAUDE_API_KEY
        self.base_url = "https://api.anthropic.com/v1/messages"

    async def _call(self, prompt: str, max_tokens: int = 500) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            data = response.json()
            return data.get("content", [{}])[0].get("text", "")

    async def analyze_sentiment(self, text: str) -> Dict:
        prompt = (
            f"Analyse le sentiment de ce texte crypto/trading. "
            f"Reponds UNIQUEMENT en JSON: "
            f'{{"sentiment": "bullish|bearish|neutral", "score": 0.0-1.0, "summary": "..."}}\n\n'
            f"Texte: {text}"
        )
        result = await self._call(prompt)
        try:
            import json
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(clean)
        except Exception:
            return {"sentiment": "neutral", "score": 0.5, "summary": result[:200]}

    async def market_briefing(self, symbol: str, indicators: Dict) -> str:
        prompt = (
            f"Tu es un analyste trading crypto. "
            f"Donne un briefing court (3-4 phrases) sur {symbol} avec ces indicateurs:\n"
            f"RSI: {indicators.get('rsi')}\n"
            f"MACD: {indicators.get('macd')}\n"
            f"SMA 20: {indicators.get('sma_20')}\n"
            f"Bollinger: {indicators.get('bollinger')}\n"
            f"Prix: {indicators.get('price')}\n"
            f"Reponds en francais."
        )
        return await self._call(prompt)
