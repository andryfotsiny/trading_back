# app/services/market_data/fetcher.py
from typing import List, Dict
from app.services.exchange.factory import create_exchange


async def fetch_ohlcv(symbol: str, timeframe: str = "1h", limit: int = 100) -> List[Dict]:
    exchange = create_exchange()
    try:
        return await exchange.get_ohlcv(symbol, timeframe, limit)
    finally:
        await exchange.close()


async def fetch_ticker(symbol: str) -> Dict:
    exchange = create_exchange()
    try:
        return await exchange.get_ticker(symbol)
    finally:
        await exchange.close()


async def fetch_multiple_tickers(symbols: List[str]) -> List[Dict]:
    exchange = create_exchange()
    try:
        results = []
        for symbol in symbols:
            ticker = await exchange.get_ticker(symbol)
            results.append(ticker)
        return results
    finally:
        await exchange.close()
