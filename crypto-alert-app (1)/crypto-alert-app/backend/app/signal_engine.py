"""
Weighted, multi-confirmation BUY/SELL zone detection (spec sections 4, 7, 24).

Design intent: never fire off a single indicator. Every component below
returns a 0.0-1.0 "strength" for that confirmation; strength * configured
weight = points. Points are summed into a 0-100 score, then mapped to a
label. This module NEVER claims a guaranteed top/bottom — output language
is enforced to stay in "potential / possible / zone / risk" territory.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd

from app.config import settings
from app.indicators import compute_all, nearest_support, nearest_resistance, volatility_pct


@dataclass
class SignalResult:
    signal_type: str          # "BUY" or "SELL"
    label: str
    score: int
    price: float
    zone_low: Optional[float]
    zone_high: Optional[float]
    reasons: List[str] = field(default_factory=list)
    breakdown: Dict[str, int] = field(default_factory=dict)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def buy_label_for_score(score: int) -> str:
    if score <= settings.score_watching_max:
        return "WATCHING"
    if score <= settings.score_weak_max:
        return "WEAK BUY SIGNAL"
    if score <= settings.score_buywatch_max:
        return "BUY WATCH"
    return "STRONG BUY WATCH"


def evaluate_buy_signal(frames: Dict[str, pd.DataFrame], symbol: str) -> SignalResult:
    """
    frames: {"15m": df, "1h": df, "4h": df, "1d": df}, each raw OHLCV (indicators added here).
    Primary timeframe for the headline zone/price is 1h; others vote into multi_timeframe.
    """
    w = settings.buy_weights
    primary = compute_all(frames["1h"])
    last = primary.iloc[-1]
    price = float(last["close"])

    breakdown: Dict[str, float] = {}
    reasons: List[str] = []

    # 1) Support confirmation — how close is price to nearest recent support?
    support = nearest_support(primary, price)
    resistance = nearest_resistance(primary, price)
    if support:
        dist_pct = (price - support) / support * 100
        strength = _clip01(1 - dist_pct / 3.0)  # full credit within 0%, none beyond 3% above support
        if strength > 0.35:
            reasons.append("Price is near a recent support level")
    else:
        strength = 0.0
    breakdown["support_confirmation"] = strength * w["support_confirmation"]

    # 2) RSI oversold
    rsi_val = last["rsi14"]
    if pd.notna(rsi_val):
        strength = _clip01((35 - rsi_val) / 15.0)  # full credit at RSI<=20, none at RSI>=35
        if rsi_val < 35:
            reasons.append(f"RSI indicates oversold conditions (RSI {rsi_val:.0f})")
    else:
        strength = 0.0
    breakdown["rsi"] = strength * w["rsi"]

    # 3) Volume — is recent selling volume declining vs the prior decline's volume?
    vol_recent = primary["volume"].tail(5).mean()
    vol_prior = primary["volume"].tail(20).head(15).mean()
    if vol_prior and vol_prior > 0:
        vol_ratio = vol_recent / vol_prior
        strength = _clip01((1.3 - vol_ratio) / 0.6)  # credit when recent volume is fading out
        if strength > 0.4:
            reasons.append("Selling pressure appears to be decreasing (volume fading)")
    else:
        strength = 0.0
    breakdown["volume"] = strength * w["volume"]

    # 4) MACD turning up
    hist_now = primary["macd_hist"].iloc[-1]
    hist_prev = primary["macd_hist"].iloc[-4] if len(primary) > 4 else hist_now
    if pd.notna(hist_now) and pd.notna(hist_prev):
        strength = _clip01((hist_now - hist_prev) / (abs(hist_prev) + 1e-9)) if hist_now > hist_prev else 0.0
        strength = _clip01(strength)
        if hist_now > hist_prev and hist_now > primary["macd_hist"].tail(6).min():
            reasons.append("MACD momentum is turning upward")
    else:
        strength = 0.0
    breakdown["macd"] = strength * w["macd"]

    # 5) Trend EMA/SMA — price stabilizing / reclaiming EMA20
    ema20, ema50 = last["ema20"], last["ema50"]
    if pd.notna(ema20) and pd.notna(ema50):
        strength = _clip01(1 - abs(price - ema20) / (ema20 * 0.03))
        if price > ema20 and ema20 < ema50:
            strength = max(strength, 0.6)
            reasons.append("Price is reclaiming its short-term moving average")
    else:
        strength = 0.0
    breakdown["trend_ema_sma"] = strength * w["trend_ema_sma"]

    # 6) Bollinger — proximity to lower band
    bb_lower = last["bb_lower"]
    if pd.notna(bb_lower) and bb_lower > 0:
        dist_pct = (price - bb_lower) / bb_lower * 100
        strength = _clip01(1 - dist_pct / 2.0)
        if strength > 0.4:
            reasons.append("Price is near the lower Bollinger Band")
    else:
        strength = 0.0
    breakdown["bollinger"] = strength * w["bollinger"]

    # 7) Price action reversal — higher low forming after a decline
    recent_lows = primary["low"].tail(6)
    strength = 0.0
    if len(recent_lows) == 6 and recent_lows.iloc[-1] > recent_lows.iloc[:-1].min():
        strength = 0.7
        reasons.append("Short-term reversal price action detected")
    breakdown["price_action_reversal"] = strength * w["price_action_reversal"]

    # 8) Multi-timeframe confirmation — do 4h/1d also show non-bearish RSI / above support?
    votes = 0
    total = 0
    for tf in ("4h", "1d"):
        if tf in frames and len(frames[tf]) > 55:
            df_tf = compute_all(frames[tf])
            r = df_tf["rsi14"].iloc[-1]
            total += 1
            if pd.notna(r) and r < 55:
                votes += 1
    strength = (votes / total) if total else 0.5
    breakdown["multi_timeframe"] = strength * w["multi_timeframe"]
    if strength >= 0.5 and total:
        reasons.append("Higher timeframes are not showing strong bearish pressure")

    score = int(round(sum(breakdown.values())))
    score = max(0, min(100, score))
    label = buy_label_for_score(score)

    zone_low = round(min(price, support) if support else price * 0.99, 2)
    zone_high = round(price * 1.01, 2)

    if not reasons:
        reasons.append("No strong confirmations present yet")

    return SignalResult(
        signal_type="BUY", label=label, score=score, price=price,
        zone_low=zone_low, zone_high=zone_high,
        reasons=reasons, breakdown={k: int(round(v)) for k, v in breakdown.items()},
    )


def sell_label_for_score(score: int, stop_loss_hit: bool, target_hit_strong: bool) -> str:
    if stop_loss_hit:
        return "STOP LOSS ALERT"
    if score >= 60 and target_hit_strong:
        return "SELL WATCH"
    if score >= 40:
        return "TARGET APPROACHING"
    return "HOLDING"


def evaluate_sell_signal(
    frames: Dict[str, pd.DataFrame],
    entry_price: float,
    target_pct: Optional[float],
    stop_loss_pct: Optional[float],
) -> SignalResult:
    w = settings.sell_weights
    primary = compute_all(frames["1h"])
    last = primary.iloc[-1]
    price = float(last["close"])
    gain_pct = (price - entry_price) / entry_price * 100

    breakdown: Dict[str, float] = {}
    reasons: List[str] = []

    resistance = nearest_resistance(primary, price)
    if resistance:
        dist_pct = abs(resistance - price) / price * 100
        strength = _clip01(1 - dist_pct / 2.0)
        if strength > 0.4:
            reasons.append("Price has reached a nearby resistance level")
    else:
        strength = 0.0
    breakdown["resistance_confirmation"] = strength * w["resistance_confirmation"]

    rsi_val = last["rsi14"]
    if pd.notna(rsi_val):
        strength = _clip01((rsi_val - 65) / 15.0)
        if rsi_val > 65:
            reasons.append(f"RSI is elevated (RSI {rsi_val:.0f})")
    else:
        strength = 0.0
    breakdown["rsi_elevated"] = strength * w["rsi_elevated"]

    hist_now = primary["macd_hist"].iloc[-1]
    hist_prev = primary["macd_hist"].iloc[-4] if len(primary) > 4 else hist_now
    strength = 0.0
    if pd.notna(hist_now) and pd.notna(hist_prev) and hist_now < hist_prev:
        strength = _clip01((hist_prev - hist_now) / (abs(hist_prev) + 1e-9))
        reasons.append("Upward momentum is weakening")
    breakdown["momentum_weakening"] = strength * w["momentum_weakening"]

    strength = 0.0
    if pd.notna(hist_now) and hist_now < 0 and pd.notna(hist_prev) and hist_prev >= 0:
        strength = 0.8
        reasons.append("MACD has crossed bearish")
    breakdown["macd_bearish"] = strength * w["macd_bearish"]

    vol_recent = primary["volume"].tail(3).mean()
    vol_avg = primary["volume"].tail(20).mean()
    strength = 0.0
    if vol_avg and vol_recent > vol_avg * 1.4:
        strength = _clip01((vol_recent / vol_avg - 1.4) / 1.0)
        reasons.append("Volume spike detected near recent highs")
    breakdown["volume_climax"] = strength * w["volume_climax"]

    bb_upper = last["bb_upper"]
    strength = 0.0
    if pd.notna(bb_upper) and bb_upper > 0:
        dist_pct = (bb_upper - price) / bb_upper * 100
        strength = _clip01(1 - dist_pct / 2.0)
        if strength > 0.4:
            reasons.append("Price is near the upper Bollinger Band")
    breakdown["bollinger_upper"] = strength * w["bollinger_upper"]

    prior_high = float(primary["high"].tail(60).max())
    strength = _clip01(1 - abs(prior_high - price) / price / 0.02) if prior_high else 0.0
    if strength > 0.4:
        reasons.append("Price is near a previous swing high")
    breakdown["prior_high_proximity"] = strength * w["prior_high_proximity"]

    votes, total = 0, 0
    for tf in ("4h", "1d"):
        if tf in frames and len(frames[tf]) > 55:
            df_tf = compute_all(frames[tf])
            r = df_tf["rsi14"].iloc[-1]
            total += 1
            if pd.notna(r) and r > 55:
                votes += 1
    strength = (votes / total) if total else 0.5
    breakdown["multi_timeframe"] = strength * w["multi_timeframe"]

    score = int(round(sum(breakdown.values())))
    score = max(0, min(100, score))

    stop_loss_hit = bool(stop_loss_pct and gain_pct <= -abs(stop_loss_pct))
    target_hit_strong = bool(target_pct and gain_pct >= target_pct * 0.85)
    label = sell_label_for_score(score, stop_loss_hit, target_hit_strong)

    if stop_loss_hit:
        reasons = [f"Stop-loss level reached ({gain_pct:.2f}% from entry)"]

    zone_low = round(price * 0.995, 2)
    zone_high = round(price * 1.01, 2)

    if not reasons:
        reasons.append("No strong sell confirmations present yet")

    return SignalResult(
        signal_type="SELL", label=label, score=score, price=price,
        zone_low=zone_low, zone_high=zone_high,
        reasons=reasons, breakdown={k: int(round(v)) for k, v in breakdown.items()},
    )
