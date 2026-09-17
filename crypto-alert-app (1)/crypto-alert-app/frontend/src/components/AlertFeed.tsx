import type { LiveAlert } from "../types";

const TITLE_MAP: Record<string, string> = {
  BUY_WATCH: "BUY WATCH",
  SELL_WATCH: "SELL WATCH",
  STOP_LOSS: "STOP LOSS",
};

const CLASS_MAP: Record<string, string> = {
  BUY_WATCH: "buy",
  SELL_WATCH: "sell",
  STOP_LOSS: "stop",
};

export default function AlertFeed({ alerts }: { alerts: LiveAlert[] }) {
  if (alerts.length === 0) {
    return <p style={{ color: "var(--ink-faint)", fontSize: 13 }}>No alerts yet. This feed fills in as the monitoring worker evaluates your watchlist.</p>;
  }
  return (
    <div className="alert-feed">
      {alerts.map((a, i) => (
        <div key={i} className={`alert-item ${CLASS_MAP[a.type] ?? ""}`}>
          <div className="alert-title">{TITLE_MAP[a.type] ?? a.type} — {a.display_name ?? a.symbol}</div>
          <div className="alert-msg">{a.message}</div>
        </div>
      ))}
    </div>
  );
}
