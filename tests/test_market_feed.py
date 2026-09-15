"""Unit tests for MarketFeed: quotes, spread calculation, freshness, and connectivity."""

import pytest
from datetime import datetime, timedelta, timezone
from aegis_rtoken.market_feed import MarketFeed


def test_market_feed_spread_calculation():
    feed = MarketFeed(stale_timeout_seconds=5.0)
    snapshot = feed.update_quote_manual("BTCUSDT", bid=50000.0, ask=50050.0)
    assert snapshot.asset == "BTCUSDT"
    assert snapshot.bid == 50000.0
    assert snapshot.ask == 50050.0
    assert 0.09 < snapshot.spread_percent < 0.11


def test_crossed_market_rejection():
    feed = MarketFeed()
    with pytest.raises(ValueError, match="Crossed market detected"):
        feed.update_quote_manual("BTCUSDT", bid=50100.0, ask=50000.0)


def test_invalid_quote_prices():
    feed = MarketFeed()
    with pytest.raises(ValueError, match="Invalid market quote prices"):
        feed.update_quote_manual("BTCUSDT", bid=-10.0, ask=50000.0)


def test_stale_quote_detection():
    feed = MarketFeed(stale_timeout_seconds=2.0)
    past_time = datetime.now(timezone.utc) - timedelta(seconds=5)
    feed.update_quote_manual("BTCUSDT", bid=50000.0, ask=50010.0, timestamp=past_time)
    assert feed.is_stale("BTCUSDT") is True


def test_disconnected_feed_fails_closed():
    feed = MarketFeed()
    assert feed.is_connected() is False  # Starts disconnected until real live quote arrives
    assert feed.get_snapshot("BTCUSDT") is None
