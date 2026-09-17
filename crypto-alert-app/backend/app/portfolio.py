"""
Manual portfolio math (spec sections 6 & 14). No trading logic here — just
the arithmetic used both by the trade-entry endpoint and the dashboard.
"""
from typing import Optional


def compute_target_price(entry_price: float, target_pct: Optional[float]) -> Optional[float]:
    if target_pct is None:
        return None
    return round(entry_price * (1 + target_pct / 100), 8)


def compute_stop_loss_price(entry_price: float, stop_loss_pct: Optional[float]) -> Optional[float]:
    if stop_loss_pct is None:
        return None
    return round(entry_price * (1 - stop_loss_pct / 100), 8)


def compute_position_metrics(
    entry_price: float,
    quantity: float,
    investment_amount: float,
    current_price: float,
    target_price: Optional[float],
    stop_loss_price: Optional[float],
):
    current_value = quantity * current_price
    profit_loss = current_value - investment_amount
    profit_loss_pct = (profit_loss / investment_amount * 100) if investment_amount else 0.0

    distance_to_target_pct = None
    if target_price:
        distance_to_target_pct = round((target_price - current_price) / current_price * 100, 2)

    distance_to_stop_pct = None
    if stop_loss_price:
        distance_to_stop_pct = round((current_price - stop_loss_price) / current_price * 100, 2)

    return {
        "current_value": round(current_value, 2),
        "profit_loss": round(profit_loss, 2),
        "profit_loss_pct": round(profit_loss_pct, 2),
        "distance_to_target_pct": distance_to_target_pct,
        "distance_to_stop_pct": distance_to_stop_pct,
    }
