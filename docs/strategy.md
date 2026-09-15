# Strategy Specification

## Strategy Overview

The **Aegis-rToken** strategy is an autonomous, event-driven trading sentinel focused on reacting to high-impact market catalysts while systematically rejecting false positives, stale information, and low-liquidity market regimes.

## Event Pipeline

### 1. Ingestion & Normalization
Incoming raw headlines and market events are normalized into a canonical schema:
- `event_id`: Deterministic hash of normalized content and timestamp window.
- `asset`: Target instrument (e.g., `BTCUSDT`).
- `source`: Source provider or webhook identifier.
- `headline`: Raw textual catalyst.
- `timestamp`: Event arrival time (UTC).

### 2. Novelty & Deduplication
To prevent execution on repetitive or recycled news:
- An in-memory rolling bloom filter / hash cache tracks recent event IDs over a configurable window (e.g., 60 minutes).
- Duplicate or near-identical events are immediately assigned a decision of `HOLD` with reason `DUPLICATE_EVENT`.

### 3. LLM Intelligence (Bitget Qwen Sentinel)
The event text is evaluated by the Bitget Qwen hackathon provider (`qwen3.8-max` via `https://hackathon.bitgetops.com/v1/responses`, `wire_api="responses"`) authenticated via `BITGET_QWEN_API_KEY` to extract structured attributes:
- `sentiment`: `BULLISH` | `BEARISH` | `NEUTRAL`
- `model_confidence`: Calibrated score between `0.0` and `1.0`
- `impact`: Estimated market impact rating (`LOW`, `MEDIUM`, `HIGH`)
- `horizon`: Time horizon (`SHORT_TERM`, `MEDIUM_TERM`, `LONG_TERM`)
- `reasoning`: Concise chain of reasoning explaining the assessment
- `trade_bias`: `BUY` | `SELL` | `HOLD`

### 4. Candidate Signal Formulation
A candidate signal (`BUY`, `SELL`, or `HOLD`) is proposed:
- `BULLISH` + Confidence ≥ `MIN_CONFIDENCE_SCORE` → Proposed `BUY`
- `BEARISH` + Confidence ≥ `MIN_CONFIDENCE_SCORE` → Proposed `SELL`
- Low confidence or `NEUTRAL` → `HOLD`

## Strict Hand-off to Risk Engine

The candidate signal is **strictly advisory**. Execution is never permitted directly from the signal engine. The candidate must successfully satisfy all deterministic checks in `risk_engine.py` and `circuit_breaker.py` before reaching the execution layer.
