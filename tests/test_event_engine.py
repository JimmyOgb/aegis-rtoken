"""Unit tests for EventEngine: normalization, deduplication, asset extraction, classification."""

from aegis_rtoken.event_engine import EventEngine


def test_event_normalization():
    engine = EventEngine()
    raw = {
        "title": "US Treasury proposes digital asset guidelines",
        "asset": "BTCUSDT",
        "source": "reuters",
    }
    event = engine.normalize(raw)
    assert event.asset == "BTCUSDT"
    assert event.headline == "US Treasury proposes digital asset guidelines"
    assert event.source == "reuters"
    assert event.event_id.startswith("evt_")


def test_duplicate_event_detection():
    engine = EventEngine()
    raw = {
        "headline": "Massive ETF approval officially announced",
        "asset": "BTCUSDT",
    }
    evt1 = engine.normalize(raw)
    assert engine.is_duplicate(evt1) is False
    engine.record_event(evt1)
    
    evt2 = engine.normalize(raw)
    assert engine.is_duplicate(evt2) is True


def test_asset_heuristic_extraction():
    engine = EventEngine()
    assert engine.extract_asset("Ethereum staking reaches all time high") == "ETHUSDT"
    assert engine.extract_asset("Solana break-point conference opens today") == "SOLUSDT"
    assert engine.extract_asset("Bitcoin network difficulty adjustment") == "BTCUSDT"
    assert engine.extract_asset("Generic economic commentary", default="BTCUSDT") == "BTCUSDT"


def test_event_classification():
    engine = EventEngine()
    e_reg = engine.normalize({"headline": "SEC announces regulatory settlement with exchange"})
    assert engine.classify_event(e_reg) == "REGULATORY"

    e_sec = engine.normalize({"headline": "Protocol drained in $20M exploit and hack"})
    assert engine.classify_event(e_sec) == "SECURITY_INCIDENT"

    e_macro = engine.normalize({"headline": "Federal Reserve leaves benchmark interest rates unchanged"})
    assert engine.classify_event(e_macro) == "MACROECONOMIC"
