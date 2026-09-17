"""
SQLAlchemy models. Everything the spec asks to "not lose on refresh"
(coin state, signals, trades, alert history) is persisted here.
"""
import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean,
    JSON, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class CoinState(str, enum.Enum):
    WATCHING = "WATCHING"
    DECLINING = "DECLINING"
    BUY_ZONE_DETECTED = "BUY_ZONE_DETECTED"
    USER_BOUGHT = "USER_BOUGHT"
    HOLDING = "HOLDING"
    TARGET_APPROACHING = "TARGET_APPROACHING"
    SELL_ZONE_DETECTED = "SELL_ZONE_DETECTED"
    USER_SOLD = "USER_SOLD"
    COOLDOWN = "COOLDOWN"


class SignalLabel(str, enum.Enum):
    WATCHING = "WATCHING"
    WEAK_BUY_SIGNAL = "WEAK BUY SIGNAL"
    BUY_WATCH = "BUY WATCH"
    STRONG_BUY_WATCH = "STRONG BUY WATCH"
    SELL_WATCH = "SELL WATCH"
    STOP_LOSS_ALERT = "STOP LOSS ALERT"
    TARGET_APPROACHING = "TARGET APPROACHING"


class Coin(Base):
    __tablename__ = "coins"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, index=True, nullable=False)  # e.g. BTCUSDT
    display_name = Column(String, nullable=False)  # e.g. BTC/USDT
    active = Column(Boolean, default=True)
    state = Column(Enum(CoinState), default=CoinState.WATCHING, nullable=False)
    state_updated_at = Column(DateTime, default=datetime.utcnow)

    buy_sensitivity = Column(Integer, default=65)   # min score to trigger BUY WATCH
    sell_sensitivity = Column(Integer, default=60)
    cooldown_hours = Column(Integer, default=12)

    created_at = Column(DateTime, default=datetime.utcnow)

    trades = relationship("Trade", back_populates="coin")
    signals = relationship("SignalHistory", back_populates="coin")


class Candle(Base):
    """OHLCV storage per coin/timeframe — used for indicators + backtesting."""
    __tablename__ = "candles"
    __table_args__ = (UniqueConstraint("symbol", "timeframe", "open_time", name="uq_candle"),)

    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True, nullable=False)
    timeframe = Column(String, index=True, nullable=False)
    open_time = Column(DateTime, index=True, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)


class SignalHistory(Base):
    """Every evaluated signal (not just alerted ones) — powers backtesting + AI explanation audit trail."""
    __tablename__ = "signal_history"

    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id"))
    symbol = Column(String, index=True)
    signal_type = Column(String)  # BUY or SELL
    label = Column(Enum(SignalLabel))
    score = Column(Integer)
    price = Column(Float)
    zone_low = Column(Float, nullable=True)
    zone_high = Column(Float, nullable=True)
    reasons = Column(JSON)          # list[str]
    breakdown = Column(JSON)        # {component: points}
    alerted = Column(Boolean, default=False)  # true if it passed cooldown/dup checks and was pushed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    coin = relationship("Coin", back_populates="signals")


class Trade(Base):
    """A manual user position: BUY entry -> optional SELL exit."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id"))
    symbol = Column(String, index=True)

    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    investment_amount = Column(Float, nullable=False)
    target_pct = Column(Float, nullable=True)
    stop_loss_pct = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    stop_loss_price = Column(Float, nullable=True)

    status = Column(String, default="OPEN")  # OPEN | SOLD | IGNORED
    exit_price = Column(Float, nullable=True)
    realized_pl = Column(Float, nullable=True)
    realized_pl_pct = Column(Float, nullable=True)

    entered_at = Column(DateTime, default=datetime.utcnow)
    exited_at = Column(DateTime, nullable=True)

    coin = relationship("Coin", back_populates="trades")


class AlertLog(Base):
    """Tracks what was actually pushed, for cooldown/duplicate suppression (section 11)."""
    __tablename__ = "alert_log"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    alert_type = Column(String)   # BUY_WATCH, SELL_WATCH, STOP_LOSS, TARGET_APPROACHING
    label = Column(String)
    score = Column(Integer)
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
