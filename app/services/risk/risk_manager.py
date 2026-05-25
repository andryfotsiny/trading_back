from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.models.trade import Trade
from app.services.risk.position_sizer import calculate_position_size, calculate_stop_loss, calculate_take_profit


class RiskManager:

    def __init__(
        self,
        capital: float,
        risk_per_trade: float = 0.02,
        max_open_trades: int = 999,
        max_drawdown: float = 0.10,
        stop_loss_pct: float = 0.01,
        take_profit_pct: float = 0.02,
    ):
        self.capital = capital
        self.risk_per_trade = risk_per_trade
        self.max_open_trades = max_open_trades
        self.max_drawdown = max_drawdown
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def can_open_trade(self, db: Session, user_id: int) -> Dict:
        open_trades = db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.status == "open",
        ).count()
        return {"allowed": True, "open_trades": open_trades, "drawdown": 0}

    def prepare_trade(self, entry_price: float, side: str) -> Dict:
        sl = calculate_stop_loss(entry_price, side, self.stop_loss_pct)
        tp = calculate_take_profit(entry_price, side, self.take_profit_pct)
        position = calculate_position_size(self.capital, self.risk_per_trade, entry_price, sl)
        return {
            "entry_price": entry_price,
            "side": side,
            "stop_loss": sl,
            "take_profit": tp,
            "quantity": position["quantity"],
            "risk_amount": position["risk_amount"],
            "position_value": position["position_value"],
        }

    def get_total_pnl(self, db: Session, user_id: int) -> float:
        trades = db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.status == "closed",
        ).all()
        return sum(t.pnl or 0 for t in trades)

    def get_risk_summary(self, db: Session, user_id: int) -> Dict:
        open_trades = db.query(Trade).filter(Trade.user_id == user_id, Trade.status == "open").all()
        closed_trades = db.query(Trade).filter(Trade.user_id == user_id, Trade.status == "closed").all()
        total_pnl = sum(t.pnl or 0 for t in closed_trades)
        winning = [t for t in closed_trades if (t.pnl or 0) > 0]
        losing = [t for t in closed_trades if (t.pnl or 0) < 0]
        win_rate = len(winning) / len(closed_trades) if closed_trades else 0
        exposure = sum(t.quantity * t.entry_price for t in open_trades)
        drawdown = abs(total_pnl) / self.capital if total_pnl < 0 else 0

        return {
            "capital": self.capital,
            "total_pnl": round(total_pnl, 2),
            "open_trades": len(open_trades),
            "closed_trades": len(closed_trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": round(win_rate, 4),
            "current_exposure": round(exposure, 2),
            "drawdown": round(drawdown, 4),
            "max_drawdown_limit": self.max_drawdown,
        }