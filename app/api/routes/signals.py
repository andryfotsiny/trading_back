# app/api/routes/signals.py
from fastapi import APIRouter, Depends, Query
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.exchange.factory import create_exchange
from app.services.strategies.indicators import (
    get_latest_rsi,
    get_latest_macd,
    get_latest_sma,
    get_latest_ema,
    get_latest_bollinger,
    get_volume_analysis,
)

router = APIRouter()


@router.get("/indicators/{base}/{quote}")
async def get_indicators(
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
    volumes = [c["volume"] for c in candles]

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "price": closes[-1],
        "rsi": get_latest_rsi(closes),
        "macd": get_latest_macd(closes),
        "sma_20": get_latest_sma(closes, 20),
        "ema_20": get_latest_ema(closes, 20),
        "bollinger": get_latest_bollinger(closes),
        "volume": get_volume_analysis(volumes),
    }
