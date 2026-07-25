from app.services.strategies.indicators.atr import get_atr_pct

TF_ATR_HIGH = 0.008
TF_ATR_LOW = 0.004


async def select_best_timeframe(exchange, symbol: str) -> str:
    candles = await exchange.get_ohlcv(symbol, "1h", 100)
    atr_pct = get_atr_pct(candles[:-1])
    if atr_pct >= TF_ATR_HIGH:
        return "15m"
    if atr_pct and atr_pct <= TF_ATR_LOW:
        return "4h"
    return "1h"


async def resolve_timeframe(exchange, strategy) -> str:
    if strategy.timeframe == "auto":
        return await select_best_timeframe(exchange, strategy.symbol)
    return strategy.timeframe
