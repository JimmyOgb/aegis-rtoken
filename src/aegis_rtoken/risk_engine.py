"""Risk Engine: Deterministic verification gates enforcing fail-closed risk policies.

ZERO-MOCK POLICY:
- If market data is missing or disconnected -> BLOCKED (DISCONNECTED_FEED).
- If market data is stale -> BLOCKED (STALE_ORDERBOOK).
- If Qwen Sentinel is unavailable, timed out, or errored -> BLOCKED (MODEL_UNAVAILABLE).
- If spread is excessive -> BLOCKED (SPREAD_EXCEEDED).
- If confidence is insufficient -> HOLD (LOW_CONFIDENCE).
- Never allows model intelligence or external triggers to bypass risk controls.
"""

import logging
from typing import Optional, Tuple

from aegis_rtoken.circuit_breaker import CircuitBreaker
from aegis_rtoken.config import settings
from aegis_rtoken.event_engine import EventEngine
from aegis_rtoken.market_feed import MarketFeed
from aegis_rtoken.models import (
    CandidateSignal,
    DecisionType,
    MarketEvent,
    MarketSnapshot,
    RiskGateReport,
    SentinelAnalysis,
    SentimentType,
    SignalAction,
)

logger = logging.getLogger(__name__)


class RiskEngine:
    """The final deterministic authority before execution."""

    def __init__(
        self,
        market_feed: MarketFeed,
        event_engine: EventEngine,
        circuit_breaker: CircuitBreaker,
        max_spread_percent: float = 0.8,
        min_confidence_score: float = 0.75,
        max_allocation_usd: float = 500.0,
        require_instrument_rules: bool = False,
        require_demo_auth: bool = False,
        demo_auth_verified: bool = False,
    ):
        self.market_feed = market_feed
        self.event_engine = event_engine
        self.circuit_breaker = circuit_breaker
        self.max_spread_percent = max_spread_percent
        self.min_confidence_score = min_confidence_score
        self.max_allocation_usd = max_allocation_usd
        self.require_instrument_rules = require_instrument_rules
        self.require_demo_auth = require_demo_auth
        self.demo_auth_verified = demo_auth_verified

    def set_demo_auth_status(self, verified: bool) -> None:
        self.demo_auth_verified = verified

    def set_require_demo_auth(self, required: bool) -> None:
        self.require_demo_auth = required

    def set_require_instrument_rules(self, required: bool) -> None:
        self.require_instrument_rules = required

    def evaluate(
        self,
        event: MarketEvent,
        analysis: SentinelAnalysis,
        market: Optional[MarketSnapshot],
        candidate: CandidateSignal,
    ) -> Tuple[DecisionType, str, RiskGateReport]:
        """Runs the deterministic fail-closed risk gates."""
        report = RiskGateReport()

        # Gate 0: Circuit Breaker State (Emergency safety halt checked first)
        report.circuit_breaker_ok = not self.circuit_breaker.is_active
        if not report.circuit_breaker_ok:
            return DecisionType.BLOCKED, "CIRCUIT_BREAKER_ACTIVE: System safety halt engaged", report

        # Gate 1: Model Availability & Integrity
        report.model_available = analysis.is_available
        if not report.model_available:
            reason = f"MODEL_UNAVAILABLE: {analysis.error_message or 'Qwen unreachable'}"
            return DecisionType.BLOCKED, reason, report

        # Gate 1b: Model Malformed / Out-of-bounds Check
        if analysis.sentiment not in (SentimentType.BULLISH, SentimentType.BEARISH, SentimentType.NEUTRAL):
            return DecisionType.BLOCKED, "MALFORMED_MODEL_OUTPUT: Invalid sentiment classification", report

        if analysis.model_confidence < 0.0 or analysis.model_confidence > 1.0:
            return DecisionType.BLOCKED, "MALFORMED_MODEL_OUTPUT: Confidence score outside [0, 1] range", report

        # Gate 2: Market Connectivity & Quote Presence
        report.connectivity = self.market_feed.is_connected() and (market is not None)
        if not report.connectivity:
            self.circuit_breaker.record_fault("DISCONNECTED_FEED")
            return DecisionType.BLOCKED, "DISCONNECTED_FEED: Real market quote unavailable", report

        assert market is not None  # Type narrowing for mypy/pyright

        # Gate 2b: Positive bid/ask check
        if market.bid <= 0 or market.ask <= 0 or market.ask < market.bid:
            return DecisionType.BLOCKED, "INVALID_MARKET_DATA: Non-positive or crossed bid/ask quotes", report

        # Gate 2c: Instrument Rules Tradability Check
        if self.require_instrument_rules:
            report.instrument_rules_ok = self.market_feed.has_valid_instrument_rules(event.asset)
            if not report.instrument_rules_ok:
                return (
                    DecisionType.BLOCKED,
                    "INSTRUMENT_RULES_UNAVAILABLE: Exchange tradable instrument rules not available or not online",
                    report,
                )

        # Gate 3: Freshness
        report.freshness = not self.market_feed.is_stale(event.asset)
        if not report.freshness:
            self.circuit_breaker.record_fault("STALE_ORDERBOOK")
            return DecisionType.BLOCKED, "STALE_ORDERBOOK: Market quote exceeded freshness threshold", report

        # Gate 4: Spread Limit
        report.spread_within_limit = market.spread_percent <= self.max_spread_percent
        if not report.spread_within_limit:
            return (
                DecisionType.BLOCKED,
                f"SPREAD_EXCEEDED ({market.spread_percent:.3f}% > {self.max_spread_percent:.3f}%)",
                report,
            )

        # Gate 5: Confidence Score
        report.confidence_sufficient = analysis.model_confidence >= self.min_confidence_score
        if not report.confidence_sufficient:
            return (
                DecisionType.HOLD,
                f"LOW_CONFIDENCE ({analysis.model_confidence:.2f} < {self.min_confidence_score:.2f})",
                report,
            )

        # Gate 6: Allocation Limit
        report.allocation_within_limit = candidate.target_allocation_usd <= self.max_allocation_usd
        if not report.allocation_within_limit:
            return (
                DecisionType.BLOCKED,
                f"ALLOCATION_EXCEEDED (${candidate.target_allocation_usd} > ${self.max_allocation_usd})",
                report,
            )

        # Gate 7: Target Asset Relevance
        if not self.event_engine.is_relevant_to_asset(event.headline, event.asset):
            return DecisionType.HOLD, "IRRELEVANT_EVENT: Catalyst does not reference target equity/rToken", report

        # Gate 8: Deduplication Check
        report.deduplication_pass = not self.event_engine.is_duplicate(event)
        if not report.deduplication_pass:
            return DecisionType.HOLD, "DUPLICATE_EVENT: Identical catalyst previously evaluated", report

        # Candidate Signal Direction Check
        if candidate.action == SignalAction.HOLD:
            return DecisionType.HOLD, "SIGNAL_ENGINE_PROPOSED_HOLD", report

        # Gate 9: Demo Authentication Readiness Gate
        if self.require_demo_auth:
            report.demo_auth_ok = self.demo_auth_verified
            if not report.demo_auth_ok:
                return (
                    DecisionType.BLOCKED,
                    "DEMO_AUTH_REQUIRED: Bitget Demo private authentication unavailable or environment mismatch (HTTP 400)",
                    report,
                )

        # All deterministic gates passed
        self.circuit_breaker.record_success()
        return DecisionType.TRADE, "ALL_RISK_GATES_PASSED", report
