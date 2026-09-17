from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class CoinOut(BaseModel):
    id: int
    symbol: str
    display_name: str
    active: bool
    state: str
    buy_sensitivity: int
    sell_sensitivity: int
    cooldown_hours: int

    class Config:
        from_attributes = True


class CoinCreate(BaseModel):
    symbol: str = Field(..., description="e.g. BTCUSDT")


class DashboardRow(BaseModel):
    symbol: str
    display_name: str
    price: float
    change_24h_pct: float
    trend: str
    rsi: Optional[float]
    support: Optional[float]
    resistance: Optional[float]
    buy_zone_low: Optional[float]
    buy_zone_high: Optional[float]
    sell_zone_low: Optional[float]
    sell_zone_high: Optional[float]
    signal_label: str
    signal_score: int
    state: str


class SignalOut(BaseModel):
    symbol: str
    signal_type: str
    label: str
    score: int
    price: float
    zone_low: Optional[float]
    zone_high: Optional[float]
    reasons: List[str]
    breakdown: Dict[str, int]
    created_at: datetime

    class Config:
        from_attributes = True


class TradeCreate(BaseModel):
    symbol: str
    entry_price: float
    quantity: float
    investment_amount: float
    target_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = None


class TradeOut(BaseModel):
    id: int
    symbol: str
    entry_price: float
    quantity: float
    investment_amount: float
    target_price: Optional[float]
    stop_loss_price: Optional[float]
    status: str
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    distance_to_target_pct: Optional[float] = None
    distance_to_stop_pct: Optional[float] = None

    class Config:
        from_attributes = True


class TradeExit(BaseModel):
    exit_price: float


class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    min_buy_score: int = 65
    target_pct: float = 5.0
    stop_loss_pct: float = 3.0


class BacktestResult(BaseModel):
    symbol: str
    timeframe: str
    num_signals: int
    entries: int
    exits: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    avg_profit_pct: float
    max_drawdown_pct: float
    total_simulated_return_pct: float
    disclaimer: str = "Historical simulation only. Not indicative of future performance."


class SettingsPatch(BaseModel):
    buy_weights: Optional[Dict[str, int]] = None
    sell_weights: Optional[Dict[str, int]] = None
    default_cooldown_hours: Optional[int] = None
    min_score_change_to_realert: Optional[int] = None
