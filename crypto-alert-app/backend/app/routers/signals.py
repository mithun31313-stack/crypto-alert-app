from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SignalHistory
from app.schemas import SignalOut
from app.market_data import binance_client
from app.signal_engine import evaluate_buy_signal

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/live/{symbol}")
async def live_signal(symbol: str):
    """On-demand fresh evaluation, used by the coin detail page (section 13)."""
    symbol = symbol.upper()
    frames = {}
    for tf in ("15m", "1h", "4h", "1d"):
        frames[tf] = await binance_client.get_klines(symbol, tf, 300)
    result = evaluate_buy_signal(frames, symbol)
    return {
        "symbol": symbol, "label": result.label, "score": result.score, "price": result.price,
        "zone_low": result.zone_low, "zone_high": result.zone_high,
        "reasons": result.reasons, "breakdown": result.breakdown,
        "ai_explanation": _explain(result),
    }


def _explain(result) -> str:
    """
    Deterministic, data-grounded explanation (spec section 18) — built directly
    from the computed reasons/score, never inventing indicators or prices.
    """
    if not result.reasons:
        return "Not enough confirmed conditions are present for a signal explanation right now."
    reason_text = "; ".join(r[0].lower() + r[1:] for r in result.reasons)
    return (
        f"{reason_text}. Combined, these factors produced a {result.signal_type.lower()} score of "
        f"{result.score}/100, labeled '{result.label}'. This reflects a potential zone based on the "
        f"calculated indicators above — it is not a guaranteed price movement."
    )


@router.get("/history/{symbol}", response_model=list[SignalOut])
async def signal_history(symbol: str, limit: int = Query(50, le=500), db: AsyncSession = Depends(get_db)):
    q = (
        select(SignalHistory)
        .where(SignalHistory.symbol == symbol.upper())
        .order_by(SignalHistory.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    return rows
