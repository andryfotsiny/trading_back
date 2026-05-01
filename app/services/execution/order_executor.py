# app/services/execution/order_executor.py
from datetime import datetime, timezone
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.db.models.trade import Trade
from app.db.models.order import Order
from app.services.exchange.factory import create_exchange
from app.services.risk.risk_manager import RiskManager


class OrderExecutor:

    def __init__(self, db: Session, user_id: int, capital: float = 1000):
        self.db = db
        self.user_id = user_id
        self.rm = RiskManager(capital=capital)

    async def open_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        strategy_name: str = None,
        risk_per_trade: float = 0.02,
        stop_loss_pct: float = 0.01,
        take_profit_pct: float = 0.02,
    ) -> Optional[Dict]:
        self.rm.risk_per_trade = risk_per_trade
        self.rm.stop_loss_pct = stop_loss_pct
        self.rm.take_profit_pct = take_profit_pct

        check = self.rm.can_open_trade(self.db, self.user_id)
        if not check["allowed"]:
            return {"error": check["reason"]}

        prep = self.rm.prepare_trade(entry_price, side)
        exchange = create_exchange()
        try:
            order_result = await exchange.create_order(
                symbol=symbol,
                side=side.lower(),
                order_type="market",
                quantity=prep["quantity"],
            )
        finally:
            await exchange.close()

        trade = Trade(
            user_id=self.user_id,
            symbol=symbol,
            side=side,
            entry_price=float(order_result.get("price") or entry_price),
            quantity=prep["quantity"],
            stop_loss=prep["stop_loss"],
            take_profit=prep["take_profit"],
            status="open",
            strategy_name=strategy_name,
            is_paper=False,
        )
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)

        order = Order(
            user_id=self.user_id,
            trade_id=trade.id,
            symbol=symbol,
            side=side,
            order_type="market",
            quantity=prep["quantity"],
            price=trade.entry_price,
            status="filled",
            exchange_order_id=order_result.get("id"),
            filled_quantity=prep["quantity"],
            filled_price=trade.entry_price,
            executed_at=datetime.now(timezone.utc),
        )
        self.db.add(order)
        self.db.commit()

        return {
            "trade_id": trade.id,
            "symbol": symbol,
            "side": side,
            "entry_price": trade.entry_price,
            "quantity": prep["quantity"],
            "stop_loss": prep["stop_loss"],
            "take_profit": prep["take_profit"],
            "exchange_order_id": order_result.get("id"),
            "status": "open",
            "is_paper": False,
        }
