# app/db/models/signal.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    symbol = Column(String, nullable=False)
    action = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0)
    indicators = Column(JSON, default={})
    executed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    strategy = relationship("Strategy", back_populates="signals")
