# app/services/ai/sentiment_analyzer.py
from typing import Dict, List
from app.services.ai.factory import create_ai_client


async def analyze_news_sentiment(news_texts: List[str]) -> Dict:
    client = create_ai_client()
    results = []
    for text in news_texts:
        sentiment = await client.analyze_sentiment(text)
        results.append(sentiment)

    if not results:
        return {"overall": "neutral", "score": 0.5, "details": []}

    scores = [r.get("score", 0.5) for r in results]
    avg_score = sum(scores) / len(scores)

    if avg_score >= 0.6:
        overall = "bullish"
    elif avg_score <= 0.4:
        overall = "bearish"
    else:
        overall = "neutral"

    return {
        "overall": overall,
        "score": round(avg_score, 2),
        "count": len(results),
        "details": results,
    }


async def get_ai_signal_boost(signal: Dict, news_sentiment: Dict) -> Dict:
    base_confidence = signal.get("confidence", 0.5)
    sentiment_score = news_sentiment.get("score", 0.5)
    action = signal.get("action", "")

    if action == "BUY" and news_sentiment.get("overall") == "bullish":
        boost = (sentiment_score - 0.5) * 0.5
    elif action == "SELL" and news_sentiment.get("overall") == "bearish":
        boost = (0.5 - sentiment_score) * 0.5
    else:
        boost = 0

    new_confidence = min(max(base_confidence + boost, 0), 1)
    return {
        "original_confidence": base_confidence,
        "ai_boost": round(boost, 4),
        "final_confidence": round(new_confidence, 4),
        "sentiment": news_sentiment.get("overall"),
    }
