# Risk Model & Deterministic Gates

## Philosophy: Fail-Closed Risk Management

In autonomous financial systems, artificial intelligence must never possess unconstrained write/execution authority.

Aegis-rToken implements a **fail-closed** risk architecture:
- If market data is stale or connectivity drops → **BLOCKED**.
- If bid/ask spread exceeds threshold → **BLOCKED**.
- If LLM confidence is below threshold or invalid → **HOLD**.
- If maximum single-trade or cumulative allocation is exceeded → **BLOCKED**.
- If any internal exception occurs → **BLOCKED**.

## Deterministic Verification Gates

Every candidate signal produced by the Signal Engine must sequentially clear the following 7 gates:

| Gate | Criterion | Default Setting | Rejection Reason |
| :--- | :--- | :--- | :--- |
| **1. Connectivity** | Market feed websocket/heartbeat active within threshold | `< 10s` | `DISCONNECTED_FEED` |
| **2. Freshness** | Order book snapshot timestamp within maximum allowable latency | `< 5s` | `STALE_ORDERBOOK` |
| **3. Spread** | `(Ask - Bid) / Mid * 100 <= MAX_SPREAD_PERCENT` | `0.8%` | `SPREAD_EXCEEDED` |
| **4. Confidence** | LLM Sentinel score `>= MIN_CONFIDENCE_SCORE` | `0.75` | `LOW_CONFIDENCE` |
| **5. Allocation** | Intended position size `<= MAX_ALLOCATION_USD` | `$500` | `ALLOCATION_EXCEEDED` |
| **6. Deduplication** | Event not seen within rolling deduplication window | `60 mins` | `DUPLICATE_EVENT` |
| **7. Circuit Breaker** | System not currently in emergency cooldown or trip state | `Active = False` | `CIRCUIT_BREAKER_ACTIVE` |

## Decision States

1. **`TRADE`**: Cleared all 7 gates. Signal is dispatched to the configured execution engine (paper trading or dry-run).
2. **`HOLD`**: Neutral catalyst, low confidence, or unconvincing event. System remains in passive monitoring.
3. **`BLOCKED`**: Signal rejected due to safety violations (excessive spread, stale book, circuit breaker, allocation limits).
