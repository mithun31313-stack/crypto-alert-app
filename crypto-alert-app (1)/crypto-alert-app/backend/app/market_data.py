"""
Binance PUBLIC Spot market data only.
No API key, no secret, no login, no withdrawal/trading permission — ever.
Docs: https://binance-docs.github.io/apidocs/spot/en/#public-api-definitions
"""
from datetime import datetime, timezone
from typing import Optional
import httpx
import pandas as pd

from app.config import settings

INTERVAL_MAP = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}


class BinancePublicClient:
    def __init__(self):
        self._client = httpx.AsyncClient(base_url=settings.binance_rest_base, timeout=15.0)

    async def close(self):
        await self._client.aclose()

    async def get_price(self, symbol: str) -> float:
        r = await self._client.get("/api/v3/ticker/price", params={"symbol": symbol})
        r.raise_for_status()
        return float(r.json()["price"])

    async def get_24h_ticker(self, symbol: str) -> dict:
        r = await self._client.get("/api/v3/ticker/24hr", params={"symbol": symbol})
        r.raise_for_status()
        data = r.json()
        return {
            "price": float(data["lastPrice"]),
            "change_pct": float(data["priceChangePercent"]),
            "volume": float(data["volume"]),
            "high": float(data["highPrice"]),
            "low": float(data["lowPrice"]),
        }

    async def get_klines(self, symbol: str, interval: str, limit: int = 300) -> pd.DataFrame:
        """Returns OHLCV as a DataFrame indexed by open_time (UTC)."""
        r = await self._client.get(
            "/api/v3/klines",
            params={"symbol": symbol, "interval": INTERVAL_MAP[interval], "limit": limit},
        )
        r.raise_for_status()
        raw = r.json()
        df = pd.DataFrame(raw, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_buy_base", "taker_buy_quote", "ignore",
        ])
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df[["open_time", "open", "high", "low", "close", "volume"]]

    async def search_symbols(self, query: str) -> list[str]:
        """Search all USDT spot pairs matching a query (for 'search and add any pair')."""
        r = await self._client.get("/api/v3/exchangeInfo")
        r.raise_for_status()
        symbols = [
            s["symbol"] for s in r.json()["symbols"]
            if s["status"] == "TRADING"
            and s["quoteAsset"] == "USDT"
            and query.upper() in s["symbol"]
        ]
        return symbols[:25]


binance_client = BinancePublicClient()
