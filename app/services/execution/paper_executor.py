from datetime import datetime, timezone
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.db.models.trade import Trade
from app.db.models.order import Order
from app.services.risk.risk_manager import RiskManager
from app.services.risk.stop_loss import check_trade_exit


class PaperExecutor:
    def __init__(self, db: Session, user_id: int, capital: float = 1000):
        self.db = db
        self.user_id = user_id
        self.rm = RiskManager(capital=capital)

    def open_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        strategy_name: str = None,
        strategy_type: str = None,
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

        trade = Trade(
            user_id=self.user_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=prep["quantity"],
            stop_loss=prep["stop_loss"],
            take_profit=prep["take_profit"],
            status="open",
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            is_paper=True,
        )
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)

        return {
            "trade_id": trade.id,
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "quantity": prep["quantity"],
            "stop_loss": prep["stop_loss"],
            "take_profit": prep["take_profit"],
            "strategy_name": strategy_name,
            "strategy_type": strategy_type,
        }

    def close_trade(self, trade_id: int, exit_price: float, reason: str = "manual") -> Optional[Dict]:
        trade = self.db.query(Trade).filter(
            Trade.id == trade_id,
            Trade.user_id == self.user_id,
            Trade.status == "open",
        ).first()

        if not trade:
            return {"error": "Trade non trouve"}

        if trade.side == "BUY":
            pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - exit_price) * trade.quantity

        pnl_pct = round((pnl / (trade.entry_price * trade.quantity)) * 100, 2)

        trade.exit_price = exit_price
        trade.pnl = round(pnl, 4)
        trade.pnl_pct = pnl_pct
        trade.status = "closed"
        trade.closed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(trade)

        return {
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "exit_price": exit_price,
            "quantity": trade.quantity,
            "pnl": round(pnl, 4),
            "pnl_pct": pnl_pct,
            "reason": reason,
            "status": "closed",
        }
