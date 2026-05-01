# app/services/ai/ollama_client.py
import httpx
from typing import Dict
from app.services.ai.base import BaseAIClient
from app.core.config import settings


class OllamaClient(BaseAIClient):

    def __init__(self, model: str = None):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = "http://localhost:11434/api/generate"

    async def _call(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.base_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            data = response.json()
            return data.get("response", "")

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
