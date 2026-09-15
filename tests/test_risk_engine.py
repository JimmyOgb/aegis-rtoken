"""Unit tests for RiskEngine: deterministic gate enforcement and fail-closed policies."""

from datetime import datetime, timedelta, timezone
from aegis_rtoken.circuit_breaker import CircuitBreaker
from aegis_rtoken.event_engine import EventEngine
from aegis_rtoken.market_feed import MarketFeed
from aegis_rtoken.models import (
    CandidateSignal,
    DecisionType,
    MarketEvent,
    MarketSnapshot,
    SentinelAnalysis,
    SentimentType,
    SignalAction,
)
from aegis_rtoken.risk_engine import RiskEngine


def setup_fixtures():
    feed = MarketFeed(stale_timeout_seconds=5.0)
    events = EventEngine()
    cb = CircuitBreaker(cooldown_seconds=60, trip_threshold=3)
    risk = RiskEngine(
        market_feed=feed,
        event_engine=events,
        circuit_breaker=cb,
        max_spread_percent=0.8,
        min_confidence_score=0.75,
        max_allocation_usd=500.0,
    )
    
    event = MarketEvent(event_id="evt_test_1", asset="BTCUSDT", headline="Massive ETF approval confirmed")
    analysis = SentinelAnalysis(
        is_available=True,
        sentiment=SentimentType.BULLISH,
        model_confidence=0.85,
        impact="HIGH",
        reasoning="Strong institutional catalyst",
    )
    market = feed.update_quote_manual("BTCUSDT", bid=65000.0, ask=65020.0)  # ~0.03% spread
    candidate = CandidateSignal(
        action=SignalAction.BUY,
        asset="BTCUSDT",
        sentiment=SentimentType.BULLISH,
        model_confidence=0.85,
        reasoning="Valid candidate",
        target_allocation_usd=500.0,
    )
    return risk, feed, events, cb, event, analysis, market, candidate


def test_all_gates_pass():
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    decision, reason, report = risk.evaluate(event, analysis, market, candidate)
    assert decision == DecisionType.TRADE
    assert reason == "ALL_RISK_GATES_PASSED"
    assert report.all_passed is True


def test_model_unavailable_blocks():
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    unavailable_analysis = analysis.model_copy(update={"is_available": False, "error_message": "MODEL_KEY_MISSING"})
    decision, reason, report = risk.evaluate(event, unavailable_analysis, market, candidate)
    assert decision == DecisionType.BLOCKED
    assert "MODEL_UNAVAILABLE" in reason
    assert report.model_available is False


def test_spread_limit_blocked():
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    wide_market = feed.update_quote_manual("BTCUSDT", bid=65000.0, ask=66000.0)  # ~1.5% spread > 0.8%
    decision, reason, report = risk.evaluate(event, analysis, wide_market, candidate)
    assert decision == DecisionType.BLOCKED
    assert "SPREAD_EXCEEDED" in reason
    assert report.spread_within_limit is False


def test_low_confidence_hold():
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    low_conf_analysis = SentinelAnalysis(
        is_available=True,
        sentiment=SentimentType.BULLISH,
        model_confidence=0.60,
        impact="LOW",
        reasoning="Uncertain catalyst",
    )
    decision, reason, report = risk.evaluate(event, low_conf_analysis, market, candidate)
    assert decision == DecisionType.HOLD
    assert "LOW_CONFIDENCE" in reason
    assert report.confidence_sufficient is False


def test_allocation_exceeded_blocked():
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    large_candidate = candidate.model_copy(update={"target_allocation_usd": 1500.0})
    decision, reason, report = risk.evaluate(event, analysis, market, large_candidate)
    assert decision == DecisionType.BLOCKED
    assert "ALLOCATION_EXCEEDED" in reason
    assert report.allocation_within_limit is False


def test_stale_orderbook_blocked():
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    past_time = datetime.now(timezone.utc) - timedelta(seconds=15)
    stale_market = feed.update_quote_manual("BTCUSDT", bid=65000.0, ask=65020.0, timestamp=past_time)
    # Keep heartbeat fresh so Gate 1 passes and Gate 2 specifically triggers
    feed._last_heartbeat = datetime.now(timezone.utc)
    decision, reason, report = risk.evaluate(event, analysis, stale_market, candidate)
    assert decision == DecisionType.BLOCKED
    assert "STALE_ORDERBOOK" in reason
    assert report.freshness is False


def test_circuit_breaker_trip_blocks():
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    cb.trip("Manual trip for testing")
    decision, reason, report = risk.evaluate(event, analysis, market, candidate)
    assert decision == DecisionType.BLOCKED
    assert "CIRCUIT_BREAKER_ACTIVE" in reason
    assert report.circuit_breaker_ok is False


def test_instrument_rules_unavailable_blocks():
    from unittest.mock import patch
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    risk.set_require_instrument_rules(True)
    # When instrument rules are unavailable or offline -> must fail closed
    with patch.object(feed, "has_valid_instrument_rules", return_value=False):
        decision, reason, report = risk.evaluate(event, analysis, market, candidate)
        assert decision == DecisionType.BLOCKED
        assert "INSTRUMENT_RULES_UNAVAILABLE" in reason
        assert report.instrument_rules_ok is False

    # Once online instrument rules are confirmed -> gate passes
    with patch.object(feed, "has_valid_instrument_rules", return_value=True):
        decision, reason, report = risk.evaluate(event, analysis, market, candidate)
        assert decision == DecisionType.TRADE
        assert report.instrument_rules_ok is True


def test_demo_auth_unavailable_blocks():
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    risk.set_require_demo_auth(True)
    risk.set_demo_auth_status(False)
    decision, reason, report = risk.evaluate(event, analysis, market, candidate)
    assert decision == DecisionType.BLOCKED
    assert "DEMO_AUTH_REQUIRED" in reason
    assert report.demo_auth_ok is False

    # When demo auth is confirmed
    risk.set_demo_auth_status(True)
    decision, reason, report = risk.evaluate(event, analysis, market, candidate)
    assert decision == DecisionType.TRADE
    assert report.demo_auth_ok is True


def test_malformed_confidence_score_blocks():
    risk, feed, events, cb, event, analysis, market, candidate = setup_fixtures()
    malformed_analysis = analysis.model_copy(update={"model_confidence": 1.5})
    decision, reason, report = risk.evaluate(event, malformed_analysis, market, candidate)
    assert decision == DecisionType.BLOCKED
    assert "MALFORMED_MODEL_OUTPUT" in reason

