from app.db.database import SessionLocal
from app.db.models.strategy import Strategy
from app.db.models.trade import Trade
from app.services.exchange.factory import create_exchange
from app.services.strategies.signal_engine import run_strategy
from app.services.execution.paper_executor import PaperExecutor
from app.services.risk.stop_loss import check_trade_exit
from app.services.risk.trailing_stop import calculate_trailing_stop, calculate_partial_tp
from app.services.notifications.telegram_notifier import notifier
import logging

logger = logging.getLogger("bot_runner")


async def check_market_conditions():
    try:
        from app.services.calendar.economic_calendar import should_trade
        result = await should_trade()
        if not result["can_trade"]:
            reasons = ", ".join(result["reasons"])
            logger.info(f"Bot PAUSE: {reasons}")
            return False, result
        return True, result
    except Exception as e:
        logger.warning(f"Impossible de verifier les conditions marche: {e}")
        return True, {}


def calculate_ma50(candles: list) -> float:
    if len(candles) < 50:
        return None
    closes = [c[4] for c in candles[-50:]]
    return sum(closes) / 50


def is_trend_favorable(signal_action: str, current_price: float, ma50: float) -> bool:
    if ma50 is None:
        return True
    if signal_action == "BUY" and current_price < ma50:
        return False
    if signal_action == "SELL" and current_price > ma50:
        return False
    return True


async def bot_cycle():
    db = SessionLocal()
    try:
        can_trade, market_info = await check_market_conditions()

        strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
        if not strategies:
            return

        exchange = create_exchange()
        try:
            if can_trade:
                for strategy in strategies:
                    try:
                        existing = db.query(Trade).filter(
                            Trade.user_id == strategy.user_id,
                            Trade.strategy_name == strategy.name,
                            Trade.status == "open",
                        ).count()
                        if existing > 0:
                            continue

                        candles = await exchange.get_ohlcv(strategy.symbol, strategy.timeframe, 100)
                        signal = run_strategy(strategy.strategy_type, candles, strategy.parameters)

                        if signal:
                            current_price = signal["price"]
                            ma50 = calculate_ma50(candles)

                            if not is_trend_favorable(signal["action"], current_price, ma50):
                                logger.info(f"Filtre MA50 ({ma50:.2f}): signal {signal['action']} ignore pour {strategy.name}")
                                continue

                            logger.info(f"Signal {signal['action']} sur {current_price} ({strategy.name}) MA50={ma50:.2f}")
                            executor = PaperExecutor(db, strategy.user_id, capital=1000)
                            result = executor.open_trade(
                                symbol=strategy.symbol,
                                side=signal["action"],
                                entry_price=current_price,
                                strategy_name=strategy.name,
                                strategy_type=strategy.strategy_type,
                                risk_per_trade=strategy.risk_per_trade,
                                stop_loss_pct=strategy.stop_loss_pct,
                                take_profit_pct=strategy.take_profit_pct,
                            )
                            if result and "error" not in result:
                                logger.info(f"Trade ouvert: {result}")
                                try:
                                    await notifier.notify_trade_open(
                                        symbol=strategy.symbol,
                                        side=signal["action"],
                                        price=current_price,
                                        quantity=result["quantity"],
                                        sl=result["stop_loss"],
                                        tp=result["take_profit"],
                                    )
                                except Exception:
                                    pass
                    except Exception as e:
                        logger.error(f"Erreur strategie {strategy.name}: {e}")

            open_trades = db.query(Trade).filter(Trade.status == "open").all()
            for trade in open_trades:
                try:
                    ticker = await exchange.get_ticker(trade.symbol)
                    price = ticker["last"]

                    trailing = calculate_trailing_stop(
                        trade.side, trade.entry_price, price, trade.stop_loss
                    )
                    if trailing["updated"]:
                        trade.stop_loss = trailing["new_sl"]
                        db.commit()
                        logger.info(f"Trailing SL: {trade.symbol} -> {trailing['new_sl']}")

                    partial = calculate_partial_tp(
                        trade.side, trade.entry_price, price, trade.take_profit
                    )
                    if partial["should_close"] and partial["close_pct"] < 1.0:
                        original_qty = trade.quantity
                        close_qty = original_qty * partial["close_pct"]
                        trade.quantity = original_qty - close_qty
                        pnl = close_qty * abs(price - trade.entry_price)
                        if trade.side == "SELL":
                            pnl = close_qty * (trade.entry_price - price)
                        trade.pnl = (trade.pnl or 0) + pnl
                        db.commit()
                        logger.info(f"Partial TP: {trade.symbol} qty={close_qty:.6f}")

                    exit_info = check_trade_exit(
                        price, trade.entry_price, trade.side, trade.stop_loss, trade.take_profit
                    )
                    if exit_info:
                        executor = PaperExecutor(db, trade.user_id)
                        result = executor.close_trade(trade.id, exit_info["exit_price"], exit_info["exit_reason"])
                        if result and "error" not in result:
                            logger.info(f"Trade ferme: {result}")
                            try:
                                await notifier.notify_trade_close(
                                    symbol=trade.symbol,
                                    side=trade.side,
                                    entry=trade.entry_price,
                                    exit_price=exit_info["exit_price"],
                                    pnl=result["pnl"],
                                    reason=exit_info["exit_reason"],
                                )
                            except Exception:
                                pass
                except Exception as e:
                    logger.error(f"Erreur check trade {trade.id}: {e}")

        finally:
            await exchange.close()

    except Exception as e:
        logger.error(f"Erreur bot_cycle: {e}")
        try:
            await notifier.notify_error(str(e))
        except Exception:
            pass
    finally:
        db.close()