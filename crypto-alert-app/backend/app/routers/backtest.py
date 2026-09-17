from fastapi import APIRouter
from app.schemas import BacktestRequest, BacktestResult
from app.market_data import binance_client
from app.backtest import run_backtest

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.post("", response_model=BacktestResult)
async def backtest(payload: BacktestRequest):
    """
    Note: for a lightweight, dependency-free build this pulls the max
    available klines from Binance for the symbol/timeframe rather than
    requiring pre-synced history — good for a few months of 1h/4h data.
    For long multi-year backtests, point this at the `candles` table instead
    (same DataFrame shape) once the worker has been running long enough
    to have accumulated history, or backfill via Binance's historical klines.
    """
    df = await binance_client.get_klines(payload.symbol.upper(), payload.timeframe, 1000)
    df = df[(df["open_time"] >= payload.start_date.replace(tzinfo=df["open_time"].dt.tz)) &
            (df["open_time"] <= payload.end_date.replace(tzinfo=df["open_time"].dt.tz))] \
        if len(df) else df

    stats = run_backtest(df.reset_index(drop=True), payload.min_buy_score, payload.target_pct, payload.stop_loss_pct)
    return BacktestResult(symbol=payload.symbol.upper(), timeframe=payload.timeframe, **stats)
