# app/api/routes/backtest/optimizer.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.optimizer_result import OptimizerResult
from app.core.dependencies import get_current_user
from app.services.backtest.optimizer import optimize_strategy, optimize_all_strategies
from app.services.backtest.data_loader import load_from_db
from app.services.market_data.cache_service import fetch_and_cache
from app.services.strategies.builtin import STRATEGY_MAP

router = APIRouter()


def save_result(db, user_id, mode, symbol, timeframe, candles_count, capital, results):
    best = results[0] if results else {}
    record = OptimizerResult(
        user_id=user_id,
        mode=mode,
        symbol=symbol,
        timeframe=timeframe,
        candles_count=candles_count,
        capital=capital,
        combinations_tested=len(results),
        best_strategy=best.get("strategy", ""),
        best_win_rate=best.get("win_rate", 0),
        best_pnl=best.get("total_pnl", 0),
        best_sl=best.get("sl_pct", 0),
        best_tp=best.get("tp_pct", 0),
        best_timeframe=best.get("timeframe", timeframe),
        top_results=results[:50],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.id


@router.post("/single/{strategy_type}/{base}/{quote}")
async def optimize_single(
    strategy_type: str,
    base: str,
    quote: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=500, le=1000),
    capital: float = Query(default=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if strategy_type not in STRATEGY_MAP:
        return {"error": f"Type inconnu. Disponibles: {list(STRATEGY_MAP.keys())}"}

    symbol = f"{base.upper()}/{quote.upper()}"
    await fetch_and_cache(db, symbol, timeframe, limit)
    candles = load_from_db(db, symbol, timeframe)

    if len(candles) < 50:
        return {"error": "Pas assez de donnees (minimum 50 bougies)"}

    results = optimize_strategy(strategy_type, candles, capital)
    for r in results:
        r["timeframe"] = timeframe
    record_id = save_result(db, current_user.id, "single", symbol, timeframe, len(candles), capital, results)

    return {
        "id": record_id,
        "symbol": symbol,
        "strategy": strategy_type,
        "candles": len(candles),
        "combinations_tested": len(results),
        "best": results[0] if results else None,
        "all_results": results,
    }


@router.post("/single-multi-tf/{strategy_type}/{base}/{quote}")
async def optimize_single_multi_tf(
    strategy_type: str,
    base: str,
    quote: str,
    limit: int = Query(default=500, le=1000),
    capital: float = Query(default=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if strategy_type not in STRATEGY_MAP:
        return {"error": f"Type inconnu. Disponibles: {list(STRATEGY_MAP.keys())}"}

    symbol = f"{base.upper()}/{quote.upper()}"
    timeframes = ["5m", "15m", "1h", "4h"]
    all_results = []

    for tf in timeframes:
        try:
            await fetch_and_cache(db, symbol, tf, limit)
            candles = load_from_db(db, symbol, tf)
            if len(candles) < 50:
                continue
            results = optimize_strategy(strategy_type, candles, capital)
            for r in results:
                r["timeframe"] = tf
            all_results.extend(results)
        except Exception:
            continue

    all_results.sort(key=lambda x: x["total_pnl"], reverse=True)
    record_id = save_result(db, current_user.id, "single-multi-tf", symbol, "multi", 0, capital, all_results)

    return {
        "id": record_id,
        "symbol": symbol,
        "strategy": strategy_type,
        "timeframes_tested": timeframes,
        "combinations_tested": len(all_results),
        "best": all_results[0] if all_results else None,
        "all_results": all_results[:50],
    }


@router.post("/all/{base}/{quote}")
async def optimize_all(
    base: str,
    quote: str,
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=500, le=1000),
    capital: float = Query(default=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    symbol = f"{base.upper()}/{quote.upper()}"
    await fetch_and_cache(db, symbol, timeframe, limit)
    candles = load_from_db(db, symbol, timeframe)

    if len(candles) < 50:
        return {"error": "Pas assez de donnees (minimum 50 bougies)"}

    results = optimize_all_strategies(candles, capital)
    for r in results:
        r["timeframe"] = timeframe
    record_id = save_result(db, current_user.id, "all", symbol, timeframe, len(candles), capital, results)

    return {
        "id": record_id,
        "symbol": symbol,
        "strategies_tested": list(STRATEGY_MAP.keys()),
        "candles": len(candles),
        "combinations_tested": len(results),
        "best": results[0] if results else None,
        "all_results": results[:50],
    }


@router.post("/all-multi-tf/{base}/{quote}")
async def optimize_all_multi_tf(
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

    all_results.sort(key=lambda x: x["total_pnl"], reverse=True)
    record_id = save_result(db, current_user.id, "all-multi-tf", symbol, "multi", 0, capital, all_results)

    return {
        "id": record_id,
        "symbol": symbol,
        "timeframes_tested": timeframes,
        "combinations_tested": len(all_results),
        "best": all_results[0] if all_results else None,
        "all_results": all_results[:50],
    }


@router.get("/history")
def list_optimizer_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = db.query(OptimizerResult).filter(
        OptimizerResult.user_id == current_user.id
    ).order_by(OptimizerResult.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "mode": r.mode,
            "symbol": r.symbol,
            "timeframe": r.timeframe,
            "capital": r.capital,
            "combinations_tested": r.combinations_tested,
            "best_strategy": r.best_strategy,
            "best_win_rate": r.best_win_rate,
            "best_pnl": r.best_pnl,
            "best_sl": r.best_sl,
            "best_tp": r.best_tp,
            "best_timeframe": r.best_timeframe,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in results
    ]


@router.get("/history/{result_id}")
def get_optimizer_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = db.query(OptimizerResult).filter(
        OptimizerResult.id == result_id,
        OptimizerResult.user_id == current_user.id,
    ).first()
    if not r:
        return {"error": "Resultat non trouve"}
    return {
        "id": r.id,
        "mode": r.mode,
        "symbol": r.symbol,
        "timeframe": r.timeframe,
        "capital": r.capital,
        "combinations_tested": r.combinations_tested,
        "best_strategy": r.best_strategy,
        "best_win_rate": r.best_win_rate,
        "best_pnl": r.best_pnl,
        "best_sl": r.best_sl,
        "best_tp": r.best_tp,
        "best_timeframe": r.best_timeframe,
        "top_results": r.top_results,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.delete("/history/{result_id}")
def delete_optimizer_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = db.query(OptimizerResult).filter(
        OptimizerResult.id == result_id,
        OptimizerResult.user_id == current_user.id,
    ).first()
    if not r:
        return {"error": "Non trouve"}
    db.delete(r)
    db.commit()
    return {"detail": "Supprime"}
