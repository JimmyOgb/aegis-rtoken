# Demo & Verification Scenarios

This document outlines the standard verification scenarios designed to demonstrate Aegis-rToken's autonomous decision engine and risk isolation.

## Scenario Matrix

| Scenario | Injected Catalyst / Condition | Expected Model Assessment | Expected Risk Gate | System Decision |
| :--- | :--- | :--- | :--- | :--- |
| **1. Standard Valid Catalyst** | Genuine regulatory approval announcement | Bullish (Confidence: 0.91) | All 7 gates pass | **`TRADE`** (Paper execution logged) |
| **2. High Spread Protection** | Market volatility widens spread to 1.4% (limit 0.8%) | Bullish (Confidence: 0.88) | Gate 3 (Spread) fails | **`BLOCKED`** (`SPREAD_EXCEEDED`) |
| **3. Low-Confidence Rumor** | Unverified social media claim | Neutral/Uncertain (0.42) | Gate 4 (Confidence) fails | **`HOLD`** (`LOW_CONFIDENCE`) |
| **4. Duplicate Headline** | Re-broadcast of earlier catalyst | Bullish (Confidence: 0.89) | Gate 6 (Deduplication) fails | **`HOLD`** (`DUPLICATE_EVENT`) |
| **5. Stale Orderbook Dropout** | Order book feed stops updating (> 5s) | Bullish (Confidence: 0.85) | Gate 2 (Freshness) fails | **`BLOCKED`** (`STALE_ORDERBOOK`) |
| **6. Circuit Breaker Trip** | 3 consecutive extreme rejection alerts | Any | Gate 7 (Circuit Breaker) fails | **`BLOCKED`** (`CIRCUIT_BREAKER_ACTIVE`) |

## Running the Verification Scenarios

```bash
# Execute test suite verifying each scenario mechanically
pytest tests/ -v

# Run the live interactive demo simulator
python scripts/run_demo.py
```
