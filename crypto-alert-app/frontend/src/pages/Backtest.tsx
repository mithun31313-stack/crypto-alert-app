import { useState } from "react";
import { api } from "../api/client";
import type { BacktestResult } from "../types";

export default function Backtest() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1h");
  const [startDate, setStartDate] = useState(() => {
    const d = new Date(); d.setMonth(d.getMonth() - 3); return d.toISOString().slice(0, 10);
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [minScore, setMinScore] = useState("65");
  const [target, setTarget] = useState("5");
  const [stopLoss, setStopLoss] = useState("3");
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [running, setRunning] = useState(false);

  async function run() {
    setRunning(true);
    try {
      const r = await api.backtest({
        symbol, timeframe,
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        min_buy_score: parseInt(minScore),
        target_pct: parseFloat(target),
        stop_loss_pct: parseFloat(stopLoss),
      });
      setResult(r);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Backtest</h1>
          <p className="page-sub">Historical simulation of the BUY signal engine — not a forecast</p>
        </div>
      </div>

      <div className="two-col">
        <div className="panel">
          <div className="grid-3">
            <div className="field-row">
              <label>Symbol</label>
              <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
            </div>
            <div className="field-row">
              <label>Timeframe</label>
              <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                <option value="15m">15m</option>
                <option value="1h">1h</option>
                <option value="4h">4h</option>
                <option value="1d">1d</option>
              </select>
            </div>
            <div className="field-row">
              <label>Min buy score</label>
              <input value={minScore} onChange={(e) => setMinScore(e.target.value)} type="number" />
            </div>
            <div className="field-row">
              <label>Start date</label>
              <input value={startDate} onChange={(e) => setStartDate(e.target.value)} type="date" />
            </div>
            <div className="field-row">
              <label>End date</label>
              <input value={endDate} onChange={(e) => setEndDate(e.target.value)} type="date" />
            </div>
            <div className="field-row">
              <label>Target %</label>
              <input value={target} onChange={(e) => setTarget(e.target.value)} type="number" />
            </div>
            <div className="field-row">
              <label>Stop-loss %</label>
              <input value={stopLoss} onChange={(e) => setStopLoss(e.target.value)} type="number" />
            </div>
          </div>
          <button className="btn btn-primary" onClick={run} disabled={running}>
            {running ? "Running…" : "Run backtest"}
          </button>
        </div>

        <div className="panel">
          <h3 style={{ margin: "0 0 12px", fontSize: 14 }}>Results</h3>
          {!result && <p style={{ color: "var(--ink-faint)", fontSize: 13 }}>Run a simulation to see results here.</p>}
          {result && (
            <div className="mono" style={{ fontSize: 13, lineHeight: 2 }}>
              <div>Signals evaluated: {result.num_signals}</div>
              <div>Entries: {result.entries}</div>
              <div>Exits: {result.exits}</div>
              <div>Win rate: <span className="pos">{result.win_rate_pct}%</span></div>
              <div>Wins / Losses: {result.winning_trades} / {result.losing_trades}</div>
              <div>Avg profit per trade: {result.avg_profit_pct}%</div>
              <div>Max drawdown: <span className="neg">{result.max_drawdown_pct}%</span></div>
              <div>Total simulated return: {result.total_simulated_return_pct}%</div>
            </div>
          )}
        </div>
      </div>

      {result && <p className="disclaimer-strip">{result.disclaimer}</p>}
    </div>
  );
}
