"""Unit tests for read-oriented FastAPI endpoints."""

from fastapi.testclient import TestClient
from aegis_rtoken.api.server import create_app
from aegis_rtoken.circuit_breaker import CircuitBreaker
from aegis_rtoken.event_engine import EventEngine
from aegis_rtoken.market_feed import MarketFeed
from aegis_rtoken.models import DecisionRecord, DecisionType, RiskGateReport, SentimentType
from aegis_rtoken.telemetry.logger import TelemetryLogger


def test_api_read_endpoints(tmp_path):
    feed = MarketFeed(stale_timeout_seconds=300.0)
    feed.update_quote_manual("BTCUSDT", bid=60000.0, ask=60010.0)
    events = EventEngine()
    cb = CircuitBreaker()
    telemetry = TelemetryLogger(log_dir=tmp_path)

    # Seed one real telemetry record structure
    record = DecisionRecord(
        event_id="test_api_evt",
        asset="BTCUSDT",
        headline="Regulatory approval granted",
        sentiment=SentimentType.BULLISH,
        model_confidence=0.85,
        bid=60000.0,
        ask=60010.0,
        spread_percent=0.016,
        risk_checks=RiskGateReport(),
        decision=DecisionType.TRADE,
        reason="ALL_RISK_GATES_PASSED",
        execution_mode="bitget_paper",
    )
    telemetry.record(record)

    app = create_app(
        market_feed=feed,
        event_engine=events,
        circuit_breaker=cb,
        telemetry=telemetry,
    )
    client = TestClient(app)

    # Health
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    # Status
    res = client.get("/api/status")
    assert res.status_code == 200
    status_data = res.json()
    assert status_data["market_connected"] is True
    assert status_data["telemetry_count"] == 1
    assert status_data["execution_environment"] == "BITGET_DEMO_PAPER"
    assert status_data["live_trading_enabled"] is False

    # Market (single)
    res = client.get("/api/market?symbol=BTCUSDT")
    assert res.status_code == 200
    assert res.json()["bid"] == 60000.0
    assert res.json()["ask"] == 60010.0

    # Markets (multi-market overview)
    res = client.get("/api/markets")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Decisions
    res = client.get("/api/decisions")
    assert res.status_code == 200
    decisions = res.json()
    assert len(decisions) == 1
    assert decisions[0]["event_id"] == "test_api_evt"

    # Circuit Breaker
    res = client.get("/api/circuit-breaker")
    assert res.status_code == 200
    assert res.json()["is_tripped"] is False
