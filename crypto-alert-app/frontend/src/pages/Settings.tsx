import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Settings() {
  const [settings, setSettings] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.settings().then(setSettings);
  }, []);

  if (!settings) return <p style={{ color: "var(--ink-dim)" }}>Loading…</p>;

  async function updateWeight(kind: "buy_weights" | "sell_weights", key: string, value: number) {
    const next = { ...settings, [kind]: { ...settings[kind], [key]: value } };
    setSettings(next);
  }

  async function save() {
    setSaving(true);
    try {
      await api.patchSettings({
        buy_weights: settings.buy_weights,
        sell_weights: settings.sell_weights,
        default_cooldown_hours: settings.default_cooldown_hours,
        min_score_change_to_realert: settings.min_score_change_to_realert,
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-sub">Signal weighting, cooldowns and sensitivity — changes apply to future evaluations</p>
        </div>
        <button className="btn btn-primary" onClick={save} disabled={saving}>{saving ? "Saving…" : "Save changes"}</button>
      </div>

      <div className="two-col">
        <div className="panel">
          <h3 style={{ marginTop: 0, fontSize: 14 }}>BUY signal weights (points, sum ≈ 100)</h3>
          {Object.entries(settings.buy_weights).map(([key, val]) => (
            <div key={key} className="field-row">
              <label>{key.replace(/_/g, " ")}</label>
              <input type="number" value={val as number}
                onChange={(e) => updateWeight("buy_weights", key, parseInt(e.target.value))} />
            </div>
          ))}
        </div>

        <div className="panel">
          <h3 style={{ marginTop: 0, fontSize: 14 }}>Alert protection</h3>
          <div className="field-row">
            <label>Cooldown (hours)</label>
            <select
              value={settings.default_cooldown_hours}
              onChange={(e) => setSettings({ ...settings, default_cooldown_hours: parseInt(e.target.value) })}
            >
              {[1, 6, 12, 24].map((h) => <option key={h} value={h}>{h}</option>)}
            </select>
          </div>
          <div className="field-row">
            <label>Minimum score change to re-alert</label>
            <input
              type="number"
              value={settings.min_score_change_to_realert}
              onChange={(e) => setSettings({ ...settings, min_score_change_to_realert: parseInt(e.target.value) })}
            />
          </div>

          <h3 style={{ fontSize: 14 }}>SELL signal weights</h3>
          {Object.entries(settings.sell_weights).map(([key, val]) => (
            <div key={key} className="field-row">
              <label>{key.replace(/_/g, " ")}</label>
              <input type="number" value={val as number}
                onChange={(e) => updateWeight("sell_weights", key, parseInt(e.target.value))} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
