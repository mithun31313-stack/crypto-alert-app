import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import PriceChart from "../components/PriceChart";
import SignalBadge from "../components/SignalBadge";
import BuyEntryForm from "../components/BuyEntryForm";
import type { LiveSignal } from "../types";

const TIMEFRAMES = ["15m", "1h", "4h", "1d"];

export default function CoinDetail() {
  const { symbol = "" } = useParams();
  const [timeframe, setTimeframe] = useState("1h");
  const [candles, setCandles] = useState<any[]>([]);
  const [signal, setSignal] = useState<LiveSignal | null>(null);
  const [showBuyForm, setShowBuyForm] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const [c, s] = await Promise.all([api.candles(symbol, timeframe), api.liveSignal(symbol)]);
    setCandles(c);
    setSignal(s);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, [symbol, timeframe]);

  const displayName = `${symbol.replace("USDT", "")}/USDT`;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">{displayName}</h1>
          {signal && <p className="page-sub">Current price ${signal.price.toLocaleString()}</p>}
        </div>
        {signal && <SignalBadge label={signal.label} />}
      </div>

      <div className="two-col">
        <div className="panel" style={{ padding: 16 }}>
          <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                className="btn"
                style={{
                  padding: "6px 12px",
                  background: tf === timeframe ? "var(--panel-raised)" : "transparent",
                  borderColor: tf === timeframe ? "var(--buy)" : "var(--line)",
                  color: tf === timeframe ? "var(--buy)" : "var(--ink-dim)",
                }}
                onClick={() => setTimeframe(tf)}
              >
                {tf}
              </button>
            ))}
          </div>
          {loading ? <p style={{ color: "var(--ink-dim)" }}>Loading chart…</p> : <PriceChart candles={candles} />}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {signal && (
            <div className="panel">
              <h3 style={{ margin: "0 0 4px", fontSize: 14 }}>Signal score</h3>
              <div style={{ fontSize: 30, fontFamily: "var(--font-mono)", fontWeight: 600 }}>{signal.score}<span style={{ fontSize: 15, color: "var(--ink-faint)" }}>/100</span></div>
              <p style={{ fontSize: 12, color: "var(--ink-faint)", margin: "2px 0 10px" }}>
                Potential Buy Zone: ${signal.zone_low.toLocaleString()} – ${signal.zone_high.toLocaleString()}
              </p>
              <ul className="reason-list">
                {signal.reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
              <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
                <button className="btn btn-primary" onClick={() => setShowBuyForm(true)}>I Bought</button>
                <button className="btn">Track This Coin</button>
              </div>
            </div>
          )}

          {signal && (
            <div className="panel">
              <h3 style={{ margin: "0 0 8px", fontSize: 14 }}>AI explanation</h3>
              <p style={{ fontSize: 13, color: "var(--ink-dim)", lineHeight: 1.6 }}>{signal.ai_explanation}</p>
            </div>
          )}
        </div>
      </div>

      <p className="disclaimer-strip">
        This is a potential buying zone, not a guaranteed bottom. Signal strength reflects how many
        independent technical confirmations are currently aligned — it does not predict future price movement.
      </p>

      {showBuyForm && signal && (
        <BuyEntryForm
          symbol={symbol}
          suggestedPrice={signal.price}
          onClose={() => setShowBuyForm(false)}
        />
      )}
    </div>
  );
}
