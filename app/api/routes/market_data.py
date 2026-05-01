# app/api/routes/market_data.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.exchange.factory import create_exchange
from app.services.market_data.cache_service import fetch_and_cache, get_candles_from_db

router = APIRouter()


@router.get("/ohlcv/{base}/{quote}")
async def get_ohlcv(
    base: str,
    quote: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=100, le=1000),
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    exchange = create_exchange()
    try:
        candles = await exchange.get_ohlcv(symbol, timeframe, limit)
        return candles
    finally:
        await exchange.close()


@router.get("/price/{base}/{quote}")
async def get_price(
    base: str,
    quote: str,
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    exchange = create_exchange()
    try:
        ticker = await exchange.get_ticker(symbol)
        return {"symbol": symbol, "price": ticker["last"]}
    finally:
        await exchange.close()


@router.post("/cache/{base}/{quote}")
async def cache_candles(
    base: str,
    quote: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    result = await fetch_and_cache(db, symbol, timeframe, limit)
    return result


@router.get("/cached/{base}/{quote}")
def get_cached_candles(
    base: str,
    quote: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    candles = get_candles_from_db(db, symbol, timeframe, limit)
    return [
        {
            "timestamp": c.open_time.isoformat(),
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in candles
    ]
