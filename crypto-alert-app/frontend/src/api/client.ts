import type { DashboardRow, LiveSignal, Trade, BacktestResult } from "../types";

// In local dev, Vite proxies "/api" to localhost:8000 (see vite.config.ts).
// In production (Render), the frontend and backend are separate services,
// so VITE_API_BASE must be set to the backend's URL, e.g.
// https://crypto-alert-backend.onrender.com
const API_ROOT = import.meta.env.VITE_API_BASE ?? "";
const BASE = `${API_ROOT}/api`;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  dashboard: () => request<DashboardRow[]>("/coins/dashboard"),
  listCoins: () => request<{ symbol: string; display_name: string }[]>("/coins"),
  addCoin: (symbol: string) => request("/coins", { method: "POST", body: JSON.stringify({ symbol }) }),
  removeCoin: (symbol: string) => request(`/coins/${symbol}`, { method: "DELETE" }),
  searchCoins: (q: string) => request<{ results: string[] }>(`/coins/search?q=${encodeURIComponent(q)}`),
  candles: (symbol: string, timeframe: string = "1h") =>
    request<any[]>(`/coins/${symbol}/candles?timeframe=${timeframe}`),

  liveSignal: (symbol: string) => request<LiveSignal>(`/signals/live/${symbol}`),
  signalHistory: (symbol: string) => request<any[]>(`/signals/history/${symbol}`),

  portfolio: (status: string = "OPEN") => request<Trade[]>(`/portfolio?status=${status}`),
  recordBuy: (payload: {
    symbol: string; entry_price: number; quantity: number; investment_amount: number;
    target_pct?: number; stop_loss_pct?: number;
  }) => request<Trade>("/portfolio/buy", { method: "POST", body: JSON.stringify(payload) }),
  markSold: (tradeId: number, exit_price: number) =>
    request<Trade>(`/portfolio/${tradeId}/sold`, { method: "POST", body: JSON.stringify({ exit_price }) }),

  backtest: (payload: {
    symbol: string; timeframe: string; start_date: string; end_date: string;
    min_buy_score: number; target_pct: number; stop_loss_pct: number;
  }) => request<BacktestResult>("/backtest", { method: "POST", body: JSON.stringify(payload) }),

  settings: () => request<any>("/settings"),
  patchSettings: (payload: any) => request<any>("/settings", { method: "PATCH", body: JSON.stringify(payload) }),
};
