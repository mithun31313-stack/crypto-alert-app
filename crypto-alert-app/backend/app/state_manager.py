"""
Coin state machine (spec section 10). Pure transition logic — the worker
calls `next_state()` each cycle and persists the result on the Coin row.
"""
from app.models import CoinState

# Allowed forward transitions (a coin can also be pushed back to WATCHING
# after COOLDOWN, or to DECLINING/WATCHING if a BUY zone fades before a user acts).
_FLOW = [
    CoinState.WATCHING,
    CoinState.DECLINING,
    CoinState.BUY_ZONE_DETECTED,
    CoinState.USER_BOUGHT,
    CoinState.HOLDING,
    CoinState.TARGET_APPROACHING,
    CoinState.SELL_ZONE_DETECTED,
    CoinState.USER_SOLD,
    CoinState.COOLDOWN,
]


def next_state_from_buy_signal(current: CoinState, buy_label: str, price_declining: bool) -> CoinState:
    if current in (CoinState.USER_BOUGHT, CoinState.HOLDING, CoinState.TARGET_APPROACHING,
                   CoinState.SELL_ZONE_DETECTED):
        return current  # already in a position; buy-side signals don't override it
    if buy_label in ("BUY WATCH", "STRONG BUY WATCH"):
        return CoinState.BUY_ZONE_DETECTED
    if buy_label == "WEAK BUY SIGNAL" or price_declining:
        return CoinState.DECLINING
    return CoinState.WATCHING


def next_state_from_sell_signal(current: CoinState, sell_label: str) -> CoinState:
    if current not in (CoinState.USER_BOUGHT, CoinState.HOLDING,
                        CoinState.TARGET_APPROACHING, CoinState.SELL_ZONE_DETECTED):
        return current
    if sell_label == "STOP LOSS ALERT":
        return CoinState.SELL_ZONE_DETECTED
    if sell_label == "SELL WATCH":
        return CoinState.SELL_ZONE_DETECTED
    if sell_label == "TARGET APPROACHING":
        return CoinState.TARGET_APPROACHING
    return CoinState.HOLDING


def state_after_user_bought() -> CoinState:
    return CoinState.USER_BOUGHT


def state_after_user_sold() -> CoinState:
    return CoinState.USER_SOLD


def state_after_cooldown_elapsed() -> CoinState:
    return CoinState.WATCHING
