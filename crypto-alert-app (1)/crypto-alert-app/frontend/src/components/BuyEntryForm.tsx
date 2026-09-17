import { useState } from "react";
import { api } from "../api/client";

export default function BuyEntryForm({
  symbol, suggestedPrice, onClose,
}: { symbol: string; suggestedPrice: number; onClose: () => void }) {
  const [entryPrice, setEntryPrice] = useState(suggestedPrice.toString());
  const [quantity, setQuantity] = useState("");
  const [investment, setInvestment] = useState("");
  const [target, setTarget] = useState("5");
  const [stopLoss, setStopLoss] = useState("3");
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function submit() {
    setSaving(true);
    setErrorMsg(null);
    try {
      await api.recordBuy({
        symbol,
        entry_price: parseFloat(entryPrice),
        quantity: parseFloat(quantity),
        investment_amount: parseFloat(investment),
        target_pct: target ? parseFloat(target) : undefined,
        stop_loss_pct: stopLoss ? parseFloat(stopLoss) : undefined,
      });
      onClose();
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50,
    }}>
      <div className="panel" style={{ width: 380, background: "var(--panel-raised)" }}>
        <h3 style={{ margin: "0 0 4px" }}>Record your buy — {symbol}</h3>
        <p style={{ fontSize: 12, color: "var(--ink-faint)", margin: "0 0 16px" }}>
          This only logs your manual purchase for tracking. No order is placed on Binance.
        </p>

        <div className="field-row">
          <label>Entry price (USDT)</label>
          <input value={entryPrice} onChange={(e) => setEntryPrice(e.target.value)} type="number" />
        </div>
        <div className="field-row">
          <label>Quantity</label>
          <input value={quantity} onChange={(e) => setQuantity(e.target.value)} type="number" placeholder="e.g. 0.0021" />
        </div>
        <div className="field-row">
          <label>Investment amount (USDT)</label>
          <input value={investment} onChange={(e) => setInvestment(e.target.value)} type="number" placeholder="e.g. 100" />
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <div className="field-row" style={{ flex: 1 }}>
            <label>Target %</label>
            <input value={target} onChange={(e) => setTarget(e.target.value)} type="number" />
          </div>
          <div className="field-row" style={{ flex: 1 }}>
            <label>Stop-loss %</label>
            <input value={stopLoss} onChange={(e) => setStopLoss(e.target.value)} type="number" />
          </div>
        </div>

        {errorMsg && <p style={{ color: "var(--sell)", fontSize: 12 }}>{errorMsg}</p>}

        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <button className="btn btn-primary" disabled={saving} onClick={submit}>
            {saving ? "Saving…" : "Save entry"}
          </button>
          <button className="btn" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
}
