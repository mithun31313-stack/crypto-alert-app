from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.models import Trade, Coin, CoinState
from app.schemas import TradeCreate, TradeOut, TradeExit
from app.portfolio import compute_target_price, compute_stop_loss_price, compute_position_metrics
from app.market_data import binance_client
from app.state_manager import state_after_user_bought, state_after_user_sold

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("/buy", response_model=TradeOut)
async def record_buy(payload: TradeCreate, db: AsyncSession = Depends(get_db)):
    """'I Bought' entry point (spec section 6)."""
    symbol = payload.symbol.upper()
    coin = (await db.execute(select(Coin).where(Coin.symbol == symbol))).scalar_one_or_none()
    if not coin:
        raise HTTPException(404, "Coin not in watchlist — add it first")

    target_price = compute_target_price(payload.entry_price, payload.target_pct)
    stop_loss_price = compute_stop_loss_price(payload.entry_price, payload.stop_loss_pct)

    trade = Trade(
        coin_id=coin.id, symbol=symbol, entry_price=payload.entry_price, quantity=payload.quantity,
        investment_amount=payload.investment_amount, target_pct=payload.target_pct,
        stop_loss_pct=payload.stop_loss_pct, target_price=target_price, stop_loss_price=stop_loss_price,
    )
    db.add(trade)
    coin.state = state_after_user_bought()
    coin.state_updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(trade)

    price = await binance_client.get_price(symbol)
    metrics = compute_position_metrics(trade.entry_price, trade.quantity, trade.investment_amount,
                                        price, trade.target_price, trade.stop_loss_price)
    return TradeOut(**trade.__dict__, current_price=price, **metrics)


@router.post("/{trade_id}/sold", response_model=TradeOut)
async def mark_sold(trade_id: int, payload: TradeExit, db: AsyncSession = Depends(get_db)):
    trade = await db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(404, "Trade not found")
    trade.status = "SOLD"
    trade.exit_price = payload.exit_price
    trade.exited_at = datetime.utcnow()
    trade.realized_pl = (payload.exit_price - trade.entry_price) * trade.quantity
    trade.realized_pl_pct = (payload.exit_price - trade.entry_price) / trade.entry_price * 100

    coin = await db.get(Coin, trade.coin_id)
    if coin:
        coin.state = state_after_user_sold()
        coin.state_updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(trade)
    return TradeOut(**trade.__dict__, current_price=payload.exit_price,
                     current_value=trade.quantity * payload.exit_price,
                     profit_loss=trade.realized_pl, profit_loss_pct=trade.realized_pl_pct)


@router.get("", response_model=list[TradeOut])
async def list_portfolio(status: str = "OPEN", db: AsyncSession = Depends(get_db)):
    q = select(Trade).where(Trade.status == status.upper())
    trades = (await db.execute(q)).scalars().all()
    out = []
    for t in trades:
        if t.status == "OPEN":
            price = await binance_client.get_price(t.symbol)
            metrics = compute_position_metrics(t.entry_price, t.quantity, t.investment_amount,
                                                price, t.target_price, t.stop_loss_price)
            out.append(TradeOut(**t.__dict__, current_price=price, **metrics))
        else:
            out.append(TradeOut(**t.__dict__, current_price=t.exit_price,
                                 current_value=t.quantity * (t.exit_price or 0),
                                 profit_loss=t.realized_pl, profit_loss_pct=t.realized_pl_pct))
    return out
