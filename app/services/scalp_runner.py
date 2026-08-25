from app.db.database import SessionLocal
from app.db.models.strategy import Strategy
from app.db.models.trade import Trade
from app.services.exchange.factory import create_exchange
from app.services.strategies.signal_engine import run_strategy
from app.services.execution.paper_executor import PaperExecutor
from app.services.risk.stop_loss import check_trade_exit, check_trade_exit_range
from app.services.risk.trailing_stop import calculate_trailing_stop
from app.services.bot_runner import resolve_risk_levels, SCALP_TYPES
from datetime import datetime, timezone
import logging

logger = logging.getLogger("scalp_runner")

SCALP_MIN_SL_PCT = 0.0015
SCALP_MAX_SL_PCT = 0.01
SCALP_MIN_TP_PCT = 0.003
SCALP_MAX_TP_PCT = 0.02


async def scalp_cycle():
    db = SessionLocal()
    cycle_start = datetime.now(timezone.utc)
    try:
        strategies = db.query(Strategy).filter(
            Strategy.is_active == True,
            Strategy.strategy_type.in_(SCALP_TYPES),
        ).all()
        if not strategies:
            return

        exchange = create_exchange()
        try:
            for strategy in strategies:
                try:
                    existing = db.query(Trade).filter(
                        Trade.user_id == strategy.user_id,
                        Trade.strategy_name == strategy.name,
                        Trade.status == "open",
                    ).count()
                    if existing > 0:
                        continue

                    params = strategy.parameters or {}
                    timeframe = params.get("scalp_timeframe", "1m")
                    candles = await exchange.get_ohlcv(strategy.symbol, timeframe, 100)
                    closed_candles = candles[:-1]
                    signal = run_strategy(strategy.strategy_type, closed_candles, params)
                    if not signal:
                        continue

                    bar_start = datetime.fromtimestamp(
                        candles[-1]["timestamp"] / 1000, tz=timezone.utc
                    )
                    already_traded = db.query(Trade).filter(
                        Trade.user_id == strategy.user_id,
                        Trade.strategy_name == strategy.name,
                        Trade.opened_at >= bar_start,
                    ).count()
                    if already_traded > 0:
                        continue

                    ticker = await exchange.get_ticker(strategy.symbol)
                    current_price = ticker["last"]

                    stop_loss_pct, take_profit_pct = resolve_risk_levels(
                        closed_candles, strategy, params,
                        SCALP_MIN_SL_PCT, SCALP_MAX_SL_PCT, SCALP_MIN_TP_PCT, SCALP_MAX_TP_PCT,
                    )

                    logger.info(f"Signal scalp {signal['action']} sur {current_price} ({strategy.name}) TF={timeframe} SL={stop_loss_pct:.4f} TP={take_profit_pct:.4f}")
                    executor = PaperExecutor(db, strategy.user_id, capital=1000)
                    result = executor.open_trade(
                        symbol=strategy.symbol,
                        side=signal["action"],
                        entry_price=current_price,
                        strategy_name=strategy.name,
                        strategy_type=strategy.strategy_type,
                        risk_per_trade=strategy.risk_per_trade,
                        stop_loss_pct=stop_loss_pct,
                        take_profit_pct=take_profit_pct,
                    )
                    if result and "error" not in result:
                        logger.info(f"Trade scalp ouvert: {result}")
                except Exception:
                    logger.exception(f"Erreur strategie scalp {strategy.name}")

            strategies_by_name = {s.name: s for s in strategies}

            open_trades = db.query(Trade).filter(
                Trade.status == "open",
                Trade.strategy_type.in_(SCALP_TYPES),
                Trade.opened_at < cycle_start,
            ).all()
            for trade in open_trades:
                try:
                    ticker = await exchange.get_ticker(trade.symbol)
                    price = ticker["last"]

                    strategy = strategies_by_name.get(trade.strategy_name)
                    params = (strategy.parameters or {}) if strategy else {}
                    trailing_pct = params.get("trailing_pct", 0.003)
                    risk_pct = (
                        abs(trade.entry_price - trade.stop_loss) / trade.entry_price
                        if trade.entry_price and trade.stop_loss
                        else 0.002
                    )
                    activation_pct = params.get("trailing_activation_pct", risk_pct)

                    trailing = calculate_trailing_stop(
                        trade.side,
                        trade.entry_price,
                        price,
                        trade.stop_loss,
                        trailing_pct,
                        activation_pct,
                    )
                    if trailing["updated"]:
                        trade.stop_loss = trailing["new_sl"]
                        db.commit()
                        logger.info(f"Trailing SL scalp: {trade.symbol} -> {trailing['new_sl']}")

                    try:
                        recent_candles = await exchange.get_ohlcv(trade.symbol, "1m", 5)
                        opened_ms = trade.opened_at.timestamp() * 1000
                        recent_candles = [c for c in recent_candles if c["timestamp"] >= opened_ms]
                        if not recent_candles:
                            raise ValueError("aucune bougie posterieure a l'entree")
                        recent_high = max(c["high"] for c in recent_candles)
                        recent_low = min(c["low"] for c in recent_candles)
                        exit_info = check_trade_exit_range(
                            recent_high, recent_low, trade.entry_price, trade.side, trade.stop_loss, trade.take_profit
                        )
                    except Exception:
                        exit_info = check_trade_exit(
                            price, trade.entry_price, trade.side, trade.stop_loss, trade.take_profit
                        )
                    if exit_info:
                        executor = PaperExecutor(db, trade.user_id)
                        result = executor.close_trade(trade.id, exit_info["exit_price"], exit_info["exit_reason"])
                        if result and "error" not in result:
                            logger.info(f"Trade scalp ferme: {result}")
                except Exception:
                    logger.exception(f"Erreur check trade scalp {trade.id}")
        finally:
            await exchange.close()
    except Exception:
        logger.exception("Erreur scalp_cycle")
    finally:
        db.close()
