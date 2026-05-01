# app/services/backtest/data_loader.py
from typing import List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models.candle import Candle
from app.services.exchange.factory import create_exchange


async def load_from_exchange(symbol: str, timeframe: str, limit: int = 500) -> List[Dict]:
    exchange = create_exchange()
    try:
        return await exchange.get_ohlcv(symbol, timeframe, limit)
    finally:
        await exchange.close()


def load_from_db(
    db: Session,
    symbol: str,
    timeframe: str,
    start_date: datetime = None,
    end_date: datetime = None,
) -> List[Dict]:
    query = db.query(Candle).filter(
        and_(Candle.symbol == symbol, Candle.timeframe == timeframe)
    )
    if start_date:
        query = query.filter(Candle.open_time >= start_date)
    if end_date:
        query = query.filter(Candle.open_time <= end_date)
    candles = query.order_by(Candle.open_time.asc()).all()
    return [
        {
            "timestamp": int(c.open_time.timestamp() * 1000),
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in candles
    ]
