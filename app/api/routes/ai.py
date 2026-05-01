# app/api/routes/ai.py
from fastapi import APIRouter, Depends, Query, Body
from typing import List
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.ai.sentiment_analyzer import analyze_news_sentiment, get_ai_signal_boost
from app.services.ai.market_briefing import generate_briefing
from app.services.exchange.factory import create_exchange
from app.services.strategies.indicators import (
    get_latest_rsi,
    get_latest_macd,
    get_latest_sma,
    get_latest_bollinger,
)

router = APIRouter()


@router.post("/sentiment")
async def sentiment_analysis(
    texts: List[str] = Body(...),
    current_user: User = Depends(get_current_user),
):
    result = await analyze_news_sentiment(texts)
    return result


@router.get("/briefing/{base}/{quote}")
async def market_briefing(
    base: str,
    quote: str,
    timeframe: str = Query(default="1h"),
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    exchange = create_exchange()
    try:
        candles = await exchange.get_ohlcv(symbol, timeframe, 100)
    finally:
        await exchange.close()

    closes = [c["close"] for c in candles]
    indicators = {
        "price": closes[-1],
        "rsi": get_latest_rsi(closes),
        "macd": get_latest_macd(closes),
        "sma_20": get_latest_sma(closes, 20),
        "bollinger": get_latest_bollinger(closes),
    }
    briefing = await generate_briefing(symbol, indicators)
    return {"symbol": symbol, "indicators": indicators, "briefing": briefing}


@router.post("/boost-signal")
async def boost_signal(
    action: str = Query(...),
    confidence: float = Query(...),
    texts: List[str] = Body(...),
    current_user: User = Depends(get_current_user),
):
    sentiment = await analyze_news_sentiment(texts)
    signal = {"action": action, "confidence": confidence}
    result = await get_ai_signal_boost(signal, sentiment)
    return result