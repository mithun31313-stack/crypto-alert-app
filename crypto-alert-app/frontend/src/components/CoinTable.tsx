import { useNavigate } from "react-router-dom";
import type { DashboardRow } from "../types";
import SignalBadge from "./SignalBadge";

function fmt(n: number | null, decimals = 2) {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export default function CoinTable({ rows }: { rows: DashboardRow[] }) {
  const navigate = useNavigate();

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Coin</th>
          <th>Price</th>
          <th>24h</th>
          <th>Trend</th>
          <th>RSI</th>
          <th>Support</th>
          <th>Buy Zone</th>
          <th>Signal</th>
          <th>Score</th>
          <th>State</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.symbol} onClick={() => navigate(`/coin/${r.symbol}`)}>
            <td className="coin-name">{r.display_name}</td>
            <td>${fmt(r.price, r.price < 1 ? 5 : 2)}</td>
            <td className={r.change_24h_pct >= 0 ? "pos" : "neg"}>
              {r.change_24h_pct >= 0 ? "+" : ""}{fmt(r.change_24h_pct)}%
            </td>
            <td>{r.trend}</td>
            <td>{r.rsi ?? "—"}</td>
            <td>{r.support ? `$${fmt(r.support)}` : "—"}</td>
            <td>{r.buy_zone_low && r.buy_zone_high ? `$${fmt(r.buy_zone_low)}–$${fmt(r.buy_zone_high)}` : "—"}</td>
            <td><SignalBadge label={r.signal_label} /></td>
            <td>{r.signal_score}/100</td>
            <td style={{ color: "var(--ink-dim)" }}>{r.state.replace(/_/g, " ")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
