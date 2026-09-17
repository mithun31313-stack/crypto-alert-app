import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Trade } from "../types";

function fmt(n: number | null, d = 2) {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
}

export default function Portfolio() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setTrades(await api.portfolio("OPEN"));
    setLoading(false);
  }

  useEffect(() => {
    load();
    const i = setInterval(load, 20000);
    return () => clearInterval(i);
  }, []);

  async function handleSold(trade: Trade) {
    const exitStr = prompt(`Exit price for ${trade.symbol} (current: $${trade.current_price}):`, `${trade.current_price}`);
    if (!exitStr) return;
    await api.markSold(trade.id, parseFloat(exitStr));
    load();
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Portfolio</h1>
          <p className="page-sub">Manually tracked positions — nothing here is auto-traded</p>
        </div>
      </div>

      {loading && <p style={{ color: "var(--ink-dim)" }}>Loading…</p>}
      {!loading && trades.length === 0 && (
        <p style={{ color: "var(--ink-faint)" }}>No open positions. Log one from a coin's detail page after you buy manually on Binance.</p>
      )}

      <div className="grid-2">
        {trades.map((t) => (
          <div key={t.id} className="panel">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <h3 style={{ margin: 0 }}>{t.symbol.replace("USDT", "")}/USDT</h3>
              <span className={ (t.profit_loss_pct ?? 0) >= 0 ? "pos mono" : "neg mono"}>
                {(t.profit_loss_pct ?? 0) >= 0 ? "+" : ""}{fmt(t.profit_loss_pct)}%
              </span>
            </div>
            <div className="mono" style={{ fontSize: 13, color: "var(--ink-dim)", marginTop: 10, lineHeight: 1.9 }}>
              <div>Invested: ${fmt(t.investment_amount)}</div>
              <div>Entry: ${fmt(t.entry_price, 4)}</div>
              <div>Current: ${fmt(t.current_price, 4)}</div>
              <div>Value: ${fmt(t.current_value)}</div>
              <div>P/L: <span className={(t.profit_loss ?? 0) >= 0 ? "pos" : "neg"}>${fmt(t.profit_loss)}</span></div>
              {t.target_price && <div>Target: ${fmt(t.target_price, 4)} ({fmt(t.distance_to_target_pct)}% away)</div>}
              {t.stop_loss_price && <div>Stop-loss: ${fmt(t.stop_loss_price, 4)} ({fmt(t.distance_to_stop_pct)}% away)</div>}
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
              <button className="btn btn-primary" onClick={() => handleSold(t)}>Mark as Sold</button>
              <button className="btn">Keep Holding</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
