from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws_hub import ws_hub

router = APIRouter()


@router.websocket("/ws/live")
async def live_feed(ws: WebSocket):
    """
    Browser dashboard connects here for live ticks + alerts (BUY_WATCH,
    SELL_WATCH, STOP_LOSS, TICK message types). Drives the browser
    Notification API on the frontend (spec section 15).
    """
    await ws_hub.connect(ws)
    try:
        while True:
            await ws.receive_text()  # client doesn't need to send anything; keeps the socket alive
    except WebSocketDisconnect:
        await ws_hub.disconnect(ws)
