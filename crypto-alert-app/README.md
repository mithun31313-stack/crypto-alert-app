# Crypto Trading Alert AI — Signal Deck

A monitoring-and-alert platform for Binance Spot markets. **It never trades for you.**
It watches your watchlist, scores potential BUY/SELL zones using a multi-confirmation
technical engine, and pushes alerts (browser notifications + in-app feed). You buy and
sell manually on Binance yourself.

```
Binance Public API → Market Data Service → Indicator Engine → Signal Detection Engine
                                                                        │
                                                                        ▼
                                            Coin State Manager → Alert Service → Database
                                                                        │
                                                                        ▼
                                                              Frontend Dashboard (WS)
```

## What's implemented

- **Multi-coin watchlist** (add/remove/search any Binance USDT spot pair) — `app/routers/coins.py`
- **Public Binance market data only** — no login, API secret, or trading permission ever requested — `app/market_data.py`
- **Multi-timeframe analysis** (15m / 1h / 4h / 1d) feeding every signal
- **Weighted BUY-zone scoring** (support, RSI, volume, MACD, EMA/SMA trend, Bollinger, price action, multi-timeframe) → `WATCHING / WEAK BUY SIGNAL / BUY WATCH / STRONG BUY WATCH` — `app/signal_engine.py`
- **Manual buy entry** ("I Bought" flow) with auto-computed target/stop-loss prices and live P/L — `app/portfolio.py`, `app/routers/portfolio.py`
- **SELL-zone / stop-loss detection** for open positions, independent of the BUY engine
- **9-state coin state machine**, persisted in Postgres so it survives refresh — `app/state_manager.py`
- **Alert cooldown + duplicate suppression** with a configurable window and a minimum-score-change override — `app/alerts.py`
- **Live dashboard** (coin, price, 24h change, trend, RSI, support/resistance, buy zone, signal, score, state)
- **Coin detail page**: live candlestick chart (15m/1h/4h/1d), signal breakdown, reasons, AI-style explanation grounded in the actual computed numbers (never invents indicators or prices, never promises profit)
- **Portfolio tracking** with distance-to-target / distance-to-stop
- **Backtesting** (historical simulation only, clearly labeled, walk-forward with no lookahead) — `app/backtest.py`
- **Browser notifications** over a WebSocket live feed — `app/ws_hub.py`, `frontend/src/hooks/useLiveFeed.ts`
- **Configurable settings**: scoring weights, cooldown, sensitivity — `app/routers/settings_router.py`
- **Background worker** that keeps monitoring even when no browser tab is open — `app/worker.py`

## Explicitly NOT implemented (by design, per the brief)

- No automatic trading, no order placement, no withdrawals
- No Binance login/API-secret/trading-permission requests anywhere in the code
- No guaranteed-profit language anywhere in generated alert or AI-explanation text

## Running it on your VPS

### Option A — Docker Compose (simplest)

```bash
docker compose up -d --build
```

- API: `http://your-vps:8000` (docs at `/docs`)
- Frontend: `http://your-vps:5173`
- Postgres: persisted in the `pgdata` volume

The backend container runs the FastAPI app **and** the background worker in the same
process by default (`RUN_WORKER_IN_PROCESS=true`). For higher-volume watchlists, split
them: set `RUN_WORKER_IN_PROCESS=false` on the API service and run a second container
with `CMD ["python", "-m", "app.worker"]`.

### Option B — manual

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL to point at your Postgres
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # dev server proxies /api and /ws to localhost:8000
```

## Notes on scaling this further

- **Redis pub/sub**: `app/ws_hub.py` is intentionally a drop-in interface — swap the
  in-memory set for Redis pub/sub if you run the worker and API as separate processes/containers.
- **Historical backfill for backtesting**: the current backtest endpoint pulls the latest
  klines directly from Binance (good for a few months). For multi-year backtests, backfill
  the `candles` table via Binance's historical klines endpoint and point `run_backtest()`
  at that table instead.
- **Settings persistence**: `/api/settings` currently patches in-memory config — add a
  `settings` table if you want weight changes to survive a restart.
- **Telegram/email notifications**: the alert layer already decides *when* to fire
  (`app/alerts.py`); add a new sender next to the WebSocket broadcast in `worker.py`.

## Disclaimer (also shown in-app)

Crypto markets are highly volatile. Signals are analytical alerts, not guaranteed
predictions. Always do your own research and manage risk.
