"""
Background monitoring worker (spec section 21 architecture):

  Binance Public API -> Market Data Service -> Indicator Engine ->
  Signal Detection Engine -> Coin State Manager -> Alert Service -> Database

Runs independently of any open browser tab via APScheduler. Start it with:
  python -m app.worker
or let main.py boot it alongside the API (see main.py).
"""
import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.market_data import binance_client
from app.models import Coin, CoinState, Candle, SignalHistory, Trade
from app.signal_engine import evaluate_buy_signal, evaluate_sell_signal
from app.state_manager import next_state_from_buy_signal, next_state_from_sell_signal
from app.alerts import (
    should_alert, log_alert, build_buy_message, build_sell_message,
    build_stop_loss_message,
)
from app.portfolio import compute_target_price, compute_stop_loss_price
from app.ws_hub import ws_hub

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("worker")


async def ensure_default_watchlist():
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(Coin.symbol))).scalars().all()
        for symbol in settings.default_watchlist:
            if symbol not in existing:
                db.add(Coin(symbol=symbol, display_name=f"{symbol[:-4]}/USDT"))
        await db.commit()


async def fetch_and_store_candles(symbol: str) -> dict:
    """Pull fresh candles for every configured timeframe and persist them."""
    frames = {}
    async with AsyncSessionLocal() as db:
        for tf in settings.timeframes:
            df = await binance_client.get_klines(symbol, tf, settings.candles_per_timeframe)
            frames[tf] = df
            existing = set(
                (await db.execute(
                    select(Candle.open_time).where(Candle.symbol == symbol, Candle.timeframe == tf)
                )).scalars().all()
            )
            for _, row in df.iterrows():
                ot = row["open_time"].to_pydatetime().replace(tzinfo=None)
                if ot not in existing:
                    db.add(Candle(
                        symbol=symbol, timeframe=tf, open_time=ot,
                        open=row["open"], high=row["high"], low=row["low"],
                        close=row["close"], volume=row["volume"],
                    ))
        await db.commit()
    return frames


async def evaluate_coin(coin_row_id: int, symbol: str, display_name: str):
    frames = await fetch_and_store_candles(symbol)
    ticker = await binance_client.get_24h_ticker(symbol)

    async with AsyncSessionLocal() as db:
        coin = await db.get(Coin, coin_row_id)
        if coin is None or not coin.active:
            return

        open_trade = (await db.execute(
            select(Trade).where(Trade.symbol == symbol, Trade.status == "OPEN")
        )).scalar_one_or_none()

        if open_trade is None:
            # --- BUY-side evaluation ---
            result = evaluate_buy_signal(frames, symbol)
            db.add(SignalHistory(
                coin_id=coin.id, symbol=symbol, signal_type="BUY", label=result.label,
                score=result.score, price=result.price, zone_low=result.zone_low,
                zone_high=result.zone_high, reasons=result.reasons, breakdown=result.breakdown,
            ))
            price_declining = frames["1h"]["close"].iloc[-1] < frames["1h"]["close"].iloc[-10]
            coin.state = next_state_from_buy_signal(coin.state, result.label, price_declining)
            coin.state_updated_at = datetime.utcnow()

            if result.label in ("BUY WATCH", "STRONG BUY WATCH") and result.score >= coin.buy_sensitivity:
                if await should_alert(db, symbol, "BUY_WATCH", result.score, coin.cooldown_hours):
                    msg = build_buy_message(display_name, result.price, result.zone_low, result.zone_high, result.score)
                    await log_alert(db, symbol, "BUY_WATCH", result.label, result.score, msg)
                    await ws_hub.broadcast({
                        "type": "BUY_WATCH", "symbol": symbol, "display_name": display_name,
                        "label": result.label, "score": result.score, "price": result.price,
                        "zone_low": result.zone_low, "zone_high": result.zone_high,
                        "reasons": result.reasons, "message": msg,
                    })
        else:
            # --- SELL-side evaluation for the open position ---
            result = evaluate_sell_signal(frames, open_trade.entry_price, open_trade.target_pct, open_trade.stop_loss_pct)
            db.add(SignalHistory(
                coin_id=coin.id, symbol=symbol, signal_type="SELL", label=result.label,
                score=result.score, price=result.price, zone_low=result.zone_low,
                zone_high=result.zone_high, reasons=result.reasons, breakdown=result.breakdown,
            ))
            coin.state = next_state_from_sell_signal(coin.state, result.label)
            coin.state_updated_at = datetime.utcnow()

            if result.label == "STOP LOSS ALERT":
                if await should_alert(db, symbol, "STOP_LOSS", result.score, 1):  # short cooldown, safety-critical
                    msg = build_stop_loss_message(display_name, result.price, open_trade.entry_price)
                    await log_alert(db, symbol, "STOP_LOSS", result.label, result.score, msg)
                    await ws_hub.broadcast({
                        "type": "STOP_LOSS", "symbol": symbol, "display_name": display_name,
                        "price": result.price, "entry_price": open_trade.entry_price, "message": msg,
                    })
            elif result.label == "SELL WATCH":
                if await should_alert(db, symbol, "SELL_WATCH", result.score, coin.cooldown_hours):
                    msg = build_sell_message(display_name, result.price, open_trade.entry_price, result.score)
                    await log_alert(db, symbol, "SELL_WATCH", result.label, result.score, msg)
                    await ws_hub.broadcast({
                        "type": "SELL_WATCH", "symbol": symbol, "display_name": display_name,
                        "label": result.label, "score": result.score, "price": result.price,
                        "zone_low": result.zone_low, "zone_high": result.zone_high,
                        "reasons": result.reasons, "message": msg,
                    })

        await db.commit()
        # Always push a lightweight price/ticker tick so the dashboard feels live
        await ws_hub.broadcast({
            "type": "TICK", "symbol": symbol, "price": ticker["price"], "change_24h_pct": ticker["change_pct"],
        })


async def run_cycle():
    async with AsyncSessionLocal() as db:
        coins = (await db.execute(select(Coin).where(Coin.active == True))).scalars().all()  # noqa: E712
    log.info(f"Cycle start — evaluating {len(coins)} coins")
    for coin in coins:
        try:
            await evaluate_coin(coin.id, coin.symbol, coin.display_name)
        except Exception as e:
            log.exception(f"Error evaluating {coin.symbol}: {e}")
    log.info("Cycle complete")


async def main():
    await init_db()
    await ensure_default_watchlist()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_cycle, "interval", seconds=settings.poll_interval_seconds, next_run_time=datetime.now())
    scheduler.start()
    log.info(f"Worker started — polling every {settings.poll_interval_seconds}s")
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await binance_client.close()


if __name__ == "__main__":
    asyncio.run(main())
