# app/services/market_data/cache_service.py
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models.candle import Candle
from app.services.market_data.fetcher import fetch_ohlcv


def save_candles_to_db(db: Session, symbol: str, timeframe: str, candles: List[Dict]) -> int:
    saved = 0
    for c in candles:
        open_time = datetime.fromtimestamp(c["timestamp"] / 1000, tz=timezone.utc)
        exists = db.query(Candle).filter(
            and_(
                Candle.symbol == symbol,
                Candle.timeframe == timeframe,
                Candle.open_time == open_time,
            )
        ).first()
        if exists:
            continue
        candle = Candle(
            symbol=symbol,
            timeframe=timeframe,
            open_time=open_time,
            open=c["open"],
            high=c["high"],
            low=c["low"],
            close=c["close"],
            volume=c["volume"],
        )
        db.add(candle)
        saved += 1
    db.commit()
    return saved


def get_candles_from_db(
    db: Session,
    symbol: str,
    timeframe: str,
    limit: int = 100,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[Candle]:
    query = db.query(Candle).filter(
        and_(Candle.symbol == symbol, Candle.timeframe == timeframe)
    )
    if start_time:
        query = query.filter(Candle.open_time >= start_time)
    if end_time:
        query = query.filter(Candle.open_time <= end_time)
    return query.order_by(Candle.open_time.desc()).limit(limit).all()[::-1]


async def fetch_and_cache(db: Session, symbol: str, timeframe: str = "1h", limit: int = 100) -> Dict:
    candles = await fetch_ohlcv(symbol, timeframe, limit)
    saved = save_candles_to_db(db, symbol, timeframe, candles)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "fetched": len(candles),
        "new_saved": saved,
    }
