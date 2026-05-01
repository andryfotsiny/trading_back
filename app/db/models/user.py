# app/db/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    exchange_accounts = relationship("ExchangeAccount", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")
    orders = relationship("Order", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    backtest_results = relationship("BacktestResult", back_populates="user")
