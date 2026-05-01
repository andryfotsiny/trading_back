# app/db/models/strategy.py
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    strategy_type = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, default="1h")
    parameters = Column(JSON, default={})
    risk_per_trade = Column(Float, default=0.02)
    stop_loss_pct = Column(Float, default=0.01)
    take_profit_pct = Column(Float, default=0.02)
    max_open_trades = Column(Integer, default=3)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="strategies")
    signals = relationship("Signal", back_populates="strategy")
