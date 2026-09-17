type Props = { label: string };

const CLASS_MAP: Record<string, string> = {
  "WATCHING": "badge-watching",
  "WEAK BUY SIGNAL": "badge-weak",
  "BUY WATCH": "badge-buy",
  "STRONG BUY WATCH": "badge-strong-buy",
  "SELL WATCH": "badge-sell",
  "STOP LOSS ALERT": "badge-stop",
  "TARGET APPROACHING": "badge-target",
  "HOLDING": "badge-watching",
};

export default function SignalBadge({ label }: Props) {
  const cls = CLASS_MAP[label] ?? "badge-watching";
  return <span className={`badge ${cls}`}>{label}</span>;
}
