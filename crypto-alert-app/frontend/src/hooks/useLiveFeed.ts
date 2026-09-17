import { useEffect, useRef, useState } from "react";
import type { LiveAlert } from "../types";

/**
 * Connects to the backend WebSocket feed and (a) fires browser notifications
 * for BUY_WATCH / SELL_WATCH / STOP_LOSS messages (spec section 15), and
 * (b) exposes the latest tick per symbol + a rolling alert feed for the UI.
 */
export function useLiveFeed() {
  const [ticks, setTicks] = useState<Record<string, { price: number; change_24h_pct: number }>>({});
  const [alerts, setAlerts] = useState<LiveAlert[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }

    // Same production/dev split as api/client.ts — same-origin in dev
    // (Vite proxies /ws), but points at the deployed backend on Render.
    const apiBase = import.meta.env.VITE_API_BASE as string | undefined;
    let wsUrl: string;
    if (apiBase) {
      wsUrl = apiBase.replace(/^http/, "ws") + "/ws/live";
    } else {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      wsUrl = `${protocol}://${window.location.host}/ws/live`;
    }
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data: LiveAlert = JSON.parse(event.data);
      if (data.type === "TICK") {
        setTicks((prev) => ({ ...prev, [data.symbol]: { price: data.price!, change_24h_pct: data.change_24h_pct ?? 0 } }));
        return;
      }
      setAlerts((prev) => [data, ...prev].slice(0, 50));
      if ("Notification" in window && Notification.permission === "granted" && data.message) {
        new Notification(`${data.type.replace("_", " ")} — ${data.display_name ?? data.symbol}`, {
          body: data.message,
        });
      }
    };

    return () => ws.close();
  }, []);

  return { ticks, alerts };
}
