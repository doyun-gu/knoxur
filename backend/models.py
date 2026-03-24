from sqlalchemy import Column, Integer, Text, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from db import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    broker = Column(Text, nullable=False)
    currency = Column(Text, nullable=False)  # GBP, USD, KRW
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    holdings = relationship("Holding", back_populates="account", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    ticker = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)  # per share, in native currency
    currency = Column(Text, nullable=False)

    account = relationship("Account", back_populates="holdings")

    __table_args__ = (
        UniqueConstraint("account_id", "ticker", name="uq_account_ticker"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    ticker = Column(Text, nullable=False)
    type = Column(Text, nullable=False)  # "buy" or "sell"
    quantity = Column(Float, nullable=False)
    price_per_share = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(Text)

    account = relationship("Account", back_populates="transactions")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Integer)
    currency = Column(Text)

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_ticker_date"),
    )


class FxRate(Base):
    __tablename__ = "fx_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pair = Column(Text, nullable=False)  # e.g. "USDGBP", "USDKRW"
    date = Column(Date, nullable=False)
    rate = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("pair", "date", name="uq_pair_date"),
    )


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    total_gbp = Column(Float)
    total_usd = Column(Float)
    total_krw = Column(Float)
    breakdown_json = Column(Text)  # per-account values as JSON
