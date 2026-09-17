"""
Tiny in-process pub/sub so the worker (which may run in the same process as
the API, or separately) can push live ticks/alerts to connected browser
clients over WebSocket. If you run the worker as a *separate* process/container
from the API, swap this for Redis pub/sub (drop-in: same .broadcast() interface).
"""
import asyncio
from typing import Set
from fastapi import WebSocket


class WSHub:
    def __init__(self):
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, message: dict):
        dead = []
        async with self._lock:
            clients = list(self._clients)
        for ws in clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)


ws_hub = WSHub()
