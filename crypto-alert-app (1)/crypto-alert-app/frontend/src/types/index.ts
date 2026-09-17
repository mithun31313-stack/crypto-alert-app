export interface DashboardRow {
  symbol: string;
  display_name: string;
  price: number;
  change_24h_pct: number;
  trend: string;
  rsi: number | null;
  support: number | null;
  resistance: number | null;
  buy_zone_low: number | null;
  buy_zone_high: number | null;
  sell_zone_low: number | null;
  sell_zone_high: number | null;
  signal_label: string;
  signal_score: number;
  state: string;
}

export interface LiveSignal {
  symbol: string;
  label: string;
  score: number;
  price: number;
  zone_low: number;
  zone_high: number;
  reasons: string[];
  breakdown: Record<string, number>;
  ai_explanation: string;
}

export interface Trade {
  id: number;
  symbol: string;
  entry_price: number;
  quantity: number;
  investment_amount: number;
  target_price: number | null;
  stop_loss_price: number | null;
  status: string;
  current_price: number | null;
  current_value: number | null;
  profit_loss: number | null;
  profit_loss_pct: number | null;
  distance_to_target_pct: number | null;
  distance_to_stop_pct: number | null;
}

export interface LiveAlert {
  type: "BUY_WATCH" | "SELL_WATCH" | "STOP_LOSS" | "TICK";
  symbol: string;
  display_name?: string;
  label?: string;
  score?: number;
  price?: number;
  zone_low?: number;
  zone_high?: number;
  reasons?: string[];
  message?: string;
  change_24h_pct?: number;
}

export interface BacktestResult {
  symbol: string;
  timeframe: string;
  num_signals: number;
  entries: number;
  exits: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  avg_profit_pct: number;
  max_drawdown_pct: number;
  total_simulated_return_pct: number;
  disclaimer: string;
}
