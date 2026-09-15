export type SentimentType = "BULLISH" | "BEARISH" | "NEUTRAL";
export type DecisionType = "TRADE" | "HOLD" | "BLOCKED";

export interface RiskGateReport {
  connectivity: boolean;
  freshness: boolean;
  spread_within_limit: boolean;
  confidence_sufficient: boolean;
  allocation_within_limit: boolean;
  deduplication_pass: boolean;
  circuit_breaker_ok: boolean;
  model_available?: boolean;
  instrument_rules_ok?: boolean;
  demo_auth_ok?: boolean;
}

export interface MarketSnapshot {
  asset: string;
  symbol?: string;
  bid: number;
  ask: number;
  spread_percent: number;
  timestamp?: string;
  is_connected: boolean;
  connected?: boolean;
  provider?: string;
  min_order_qty?: number;
  min_order_amount?: number;
  base_coin?: string;
  quote_coin?: string;
  market_status?: string;
  status?: string;
  quote_freshness?: number;
}

export interface MarketOverviewItem {
  symbol: string;
  underlying: string;
  base_coin: string;
  quote_coin: string;
  status: string;
  min_order_qty: number;
  min_order_amount: number;
  bid: number;
  ask: number;
  spread_percent: number;
  quote_freshness?: number;
  market_connected: boolean;
  latest_event: string | null;
  latest_qwen: string | null;
  latest_risk: string;
}

export interface DecisionRecord {
  event_id: string;
  timestamp: string;
  asset: string;
  symbol?: string;
  underlying_asset?: string;
  event_type: string;
  headline: string;
  sentiment: SentimentType;
  model_confidence: number;
  confidence?: number;
  bid: number;
  ask: number;
  spread_percent: number;
  spread?: number;
  risk_checks: RiskGateReport;
  decision: DecisionType;
  reason: string;
  execution_mode: string;
  execution_status?: string;
  order_id?: string | null;
  execution_details?: Record<string, unknown> | null;
}

export interface AgentStatus {
  agent_status: string;
  status_label?: string;
  bitget_demo_status?: string;
  qwen_status?: string;
  market_data_status?: string;
  asset_support_status?: string;
  order_status_label?: string;
  target_asset: string;
  category?: string;
  trading_mode: string;
  execution_environment?: string;
  live_trading_enabled?: boolean;
  demo_auth_verified?: boolean;
  monitored_markets?: string[];
  active_market?: string;
  market_universe_count?: number;
  market_connected: boolean;
  circuit_breaker: {
    is_tripped: boolean;
    consecutive_faults: number;
    trip_reason: string | null;
    remaining_cooldown_seconds: number;
  };
  telemetry_count: number;
}

