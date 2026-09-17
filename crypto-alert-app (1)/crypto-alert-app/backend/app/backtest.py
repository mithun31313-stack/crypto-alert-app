"""
Backtesting engine (spec section 17). Walks forward bar-by-bar over stored
candles, re-evaluates the BUY signal at each bar using ONLY data available up
to that point (no lookahead), simulates entries above `min_buy_score`, and
exits at the configured target or stop-loss. Clearly a historical simulation —
see the disclaimer baked into BacktestResult.
"""
from dataclasses import dataclass
from typing import List
import pandas as pd

from app.signal_engine import evaluate_buy_signal

MIN_WINDOW = 60  # bars needed before indicators (EMA50 etc.) are valid


@dataclass
class SimTrade:
    entry_idx: int
    entry_price: float
    exit_idx: int | None
    exit_price: float | None
    outcome: str  # WIN | LOSS | OPEN
    return_pct: float | None


def run_backtest(df: pd.DataFrame, min_buy_score: int, target_pct: float, stop_loss_pct: float):
    """
    df: OHLCV for a single symbol/timeframe, sorted by open_time ascending,
    already filtered to the requested date range (with MIN_WINDOW extra
    bars of lead-in data ideally included by the caller).
    """
    trades: List[SimTrade] = []
    signals_seen = 0
    in_position = False
    entry_price = 0.0
    entry_idx = 0
    equity_curve = [1.0]

    for i in range(MIN_WINDOW, len(df)):
        window = df.iloc[max(0, i - 200): i + 1]
        if in_position:
            price = float(df["close"].iloc[i])
            gain_pct = (price - entry_price) / entry_price * 100
            if gain_pct >= target_pct:
                trades.append(SimTrade(entry_idx, entry_price, i, price, "WIN", gain_pct))
                equity_curve.append(equity_curve[-1] * (1 + gain_pct / 100))
                in_position = False
            elif gain_pct <= -abs(stop_loss_pct):
                trades.append(SimTrade(entry_idx, entry_price, i, price, "LOSS", gain_pct))
                equity_curve.append(equity_curve[-1] * (1 + gain_pct / 100))
                in_position = False
            continue

        result = evaluate_buy_signal({"1h": window}, symbol="BACKTEST")
        signals_seen += 1
        if result.score >= min_buy_score:
            in_position = True
            entry_price = float(df["close"].iloc[i])
            entry_idx = i

    if in_position:
        last_price = float(df["close"].iloc[-1])
        gain_pct = (last_price - entry_price) / entry_price * 100
        trades.append(SimTrade(entry_idx, entry_price, None, None, "OPEN", gain_pct))

    closed = [t for t in trades if t.outcome in ("WIN", "LOSS")]
    wins = [t for t in closed if t.outcome == "WIN"]
    losses = [t for t in closed if t.outcome == "LOSS"]

    win_rate = (len(wins) / len(closed) * 100) if closed else 0.0
    avg_profit = (sum(t.return_pct for t in closed) / len(closed)) if closed else 0.0

    # Max drawdown on the equity curve built from realized trades only
    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        dd = (peak - v) / peak * 100
        max_dd = max(max_dd, dd)

    total_return = (equity_curve[-1] - 1) * 100

    return {
        "num_signals": signals_seen,
        "entries": len(trades),
        "exits": len(closed),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate_pct": round(win_rate, 2),
        "avg_profit_pct": round(avg_profit, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "total_simulated_return_pct": round(total_return, 2),
    }
