"""
Technical indicator calculations. Pure functions over pandas DataFrames
(columns: open_time, open, high, low, close, volume). No network calls here —
keeps this module unit-testable and reusable by both the live engine and backtester.
"""
import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0):
    mid = sma(series, period)
    std = series.rolling(window=period, min_periods=period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def swing_lows(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """Local minima of `low` — used as candidate support levels."""
    lows = df["low"]
    is_swing_low = (lows == lows.rolling(window=window * 2 + 1, center=True, min_periods=1).min())
    return lows.where(is_swing_low)


def swing_highs(df: pd.DataFrame, window: int = 5) -> pd.Series:
    highs = df["high"]
    is_swing_high = (highs == highs.rolling(window=window * 2 + 1, center=True, min_periods=1).max())
    return highs.where(is_swing_high)


def nearest_support(df: pd.DataFrame, current_price: float, lookback: int = 100) -> float | None:
    """Closest recent swing-low below current price."""
    recent = df.tail(lookback)
    lows = swing_lows(recent).dropna()
    below = lows[lows < current_price]
    if below.empty:
        return float(recent["low"].tail(30).min())
    return float(below.iloc[-1] if len(below) else below.max())


def nearest_resistance(df: pd.DataFrame, current_price: float, lookback: int = 100) -> float | None:
    recent = df.tail(lookback)
    highs = swing_highs(recent).dropna()
    above = highs[highs > current_price]
    if above.empty:
        return float(recent["high"].tail(30).max())
    return float(above.iloc[0] if len(above) else above.min())


def volatility_pct(df: pd.DataFrame, period: int = 20) -> float:
    """Simple realized volatility (std of returns) over the period, as a percentage."""
    returns = df["close"].pct_change().tail(period)
    return float(returns.std() * 100) if len(returns.dropna()) > 1 else 0.0


def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """Attach every indicator as columns to a copy of df."""
    out = df.copy()
    out["ema20"] = ema(out["close"], 20)
    out["ema50"] = ema(out["close"], 50)
    out["sma20"] = sma(out["close"], 20)
    out["sma50"] = sma(out["close"], 50)
    out["rsi14"] = rsi(out["close"], 14)
    macd_line, signal_line, hist = macd(out["close"])
    out["macd"] = macd_line
    out["macd_signal"] = signal_line
    out["macd_hist"] = hist
    bb_up, bb_mid, bb_low = bollinger_bands(out["close"])
    out["bb_upper"] = bb_up
    out["bb_mid"] = bb_mid
    out["bb_lower"] = bb_low
    return out
