"""
Central configuration for the Crypto Alert app.
All signal weights, cooldowns and sensitivity knobs live here so the
Settings API (routers/settings.py) can read + patch them at runtime.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Dict


class Settings(BaseSettings):
    # --- Database ---
    # Render (and most managed Postgres providers) hand you a
    # postgres://... or postgresql://... URL — SQLAlchemy's async engine
    # needs the +asyncpg driver prefix, so we normalize it automatically.
    database_url: str = "postgresql+asyncpg://crypto:crypto@localhost:5432/crypto_alerts"

    @field_validator("database_url")
    @classmethod
    def _use_asyncpg_driver(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # --- Binance public endpoints (no auth needed, ever) ---
    binance_rest_base: str = "https://api.binance.com"
    binance_ws_base: str = "wss://stream.binance.com:9443/ws"

    # --- Monitoring ---
    default_watchlist: list[str] = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
        "BNBUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT",
    ]
    timeframes: list[str] = ["15m", "1h", "4h", "1d"]
    candles_per_timeframe: int = 300
    poll_interval_seconds: int = 30  # how often the worker re-evaluates each coin

    # --- Signal scoring weights (must sum to ~100, configurable via API) ---
    buy_weights: Dict[str, int] = {
        "support_confirmation": 20,
        "rsi": 15,
        "volume": 15,
        "macd": 10,
        "trend_ema_sma": 10,
        "bollinger": 10,
        "price_action_reversal": 10,
        "multi_timeframe": 10,
    }
    sell_weights: Dict[str, int] = {
        "resistance_confirmation": 20,
        "rsi_elevated": 15,
        "momentum_weakening": 15,
        "macd_bearish": 10,
        "volume_climax": 10,
        "bollinger_upper": 10,
        "prior_high_proximity": 10,
        "multi_timeframe": 10,
    }

    # --- Score thresholds -> label ---
    score_watching_max: int = 39
    score_weak_max: int = 59
    score_buywatch_max: int = 74
    # >= score_buywatch_max+1 => STRONG BUY WATCH

    # --- Alert protection ---
    default_cooldown_hours: int = 12
    min_score_change_to_realert: int = 8

    # --- Trade defaults (user can override per position) ---
    default_target_pct: float = 5.0
    default_stop_loss_pct: float = 3.0

    class Config:
        env_file = ".env"


settings = Settings()
