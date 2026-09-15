"""Unit tests for Bitget execution engine: command synthesis, paper mode flags, and fail-closed safety."""

from unittest.mock import MagicMock, patch
from aegis_rtoken.execution.bitget_cli import BitgetCliExecutionEngine
from aegis_rtoken.models import CandidateSignal, MarketSnapshot, SentimentType, SignalAction


def test_bitget_cli_command_builder_paper_mode():
    """Verifies that paper mode adds the official --paper-trading flag to bgc."""
    engine = BitgetCliExecutionEngine(mode="paper")
    market = MarketSnapshot.calculate("BTCUSDT", bid=60000.0, ask=60010.0)
    candidate = CandidateSignal(
        action=SignalAction.BUY,
        asset="BTCUSDT",
        sentiment=SentimentType.BULLISH,
        model_confidence=0.85,
        reasoning="Paper trade buy test",
        target_allocation_usd=250.0,
    )
    cmd = engine.build_command(candidate, market)
    assert cmd[0] == "bgc"
    assert cmd[1] == "--paper-trading"
    assert "order" in cmd
    assert "--action" in cmd
    assert "place" in cmd
    assert "--symbol" in cmd
    assert "BTCUSDT" in cmd
    assert "--qty" in cmd
    assert "250.0" in cmd


def test_bitget_cli_command_builder_dry_run():
    """Verifies that dry_run mode appends --dry-run without fake fills."""
    engine = BitgetCliExecutionEngine(mode="dry_run")
    market = MarketSnapshot.calculate("BTCUSDT", bid=60000.0, ask=60010.0)
    candidate = CandidateSignal(
        action=SignalAction.SELL,
        asset="BTCUSDT",
        sentiment=SentimentType.BEARISH,
        model_confidence=0.85,
        reasoning="Dry run sell test",
        target_allocation_usd=300.0,
    )
    cmd = engine.build_command(candidate, market)
    assert "--dry-run" in cmd
    assert "--side" in cmd
    assert "sell" in cmd


def test_bitget_cli_hold_noop():
    """HOLD candidate produces a safe noop without CLI invocation."""
    engine = BitgetCliExecutionEngine(mode="paper")
    market = MarketSnapshot.calculate("BTCUSDT", bid=60000.0, ask=60010.0)
    candidate = CandidateSignal(
        action=SignalAction.HOLD,
        asset="BTCUSDT",
        sentiment=SentimentType.NEUTRAL,
        model_confidence=0.5,
        reasoning="Hold test",
        target_allocation_usd=0.0,
    )
    res = engine.execute(candidate, market)
    assert res.success is True
    assert res.order_id == "NONE"
    assert res.allocated_usd == 0.0


def test_bitget_cli_failure_fails_closed():
    """When the external Bitget CLI returns an error, no fake fill is produced."""
    engine = BitgetCliExecutionEngine(mode="paper")
    market = MarketSnapshot.calculate("BTCUSDT", bid=60000.0, ask=60010.0)
    candidate = CandidateSignal(
        action=SignalAction.BUY,
        asset="BTCUSDT",
        sentiment=SentimentType.BULLISH,
        model_confidence=0.90,
        reasoning="Buy failure test",
        target_allocation_usd=500.0,
    )

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = ""
    mock_proc.stderr = "Authentication failed: Invalid API key"

    with patch("subprocess.run", return_value=mock_proc):
        with patch("shutil.which", return_value="/usr/bin/bgc"):
            res = engine.execute(candidate, market)
            assert res.success is False
            assert res.order_id == "FAILED"
            assert res.fill_price == 0.0
            assert "Invalid API key" in res.details.get("error", "")


def test_live_trading_strictly_prohibited():
    """Verifies that attempting to initialize execution engine in live/mainnet mode raises ValueError."""
    import pytest
    for bad_mode in ["live", "mainnet", "prod", "production"]:
        with pytest.raises(ValueError, match="LIVE TRADING STRICTLY PROHIBITED"):
            BitgetCliExecutionEngine(mode=bad_mode)


def test_demo_auth_required_classification():
    """Verifies that exchange environment mismatch classifies order_status as DEMO_AUTH_REQUIRED."""
    engine = BitgetCliExecutionEngine(mode="demo")
    market = MarketSnapshot.calculate("RAAPLUSDT", bid=330.0, ask=330.2)
    candidate = CandidateSignal(
        action=SignalAction.BUY,
        asset="RAAPLUSDT",
        sentiment=SentimentType.BULLISH,
        model_confidence=0.85,
        reasoning="Demo auth mismatch test",
        target_allocation_usd=250.0,
    )

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = '{"ok": false, "error": "HTTP 400: exchange environment is incorrect"}'
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        with patch("shutil.which", return_value="/usr/bin/bgc"):
            res = engine.execute(candidate, market)
            assert res.success is False
            assert res.order_status == "DEMO_AUTH_REQUIRED"
            assert res.order_id == "FAILED"
            assert res.fill_price == 0.0

