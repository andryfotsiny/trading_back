# app/db/models/optimizer_result.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.database import Base


class OptimizerResult(Base):
    __tablename__ = "optimizer_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mode = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=True)
    candles_count = Column(Integer, default=0)
    capital = Column(Float, default=1000)
    combinations_tested = Column(Integer, default=0)
    best_strategy = Column(String, nullable=True)
    best_win_rate = Column(Float, default=0)
    best_pnl = Column(Float, default=0)
    best_sl = Column(Float, default=0)
    best_tp = Column(Float, default=0)
    best_timeframe = Column(String, nullable=True)
    top_results = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
