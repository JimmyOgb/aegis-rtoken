# Paper Trading & Telemetry Specification

## Philosophy

Aegis-rToken operates strictly on a **Paper-Trading-First** discipline:
- No real capital execution during verification and demonstration phases.
- Real-time market data is ingested directly from Bitget market feeds.
- **Zero Fabrication**: All order submissions route through official Bitget Demo/Testnet (`bgc --paper-trading`). Local fake fills, synthetic balances, and fabricated order IDs are strictly prohibited.

## Execution Modes

1. **`demo` / `paper` (Default)**:
   - Evaluates real Bitget market data against incoming real events.
   - Dispatches orders to official Bitget Demo/Testnet via `bgc --paper-trading order --action place`.
   - Records genuine exchange order ID, status, and telemetry into `logs/decisions.jsonl`.
2. **`dry_run`**:
   - Assembles live Unified Trading Account order payloads via `bgc --paper-trading order --action place ... --dry-run`.
   - Validates exchange parameter compliance without queuing orders to the matching engine.
3. **`live`**:
   - Strictly disabled by default. Requires explicit manual override and live API keys.

## Telemetry Record Structure

Every processed event generates an append-only JSON record:

```json
{
  "event_id": "evt_8f1a23e9",
  "timestamp": "2026-09-09T14:00:00.000Z",
  "asset": "BTCUSDT",
  "event_type": "BREAKING_NEWS",
  "headline": "Federal Reserve announces liquidity facility framework",
  "sentiment": "BULLISH",
  "confidence": 0.88,
  "bid": 64250.0,
  "ask": 64255.0,
  "spread_percent": 0.0078,
  "risk_checks": {
    "connectivity": true,
    "freshness": true,
    "spread_within_limit": true,
    "confidence_sufficient": true,
    "allocation_within_limit": true,
    "deduplication_pass": true,
    "circuit_breaker_ok": true
  },
  "decision": "TRADE",
  "reason": "ALL_RISK_GATES_PASSED",
  "execution_mode": "paper",
  "execution_details": {
    "action": "BUY",
    "fill_price": 64255.0,
    "allocated_usd": 500.0
  }
}
```
