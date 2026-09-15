# AegisrToken

> **Autonomous Multi-Market Event-Driven Sentinel for Tokenized U.S. Equities (rTokens)**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-green.svg)](https://www.python.org/)
[![Next.js: 15+](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Execution: Bitget Demo Only](https://img.shields.io/badge/Execution-Bitget%20Demo%20Only-orange.svg)](https://www.bitget.com)
[![Zero-Mock Policy](https://img.shields.io/badge/Policy-Zero--Mock-emerald.svg)](#zero-mock-policy)

**Website Brand**: [AegisrToken](https://github.com/JimmyOgb/aegis-rtoken)  
**Technical Repository**: `Aegis-rToken`  
**GitHub Repository**: `https://github.com/JimmyOgb/aegis-rtoken`  
**Hackathon Track**: Bitget AI Base Camp Hackathon — Track 2: Agentic Trading

---

## 1. Overview & Vision

**AegisrToken** is an autonomous event-driven trading sentinel engineered specifically for tokenized U.S. equities (`rTokens`) on the Bitget Unified Trading Architecture (UTA). It operates 24/7 across pre-market, regular market, and after-hours sessions, detecting real-time corporate and economic catalysts, running structured semantic reasoning via Bitget Qwen 3.8 Max, and subjecting all trade proposals to deterministic, fail-closed risk controls before routing them exclusively to **Bitget Demo / Paper Trading**.

### Core Philosophy
```text
The AI does not control the money.
The AI provides market intelligence.
The deterministic risk engine controls execution authority.
Bitget Demo / Paper Trading is the ONLY execution environment.
```

---

## 2. Zero-Mock Policy

AegisrToken operates under a strict, verifiable **Zero-Mock Policy**:

- **No Fabricated Prices**: Every market quote (bid, ask, spread, timestamp) is queried live from Bitget UTA SPOT order books (`https://api.bitget.com`).
- **No Fabricated Events**: Catalysts are polled in real time from financial news and corporate filings via Yahoo Finance RSS.
- **No Fabricated Sentiments**: Headline analysis is performed by genuine Bitget Qwen 3.8 Max inference (`https://hackathon.bitgetops.com/v1`).
- **No Fabricated Executions**: Orders are submitted exclusively through Bitget CLI (`bgc --paper-trading`, `paptrading: 1`).
- **Honest Fail-Closed State**: If Demo credentials mismatch or return `HTTP 400: exchange environment is incorrect`, the sentinel cleanly reports `BLOCKED: DEMO_AUTH_REQUIRED` with **0 orders submitted**. It never invents fake fills or simulated balances.

---

## 3. High-Level Architecture

```text
                        [ Yahoo Finance RSS Catalysts ]
                                       │ Real Headlines & Filings
                                       ▼
                         [ Bitget Qwen 3.8 Max LLM ]
                   (Unstructured Intelligence & Confidence Score)
                                       │
                                       ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      AegisrToken Deterministic Multi-Market Risk Engine                │
│                                                                                        │
│  [Market Freshness Gate]  [BBO Spread Gate]  [Instrument Rules Gate]  [Demo Auth Gate] │
│  [Circuit Breaker Gate]   [Confidence Gate]  [Notional Bounds Gate]   [Deduplication]  │
└──────────────────────────────────────┬─────────────────────────────────────────────────┘
                                       │
                         All Gates Pass / Fail Closed
                                       │
               ┌───────────────────────┴───────────────────────┐
               ▼                                               ▼
   [ Bitget CLI Execution ]                         [ Extended Telemetry ]
   (bgc --paper-trading only)                       (Audit Trail JSONL)
               │                                               │
               └───────────────────────┬───────────────────────┘
                                       │
                                       ▼
                         [ AegisrToken Web Dashboard ]
                    (Next.js 15 · Real BBO · Multi-Market)
```

---

## 4. Supported Monitored Markets

AegisrToken dynamically discovers and validates active tokenized U.S. equities from Bitget UTA SPOT metadata (`symbolType: stock`). Only verified online instruments are monitored:

| Market | Underlying | Base Coin | Quote Coin | Status | Real Data Source |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **`RAAPLUSDT`** | Apple Inc. (`AAPL`) | `rAAPL` | `USDT` | **ONLINE** | Bitget UTA SPOT BBO |
| **`RNVDAUSDT`** | NVIDIA Corp. (`NVDA`) | `rNVDA` | `USDT` | **ONLINE** | Bitget UTA SPOT BBO |
| **`RTSLAUSDT`** | Tesla, Inc. (`TSLA`) | `rTSLA` | `USDT` | **ONLINE** | Bitget UTA SPOT BBO |
| **`RMSFTUSDT`** | Microsoft Corp. (`MSFT`) | `rMSFT` | `USDT` | **ONLINE** | Bitget UTA SPOT BBO |
| **`RAMZNUSDT`** | Amazon.com Inc. (`AMZN`) | `rAMZN` | `USDT` | **ONLINE** | Bitget UTA SPOT BBO |
| **`RGOOGLUSDT`**| Alphabet Inc. (`GOOGL`)| `rGOOGL`| `USDT` | **ONLINE** | Bitget UTA SPOT BBO |
| **`RMETAUSDT`** | Meta Platforms (`META`)| `rMETA` | `USDT` | **ONLINE** | Bitget UTA SPOT BBO |

---

## 5. Deterministic Risk Gates

Before any trade signal reaches execution, it must pass 8 independent, deterministic gates:

1. **Connectivity Gate**: Verifies active live order book stream from Bitget UTA.
2. **Freshness Gate**: Rejects quotes older than `STALE_DATA_TIMEOUT_SECONDS` (default: 10s).
3. **Spread Gate**: Enforces bid-ask spread within `MAX_SPREAD_PERCENT` (default: 0.50%).
4. **Confidence Gate**: Requires Qwen sentiment confidence ≥ `CONFIDENCE_THRESHOLD` (default: 0.75).
5. **Notional Bounds Gate**: Asserts order size meets Bitget instrument minimums (`minOrderQty`, `minOrderAmount`).
6. **Deduplication Gate**: 60-minute sliding window Bloom filter prevents re-trading the same catalyst.
7. **Circuit Breaker Gate**: Trips automatically after 3 consecutive faults, halting execution for 300s.
8. **Demo Auth Gate**: Asserts valid Bitget Demo API credentials (`paptrading: 1`).

---

## 6. Project Structure

```text
aegis-rtoken/
├── .env.example                     # Environment template (placeholders only)
├── .gitignore                       # Git ignore enforcing zero credentials tracked
├── config.toml                      # Runtime configuration
├── LICENSE                          # MIT License
├── pyproject.toml                   # Python package configuration
├── requirements.txt                 # Backend dependencies
├── contracts/                       # Smart contract verification
│   └── AegisVerification.sol        # On-chain attestation contract
├── docs/                            # In-depth architectural guides
│   ├── architecture.md              # System architecture specification
│   ├── demo-script.md               # Video demo script & walkthrough
│   ├── paper-trading.md             # Paper-trading validation documentation
│   ├── risk-model.md                # Mathematical risk model & limits
│   └── strategy.md                  # Signal & catalyst strategy specification
├── frontend/                        # AegisrToken Web Dashboard (Next.js 15)
│   ├── .env.example                 # Frontend configuration template
│   ├── package.json                 # Next.js & React dependencies
│   ├── tsconfig.json                # TypeScript compiler configuration
│   ├── vercel.json                  # Vercel deployment specification
│   └── src/
│       ├── app/
│       │   ├── api/                 # Next.js same-origin API route handlers
│       │   │   ├── circuit-breaker/route.ts
│       │   │   ├── decisions/route.ts
│       │   │   ├── market/route.ts
│       │   │   ├── markets/route.ts
│       │   │   └── status/route.ts
│       │   ├── globals.css          # Tailwind styling
│       │   ├── layout.tsx           # AegisrToken root layout & metadata
│       │   └── page.tsx             # Main sentinel command center
│       ├── components/              # UI components
│       │   ├── ActiveMarketDetail.tsx
│       │   ├── ArchitecturePipeline.tsx
│       │   ├── DecisionPanel.tsx
│       │   ├── EventTimeline.tsx
│       │   ├── Header.tsx
│       │   ├── MetricCard.tsx
│       │   ├── MultiMarketOverview.tsx
│       │   └── RiskTelemetry.tsx
│       ├── hooks/useAegis.ts        # Polling & state synchronization hook
│       ├── lib/api.ts               # Same-origin API client
│       └── types/index.ts           # Shared TypeScript interfaces
├── logs/
│   └── .gitkeep                     # Git keep for local telemetry
├── scripts/
│   ├── run_agent.py                 # Long-running autonomous sentinel daemon
│   ├── run_demo.py                  # Single-cycle pipeline demo
│   ├── test_demo_pipeline.py        # Demo pipeline verification utility
│   └── verify_environment.py        # 7-point live integration audit script
├── src/aegis_rtoken/                # Backend core Python package
│   ├── __init__.py
│   ├── circuit_breaker.py           # Fault counting & exponential backoff
│   ├── config.py                    # Pydantic v2 settings & live mode prohibition
│   ├── event_engine.py              # Yahoo Finance RSS parser & deduplicator
│   ├── llm_sentinel.py              # Bitget Qwen 3.8 Max client
│   ├── main.py                      # Master AegisAgent event loop
│   ├── market_feed.py               # Bitget UTA multi-market live quote feed
│   ├── models.py                    # Immutable data models & telemetry schemas
│   ├── risk_engine.py               # Deterministic fail-closed risk gate evaluator
│   ├── signal_engine.py             # Sizing & candidate signal generator
│   ├── api/server.py                # FastAPI telemetry & read endpoints
│   ├── execution/bitget_cli.py      # Bitget CLI wrapper (--paper-trading only)
│   └── telemetry/logger.py          # JSONL structured audit trail logger
└── tests/                           # Pytest unit & integration test suite (32 tests)
    ├── test_api.py
    ├── test_circuit_breaker.py
    ├── test_event_engine.py
    ├── test_execution.py
    ├── test_llm_sentinel.py
    ├── test_market_feed.py
    ├── test_risk_engine.py
    ├── test_signal_engine.py
    └── test_telemetry.py
```

---

## 7. Environment Variables Matrix

| Variable | Purpose | Location | Secret? | Required |
| :--- | :--- | :--- | :---: | :---: |
| `BITGET_API_KEY` | Bitget Demo API key | Server only | **Yes** | Yes (for private demo orders) |
| `BITGET_SECRET_KEY` | Bitget Demo API secret | Server only | **Yes** | Yes (for private demo orders) |
| `BITGET_PASSPHRASE` | Bitget Demo API passphrase | Server only | **Yes** | Yes (for private demo orders) |
| `BITGET_QWEN_API_KEY` | Bitget Hackathon Qwen API key | Server only | **Yes** | Yes (for Qwen analysis) |
| `TRADING_MODE` | Execution mode (must be `demo`) | Server only | No | Yes (default: `demo`) |
| `TARGET_ASSET` | Default target rToken asset | Server only | No | Optional (default: `RAAPLUSDT`) |
| `CATEGORY` | Instrument category (must be `SPOT`) | Server only | No | Optional (default: `SPOT`) |
| `AEGIS_BACKEND_URL` | Upstream FastAPI backend URL | Next.js Server | No | Optional (for separate backend) |
| `NEXT_PUBLIC_AEGIS_API_URL`| Frontend API client URL override | Browser | No | Optional (empty = same-origin) |

> [!IMPORTANT]
> Never expose `BITGET_API_KEY`, `BITGET_SECRET_KEY`, `BITGET_PASSPHRASE`, or `BITGET_QWEN_API_KEY` to the browser or prefix them with `NEXT_PUBLIC_`.

---

## 8. Quickstart & Local Development

### Prerequisites
- Python 3.12+
- Node.js 18+
- Bitget CLI (`bgc`) installed and accessible in PATH

### Step 1: Clone Repository
```bash
git clone https://github.com/JimmyOgb/aegis-rtoken.git
cd aegis-rtoken
```

### Step 2: Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your BITGET_QWEN_API_KEY and Bitget Demo credentials

# Run factual live environment verification (7 audit checks)
python scripts/verify_environment.py

# Run test suite
pytest
```

### Step 3: Start Backend Sentinel Daemon
```bash
python scripts/run_agent.py
# Spawns Aegis Agent Core + FastAPI gateway at http://127.0.0.1:8000
```

### Step 4: Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Dashboard accessible at http://localhost:3000
```

---

## 9. Vercel Production Deployment

AegisrToken is configured with self-contained same-origin API route handlers in Next.js, allowing zero-dependency deployments on Vercel:

1. **Connect GitHub**: Import `https://github.com/JimmyOgb/aegis-rtoken` in the Vercel Dashboard.
2. **Root Directory**: Set Root Directory to `frontend`.
3. **Build Settings**: Framework: `Next.js`, Build Command: `npm run build`.
4. **Environment Variables**:
   - `BITGET_QWEN_API_KEY`: Configured server-side for real Qwen connectivity checks.
   - `BITGET_API_KEY`: Configured server-side for Demo auth status.
   - `BITGET_SECRET_KEY`: Configured server-side for Demo auth status.
   - `AEGIS_BACKEND_URL`: (Optional) Point to an independently hosted FastAPI runtime.
5. **Deploy**: The deployed site uses same-origin `/api/*` endpoints to query Bitget UTA SPOT order books directly over HTTPS with zero localhost dependencies.

---

## 10. Verified API Endpoints

Both the Python FastAPI backend and the Next.js same-origin production handlers implement these endpoints:

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/status` | `GET` | Overall agent health, Bitget Demo status, Qwen status, market universe count |
| `/api/markets` | `GET` | Discovered rToken universe with live BBO, spread %, bounds, and latest events |
| `/api/market?symbol=RAAPLUSDT` | `GET` | Granular snapshot for selected rToken with freshness and order bounds |
| `/api/decisions?symbol=...` | `GET` | Structured decision history and audit trail records |
| `/api/circuit-breaker` | `GET` | Circuit breaker status, fault count, and remaining cooldown |

---

## 11. Testing & Verification Results

### Backend Automated Test Suite
```bash
$ pytest
============================== test session starts ==============================
collected 32 items

tests/test_api.py ....                                                    [ 12%]
tests/test_circuit_breaker.py ....                                        [ 25%]
tests/test_event_engine.py ...                                            [ 34%]
tests/test_execution.py .....                                             [ 50%]
tests/test_llm_sentinel.py ...                                            [ 59%]
tests/test_market_feed.py .....                                           [ 75%]
tests/test_risk_engine.py .....                                           [ 90%]
tests/test_signal_engine.py ..                                            [ 96%]
tests/test_telemetry.py .                                                 [100%]

============================== 32 passed in 10.26s ==============================
```

### Frontend Production Build
```bash
$ npm run build
   ▲ Next.js 15.5.25
   Creating an optimized production build ...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
 ✓ Generating static pages (4/4)
Route (app)                                 Size     First Load JS
┌ ○ /                                       9.97 kB  113 kB
├ ƒ /api/circuit-breaker                    135 B    103 kB
├ ƒ /api/decisions                          135 B    103 kB
├ ƒ /api/market                             135 B    103 kB
├ ƒ /api/markets                            135 B    103 kB
└ ƒ /api/status                             135 B    103 kB
+ First Load JS shared by all               103 kB
```

---

## 12. Security & Safeguards

- **No Credential Leakage**: `.env` and `.env.local` are strictly `.gitignore`d. No API keys appear in client JavaScript or git history.
- **Fail-Closed Execution**: If any dependency (market data, Qwen, credentials) fails or times out, execution is immediately blocked.
- **Strict Mode Prohibition**: Pydantic models automatically raise validation errors if `TRADING_MODE` is set to `"live"`, `"prod"`, or `"mainnet"`.
- **Demo Flag Enforcement**: The execution layer asserts `--paper-trading` is present on every Bitget CLI command.

---

## 13. Limitations & Transparent Disclosures

- **Bitget Demo Environment Mismatch**: If the active API credentials belong to live/mainnet rather than Bitget Demo (or vice-versa), Bitget private endpoints return `HTTP 400: exchange environment is incorrect`. In this state, AegisrToken transparently fails closed, blocks order placement, and displays `BLOCKED: DEMO_AUTH_REQUIRED` with 0 orders placed.
- **Market Data Scope**: Only tokenized equities that Bitget currently lists and marks as `status: online` can be traded.
- **Catalyst Availability**: News frequency varies by underlying equity ticker.

---

## 14. 60–90 Second Demo Walkthrough

1. **Launch AegisrToken**: Open the dashboard to see the system status and the "BITGET DEMO / PAPER TRADING" indicator.
2. **Review Market Universe**: Observe the table displaying real-time live BBO prices for `RAAPLUSDT`, `RNVDAUSDT`, `RTSLAUSDT`, and `RMSFTUSDT`.
3. **Inspect Active Market**: Select `RAAPLUSDT` to view base/quote breakdowns, spread percentage, and Bitget order bounds.
4. **Trigger Catalyst Ingestion**: The system polls Yahoo Finance RSS for Apple-related news.
5. **Observe Qwen Analysis**: View structured sentiment classification and calibrated confidence score generated by Bitget Qwen 3.8 Max.
6. **Evaluate Deterministic Risk Gate**: See the 8-gate evaluation matrix pass or block the candidate signal.
7. **Verify Demo Routing**: Observe the order status: strictly routed to `--paper-trading` or blocked fail-closed if demo authentication is required.
8. **Inspect Telemetry**: Review the immutable audit trail in the Event Decision History.

---

## 15. License

This project is licensed under the [MIT License](LICENSE).
