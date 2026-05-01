# app/services/bot_runner.py
from app.db.database import SessionLocal
from app.db.models.strategy import Strategy
from app.db.models.trade import Trade
from app.services.exchange.factory import create_exchange
from app.services.strategies.signal_engine import run_strategy
from app.services.execution.paper_executor import PaperExecutor
from app.services.risk.stop_loss import check_trade_exit
from app.services.notifications.telegram_notifier import notifier
import logging

logger = logging.getLogger("bot_runner")


async def bot_cycle():
    db = SessionLocal()
    try:
        strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
        if not strategies:
            return

        exchange = create_exchange()
        try:
            for strategy in strategies:
                try:
                    candles = await exchange.get_ohlcv(strategy.symbol, strategy.timeframe, 100)
                except Exception as e:
                    logger.warning(f"Timeout Binance pour {strategy.symbol} - skip: {str(e)[:100]}")
                    continue

                signal = run_strategy(strategy.strategy_type, candles, strategy.parameters)

                if signal:
                    logger.info(f"Signal {signal['action']} sur {strategy.symbol} ({strategy.name})")
                    executor = PaperExecutor(db, strategy.user_id, capital=1000)
                    result = executor.open_trade(
                        symbol=strategy.symbol,
                        side=signal["action"],
                        entry_price=signal["price"],
                        strategy_name=strategy.name,
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
                                price=signal["price"],
                                quantity=result["quantity"],
                                sl=result["stop_loss"],
                                tp=result["take_profit"],
                            )
                        except Exception:
                            pass

            open_trades = db.query(Trade).filter(Trade.status == "open").all()
            for trade in open_trades:
                try:
                    ticker = await exchange.get_ticker(trade.symbol)
                    price = ticker["last"]
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
                    logger.warning(f"Timeout check trade {trade.id} - skip: {str(e)[:100]}")

        finally:
            await exchange.close()

    except Exception as e:
        logger.error(f"Erreur bot_cycle: {e}")
        try:
            await notifier.notify_error(str(e)[:200])
        except Exception:
            pass
    finally:
        db.close()
