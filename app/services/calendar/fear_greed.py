# app/services/calendar/fear_greed.py
import httpx
from typing import Dict, Optional


async def get_fear_greed_index(limit: int = 1) -> Dict:
    url = f"https://api.alternative.me/fng/?limit={limit}&format=json"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        data = response.json()

    if not data.get("data"):
        return {"error": "Pas de donnees"}

    current = data["data"][0]
    value = int(current["value"])

    if value <= 20:
        action = "NO_BUY"
        advice = "Extreme Fear - ne pas acheter, attendre"
    elif value <= 35:
        action = "CAUTION_BUY"
        advice = "Fear - acheter avec prudence (potentiel bottom)"
    elif value <= 55:
        action = "NEUTRAL"
        advice = "Neutre - trader normalement"
    elif value <= 75:
        action = "CAUTION_SELL"
        advice = "Greed - vendre avec prudence"
    else:
        action = "NO_BUY"
        advice = "Extreme Greed - ne pas acheter, risque de correction"

    result = {
        "value": value,
        "classification": current["value_classification"],
        "action": action,
        "advice": advice,
        "timestamp": current["timestamp"],
    }

    if limit > 1:
        result["history"] = [
            {
                "value": int(d["value"]),
                "classification": d["value_classification"],
                "timestamp": d["timestamp"],
            }
            for d in data["data"]
        ]

    return result
