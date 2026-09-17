"""
FastAPI entrypoint. Runs the REST API + WebSocket feed. The monitoring
worker (app/worker.py) is launched as its own asyncio task on startup so a
single `uvicorn app.main:app` process gives you the full stack — or run
`python -m app.worker` as a separate process/container if you prefer to
scale API and monitoring independently (recommended for production).
"""
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import coins, signals, portfolio, backtest, settings_router, websocket
from app.worker import main as worker_main


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    worker_task = None
    if os.getenv("RUN_WORKER_IN_PROCESS", "true").lower() == "true":
        worker_task = asyncio.create_task(worker_main())
    yield
    if worker_task:
        worker_task.cancel()


app = FastAPI(title="Crypto Trading Alert AI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(coins.router)
app.include_router(signals.router)
app.include_router(portfolio.router)
app.include_router(backtest.router)
app.include_router(settings_router.router)
app.include_router(websocket.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "trading_enabled": False, "note": "Analysis & alert platform only. No auto-trading."}
