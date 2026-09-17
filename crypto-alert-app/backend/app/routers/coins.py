from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Coin, Candle
from app.schemas import CoinOut, CoinCreate, DashboardRow
from app.market_data import binance_client
from app.signal_engine import evaluate_buy_signal
from app.indicators import compute_all, nearest_support, nearest_resistance

router = APIRouter(prefix="/api/coins", tags=["coins"])


@router.get("", response_model=list[CoinOut])
async def list_coins(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Coin))).scalars().all()
    return rows


@router.post("", response_model=CoinOut)
async def add_coin(payload: CoinCreate, db: AsyncSession = Depends(get_db)):
    symbol = payload.symbol.upper()
    existing = (await db.execute(select(Coin).where(Coin.symbol == symbol))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Coin already in watchlist")
    if not symbol.endswith("USDT"):
        raise HTTPException(400, "Only USDT spot pairs are supported in this build")
    try:
        await binance_client.get_price(symbol)  # validates the symbol exists on Binance
    except Exception:
        raise HTTPException(400, f"{symbol} is not a valid Binance Spot symbol")
    coin = Coin(symbol=symbol, display_name=f"{symbol[:-4]}/USDT")
    db.add(coin)
    await db.commit()
    await db.refresh(coin)
    return coin


@router.delete("/{symbol}")
async def remove_coin(symbol: str, db: AsyncSession = Depends(get_db)):
    coin = (await db.execute(select(Coin).where(Coin.symbol == symbol.upper()))).scalar_one_or_none()
    if not coin:
        raise HTTPException(404, "Not found")
    coin.active = False
    await db.commit()
    return {"ok": True}


@router.get("/search")
async def search(q: str):
    return {"results": await binance_client.search_symbols(q)}


@router.get("/{symbol}/candles")
async def candles(symbol: str, timeframe: str = "1h", limit: int = 300):
    """Raw OHLCV for the coin-detail charts (section 13)."""
    df = await binance_client.get_klines(symbol.upper(), timeframe, limit)
    return [
        {"open_time": row["open_time"].isoformat(), "open": row["open"], "high": row["high"],
         "low": row["low"], "close": row["close"], "volume": row["volume"]}
        for _, row in df.iterrows()
    ]


@router.get("/dashboard", response_model=list[DashboardRow])
async def dashboard(db: AsyncSession = Depends(get_db)):
    """One-shot snapshot for the main dashboard table (section 12)."""
    coins = (await db.execute(select(Coin).where(Coin.active == True))).scalars().all()  # noqa: E712
    rows = []
    for coin in coins:
        ticker = await binance_client.get_24h_ticker(coin.symbol)
        df = await binance_client.get_klines(coin.symbol, "1h", 300)
        indicators = compute_all(df)
        last = indicators.iloc[-1]
        price = ticker["price"]
        support = nearest_support(indicators, price)
        resistance = nearest_resistance(indicators, price)

        buy_result = evaluate_buy_signal({"1h": df, "4h": df, "1d": df}, coin.symbol)
        ema20, ema50 = last["ema20"], last["ema50"]
        trend = "Bullish" if ema20 and ema50 and ema20 > ema50 else "Bearish"
        if ticker["change_pct"] < -1 and buy_result.score > 55:
            trend += " → Reversal"

        rows.append(DashboardRow(
            symbol=coin.symbol, display_name=coin.display_name, price=price,
            change_24h_pct=ticker["change_pct"], trend=trend,
            rsi=round(float(last["rsi14"]), 1) if last["rsi14"] == last["rsi14"] else None,
            support=support, resistance=resistance,
            buy_zone_low=buy_result.zone_low, buy_zone_high=buy_result.zone_high,
            sell_zone_low=None, sell_zone_high=None,
            signal_label=buy_result.label, signal_score=buy_result.score,
            state=coin.state.value if hasattr(coin.state, "value") else str(coin.state),
        ))
    return rows
