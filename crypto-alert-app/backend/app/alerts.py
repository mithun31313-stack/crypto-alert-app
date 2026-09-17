"""
Alert protection (spec section 11) + notification message builders (section 15).
No push transport is wired to a third party here — browser notifications are
delivered via the WebSocket/poll endpoint in routers/websocket.py, and this
module just decides WHETHER an alert should fire and what it should say.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AlertLog
from app.config import settings


async def should_alert(
    db: AsyncSession, symbol: str, alert_type: str, score: int, cooldown_hours: Optional[int] = None
) -> bool:
    """
    Suppresses duplicate alerts of the same type within the cooldown window,
    UNLESS the score has moved enough to represent a materially different signal.
    """
    cooldown = cooldown_hours or settings.default_cooldown_hours
    cutoff = datetime.utcnow() - timedelta(hours=cooldown)

    q = (
        select(AlertLog)
        .where(AlertLog.symbol == symbol, AlertLog.alert_type == alert_type, AlertLog.sent_at >= cutoff)
        .order_by(AlertLog.sent_at.desc())
        .limit(1)
    )
    last = (await db.execute(q)).scalar_one_or_none()
    if last is None:
        return True
    if abs(score - last.score) >= settings.min_score_change_to_realert:
        return True
    return False


async def log_alert(db: AsyncSession, symbol: str, alert_type: str, label: str, score: int, message: str):
    db.add(AlertLog(symbol=symbol, alert_type=alert_type, label=label, score=score, message=message))
    await db.commit()


def build_buy_message(display_name: str, price: float, zone_low: float, zone_high: float, score: int) -> str:
    return (
        f"{display_name} potential BUY zone detected at ${price:,.2f} "
        f"(zone ${zone_low:,.2f}–${zone_high:,.2f}, score {score}/100). "
        f"This is a potential buying zone, not a guaranteed bottom."
    )


def build_sell_message(display_name: str, price: float, entry_price: float, score: int) -> str:
    gain = (price - entry_price) / entry_price * 100
    return (
        f"{display_name} potential SELL zone at ${price:,.2f} ({gain:+.2f}% from entry, "
        f"score {score}/100). This is a potential sell zone, not a guaranteed top."
    )


def build_stop_loss_message(display_name: str, price: float, entry_price: float) -> str:
    loss = (price - entry_price) / entry_price * 100
    return f"{display_name} STOP LOSS level reached: ${price:,.2f} ({loss:+.2f}% from entry ${entry_price:,.2f})."


def build_target_approaching_message(display_name: str, price: float, target_price: float) -> str:
    return f"{display_name} is approaching your target of ${target_price:,.2f} (current ${price:,.2f})."
