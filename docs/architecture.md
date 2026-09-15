# System Architecture

## Overview

Aegis-rToken is an autonomous event-driven trading sentinel architecture designed to operate with high reliability in volatile cryptocurrency markets.

The architecture strictly separates unstructured intelligence (LLM event parsing) from deterministic execution authority (risk engine and circuit breakers).

```text
                    ┌─────────────────────────┐
                    │     Frontend Dashboard  │
                    │   Next.js / Vercel Edge │
                    └────────────┬────────────┘
                                 │ HTTPS Read APIs
                                 ▼
                    ┌─────────────────────────┐
                    │      Aegis API Layer    │
                    │     Python / FastAPI    │
                    └────────────┬────────────┘
                                 │ Internal State Query
                                 ▼
                    ┌─────────────────────────┐
                    │    Aegis Agent Core     │
                    │   (Persistent Worker)   │
                    │                         │
                    │  1. Event Engine        │
                    │  2. LLM Sentinel (Qwen) │
                    │  3. Signal Engine       │
                    │  4. Risk Engine         │
                    │  5. Circuit Breaker     │
                    │  6. Execution Layer     │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
            Bitget Agent       Qwen API       Contracts /
             Hub (`bgc`)    (LLM Analysis)   Verification
```

## Component Boundaries

### 1. Frontend (Next.js / TypeScript)
- Deployed on **Vercel**.
- Serves the Command Center UI: monitoring asset state, live events, model reasoning, order book spread, risk checks, and paper execution records.
- **Security Boundary**: Contains zero exchange API keys, zero LLM secret keys, and zero order-placement authority. It only queries the Aegis API layer.

### 2. Aegis API Layer (FastAPI)
- Read-oriented telemetry gateway.
- Exposes endpoints:
  - `GET /health`
  - `GET /api/status`
  - `GET /api/market`
  - `GET /api/decisions`
  - `GET /api/telemetry`
- Does not expose arbitrary trade execution routes.

### 3. Aegis Agent Core
A long-running autonomous worker running inside a persistent environment (e.g. VPS or container):
1. **Event Engine**: Ingests, normalizes, deduplicates, and classifies market headlines and events.
2. **LLM Sentinel (Bitget Qwen Provider)**: Prompts `qwen3.8-max` via Bitget's Hackathon provider endpoint (`https://hackathon.bitgetops.com/v1/responses`, `wire_api="responses"`) for structured sentiment, confidence score, impact, and reasoning. Keys are loaded from `BITGET_QWEN_API_KEY`. Fails closed if unreachable or unauthenticated.
3. **Signal Engine**: Converts normalized events and orderbook context into candidate trade signals (`BUY`, `SELL`, `HOLD`).
4. **Risk Engine**: Deterministic gate enforcing max spread limits, minimum confidence threshold, maximum allocation limits, and freshness checks.
5. **Circuit Breaker**: Detects consecutive anomalies, extreme volatility, or feed dropouts, forcing cooldown state.
6. **Execution Engine**: Routes orders to official Bitget Demo/Testnet (`bgc --paper-trading`) or dry-run validation. No local fake fills.
7. **Telemetry**: Logs every decision (`TRADE`, `HOLD`, `BLOCKED`) with complete context into append-only JSONL files.

### 4. Contracts / Verification Layer
- Dedicated integration boundary in `contracts/`.
- Scaffolding for decentralized attestation, event verification, and tamper-proof strategy execution receipts.
- Trading operates seamlessly with or without active contract connections.
