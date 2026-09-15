"""Real Integration Demonstration Script.

ZERO-MOCK POLICY:
Demonstrates Aegis-rToken against actual configured live services.
Never fabricates catalysts, market prices, model sentiment, or simulated fills.
Reports explicit system states:
- WAITING FOR REAL EVENT
- MARKET DATA DISCONNECTED
- MODEL UNAVAILABLE / EXECUTION BLOCKED
- EXECUTION UNAVAILABLE
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))

from aegis_rtoken.config import settings
from aegis_rtoken.main import AegisAgent


def run_real_demo():
    print("=" * 70)
    print("Aegis-rToken Real Service Integration Demonstration")
    print("=" * 70)

    agent = AegisAgent()

    print(f"\n[1] Market Data Connectivity ({settings.target_asset}):")
    quote = agent.feed.get_snapshot(settings.target_asset)
    if quote and quote.is_connected:
        print(f"    STATUS   : CONNECTED ({quote.provider})")
        print(f"    BID / ASK: ${quote.bid:,.2f} / ${quote.ask:,.2f}")
        print(f"    SPREAD   : {quote.spread_percent:.3f}%")
    else:
        print("    STATUS   : MARKET DATA DISCONNECTED")
        print(f"    DETAILS  : {agent.feed.last_error or 'Bitget feed offline'}")
        print("    ACTION   : Risk engine armed to FAIL CLOSED")

    print("\n[2] Model Intelligence Gateway (Bitget Qwen):")
    if settings.effective_llm_key:
        print(f"    STATUS   : CONFIGURED ({settings.model})")
        print(f"    PROVIDER : {settings.model_provider_name} ({settings.model_provider})")
        print(f"    ENDPOINT : {settings.llm_base_url} (wire: {settings.wire_api})")
    else:
        print("    STATUS   : MODEL UNAVAILABLE")
        print("    DETAILS  : BITGET_QWEN_API_KEY not provided in environment")
        print("    ACTION   : All catalyst candidate signals will be BLOCKED")

    print("\n[3] Execution Routing (Bitget Demo/Testnet):")
    print(f"    MODE     : {agent.execution.mode.upper()}")
    print("    TARGET   : Official Bitget Demo/Testnet via `bgc --paper-trading`")

    print("\n[4] Real U.S. Equity Catalyst Ingestion:")
    print(f"    Ingesting real financial news for {settings.target_asset} (Yahoo Finance, CNBC, Dow Jones)...")
    live_events = agent.events.fetch_live_events(target_asset=settings.target_asset, max_items=3)

    if not live_events:
        print("    LATEST EVENT: WAITING FOR REAL EVENT")
    else:
        print(f"    Found {len(live_events)} real U.S. equity catalysts:")
        for idx, event in enumerate(live_events, 1):
            print(f"\n    --- Catalyst #{idx} ---")
            print(f"    Headline  : {event.headline}")
            print(f"    Type      : {event.event_type}")
            print(f"    Source    : {event.source} ({event.source_url[:60]}...)")
            print(f"    Published : {event.published_at or event.ingested_at}")
            
            # Process catalyst through real pipeline
            record = agent.process_event(event)
            print(f"    Model Eval: Sentiment={record.model_sentiment.value} | Confidence={record.model_confidence:.2f}")
            print(f"    Verdict   : {record.decision.value}")
            print(f"    Reason    : {record.decision_reason}")

    print("\n" + "=" * 70)
    print("Demonstration finished. Zero fake data was generated or presented.")
    print("=" * 70)


if __name__ == "__main__":
    run_real_demo()
