# app/api/routes/backtest/optimizer.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.backtest.optimizer import optimize_strategy, optimize_all_strategies
from app.services.backtest.data_loader import load_from_exchange, load_from_db
from app.services.market_data.cache_service import fetch_and_cache
from app.services.strategies.builtin import STRATEGY_MAP

router = APIRouter()


@router.post("/optimize/{strategy_type}/{base}/{quote}")
async def run_optimization(
    strategy_type: str,
    base: str,
    quote: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=500, le=1000),
    capital: float = Query(default=1000),
    use_cache: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if strategy_type not in STRATEGY_MAP:
        return {"error": f"Type inconnu. Disponibles: {list(STRATEGY_MAP.keys())}"}

    symbol = f"{base.upper()}/{quote.upper()}"

    if use_cache:
        await fetch_and_cache(db, symbol, timeframe, limit)
        candles = load_from_db(db, symbol, timeframe)
    else:
        candles = await load_from_exchange(symbol, timeframe, limit)

    if len(candles) < 50:
        return {"error": "Pas assez de donnees (minimum 50 bougies)"}

    results = optimize_strategy(strategy_type, candles, capital)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy": strategy_type,
        "candles": len(candles),
        "combinations_tested": len(results),
        "best": results[0] if results else None,
        "top_10": results[:10],
        "all_results": results,
    }


@router.post("/optimize-all/{base}/{quote}")
async def run_full_optimization(
    base: str,
    quote: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=500, le=1000),
    capital: float = Query(default=1000),
    use_cache: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"

    if use_cache:
        await fetch_and_cache(db, symbol, timeframe, limit)
        candles = load_from_db(db, symbol, timeframe)
    else:
        candles = await load_from_exchange(symbol, timeframe, limit)

    if len(candles) < 50:
        return {"error": "Pas assez de donnees (minimum 50 bougies)"}

    results = optimize_all_strategies(candles, capital)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategies_tested": list(STRATEGY_MAP.keys()),
        "candles": len(candles),
        "combinations_tested": len(results),
        "best": results[0] if results else None,
        "top_10": results[:10],
        "all_results": results,
    }


@router.post("/optimize-timeframes/{base}/{quote}")
async def optimize_across_timeframes(
    base: str,
    quote: str,
    limit: int = Query(default=500, le=1000),
    capital: float = Query(default=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    timeframes = ["5m", "15m", "1h", "4h"]
    all_results = []

    for tf in timeframes:
        try:
            await fetch_and_cache(db, symbol, tf, limit)
            candles = load_from_db(db, symbol, tf)
            if len(candles) < 50:
                continue
            results = optimize_all_strategies(candles, capital)
            for r in results:
                r["timeframe"] = tf
            all_results.extend(results)
        except Exception:
            continue

    all_results.sort(key=lambda x: x["win_rate"], reverse=True)

    return {
        "symbol": symbol,
        "timeframes_tested": timeframes,
        "combinations_tested": len(all_results),
        "best": all_results[0] if all_results else None,
        "top_20": all_results[:20],
    }
