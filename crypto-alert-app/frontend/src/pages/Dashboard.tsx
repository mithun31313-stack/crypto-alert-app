import { useEffect, useState } from "react";
import { api } from "../api/client";
import CoinTable from "../components/CoinTable";
import AlertFeed from "../components/AlertFeed";
import { useLiveFeed } from "../hooks/useLiveFeed";
import type { DashboardRow } from "../types";

export default function Dashboard() {
  const [rows, setRows] = useState<DashboardRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { alerts, ticks } = useLiveFeed();

  async function load() {
    try {
      const data = await api.dashboard();
      setRows(data);
      setError(null);
    } catch (e: any) {
      setError("Could not reach the monitoring backend. Is the API running?");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  async function handleAdd() {
    const symbol = prompt("Symbol to add (e.g. MATICUSDT):");
    if (!symbol) return;
    try {
      await api.addCoin(symbol.toUpperCase());
      load();
    } catch (e: any) {
      alert(e.message);
    }
  }

  const merged = rows.map((r) => {
    const tick = ticks[r.symbol];
    return tick ? { ...r, price: tick.price, change_24h_pct: tick.change_24h_pct } : r;
  });
  const filtered = search
    ? merged.filter((r) => r.display_name.toLowerCase().includes(search.toLowerCase()))
    : merged;

  return (
    <div className="two-col">
      <div>
        <div className="page-header">
          <div>
            <h1 className="page-title">Watchlist</h1>
            <p className="page-sub">Monitoring {rows.length} pairs · re-evaluated continuously by the backend worker</p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              placeholder="Filter…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                background: "var(--panel)", border: "1px solid var(--line)", color: "var(--ink)",
                padding: "8px 12px", borderRadius: 5, fontFamily: "var(--font-mono)", fontSize: 13,
              }}
            />
            <button className="btn btn-primary" onClick={handleAdd}>+ Add coin</button>
          </div>
        </div>

        {loading && <p style={{ color: "var(--ink-dim)" }}>Loading…</p>}
        {error && <p style={{ color: "var(--sell)" }}>{error}</p>}
        {!loading && !error && (
          <div className="panel" style={{ padding: 0, overflowX: "auto" }}>
            <CoinTable rows={filtered} />
          </div>
        )}

        <p className="disclaimer-strip">
          Crypto markets are highly volatile. Signals shown here are analytical alerts based on
          technical indicators, not guaranteed predictions. This platform never places trades —
          all buys and sells are made manually by you on Binance. Always do your own research and manage risk.
        </p>
      </div>

      <div>
        <div className="panel">
          <h3 style={{ margin: "0 0 12px", fontSize: 14 }}>Live alerts</h3>
          <AlertFeed alerts={alerts} />
        </div>
      </div>
    </div>
  );
}
