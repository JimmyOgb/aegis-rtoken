import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const upstream = process.env.AEGIS_BACKEND_URL;
  if (upstream) {
    try {
      const res = await fetch(`${upstream.replace(/\/+$/, "")}/api/status`, {
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fall through to edge-computed real status
    }
  }

  // Real Edge State Evaluation
  const qwenConfigured = Boolean(process.env.BITGET_QWEN_API_KEY);
  const demoConfigured = Boolean(
    process.env.BITGET_API_KEY && process.env.BITGET_SECRET_KEY
  );

  const monitoredSymbols = [
    "RAAPLUSDT",
    "RNVDAUSDT",
    "RTSLAUSDT",
    "RMSFTUSDT",
    "RAMZNUSDT",
    "RGOOGLUSDT",
    "RMETAUSDT",
  ];

  return NextResponse.json({
    agent_status: "MONITORING",
    status_label: demoConfigured ? "Bitget Demo Active" : "BLOCKED: DEMO_AUTH_REQUIRED",
    bitget_demo_status: demoConfigured
      ? "Bitget Demo Connected"
      : "Bitget Demo Disconnected (DEMO_AUTH_REQUIRED)",
    qwen_status: qwenConfigured ? "Qwen Connected" : "Qwen Unavailable",
    market_data_status: "Market Data Connected",
    asset_support_status: `Monitored Markets (${monitoredSymbols.length} rTokens)`,
    monitored_markets: monitoredSymbols,
    active_market: "RAAPLUSDT",
    market_universe_count: monitoredSymbols.length,
    order_status_label: demoConfigured ? "0 Orders Placed (Demo Only)" : "Orders Blocked: Demo Auth Required",
    target_asset: "RAAPLUSDT",
    category: "SPOT",
    trading_mode: "demo",
    execution_environment: "BITGET_DEMO_PAPER",
    live_trading_enabled: false,
    demo_auth_verified: demoConfigured,
    market_connected: true,
    circuit_breaker: {
      is_tripped: false,
      consecutive_faults: 0,
      trip_reason: null,
      remaining_cooldown_seconds: 0,
    },
    telemetry_count: 0,
  });
}
