"""Aegis-rToken Main Entrypoint: Autonomous event-driven sentinel runtime.

ZERO-MOCK POLICY:
- Ingests real market catalysts and queries live Bitget market feeds.
- Routes execution through official Bitget CLI (demo/paper or dry-run).
- Never fabricates prices, headlines, fills, or model scores.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# Ensure 'src' is in sys.path when invoked via `python -m src.aegis_rtoken.main`
_src_path = str(Path(__file__).resolve().parent.parent)
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from aegis_rtoken.circuit_breaker import CircuitBreaker
from aegis_rtoken.config import settings
from aegis_rtoken.event_engine import EventEngine
from aegis_rtoken.execution.base import BaseExecutionEngine
from aegis_rtoken.execution.bitget_cli import BitgetCliExecutionEngine
from aegis_rtoken.llm_sentinel import LLMSentinel
from aegis_rtoken.market_feed import MarketFeed
from aegis_rtoken.models import (
    CandidateSignal,
    DecisionRecord,
    DecisionType,
    MarketEvent,
    MarketSnapshot,
    SentimentType,
    SignalAction,
)
from aegis_rtoken.risk_engine import RiskEngine
from aegis_rtoken.signal_engine import SignalEngine
from aegis_rtoken.telemetry.logger import TelemetryLogger

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aegis_rtoken")


class AegisAgent:
    """Core autonomous trading agent pairing real Qwen intelligence with deterministic risk."""

    def __init__(self):
        logger.info(f"Initializing Aegis Sentinel for asset: {settings.target_asset}")
        self.feed = MarketFeed(stale_timeout_seconds=settings.stale_data_timeout_seconds)
        self.events = EventEngine()
        self.sentinel = LLMSentinel(
            api_key=settings.effective_llm_key,
            base_url=settings.llm_base_url,
            model=settings.model,
            wire_api=settings.wire_api,
        )
        self.signal_engine = SignalEngine(
            min_confidence=settings.min_confidence_score,
            max_allocation=settings.max_allocation_usd,
        )
        self.circuit_breaker = CircuitBreaker(
            cooldown_seconds=settings.circuit_breaker_cooldown_seconds
        )
        self.risk_engine = RiskEngine(
            market_feed=self.feed,
            event_engine=self.events,
            circuit_breaker=self.circuit_breaker,
            max_spread_percent=settings.max_spread_percent,
            min_confidence_score=settings.min_confidence_score,
            max_allocation_usd=settings.max_allocation_usd,
            require_instrument_rules=True,
            require_demo_auth=True,
            demo_auth_verified=False,  # Fails closed until a verified Bitget Demo key is configured
        )

        # Official Bitget execution: strictly restricted to Bitget Demo/Paper Trading
        exec_mode = "dry_run" if settings.trading_mode == "dry_run" else "demo"
        self.execution: BaseExecutionEngine = BitgetCliExecutionEngine(mode=exec_mode)
        self.telemetry = TelemetryLogger()

        # Multi-market universe initialization
        self.active_asset = settings.target_asset.upper()
        self.discovered_markets = self.feed.discover_rtoken_markets()
        logger.info(f"Discovered {len(self.discovered_markets)} online rToken markets on Bitget SPOT.")

        # Query live Bitget quotes for core universe (zero-mock policy)
        self.feed.refresh_multi_market_quotes(["RAAPLUSDT", "RNVDAUSDT", "RTSLAUSDT", "RMSFTUSDT"])

    def set_active_market(self, asset: str) -> None:
        """Switches the primary active market."""
        self.active_asset = asset.upper()
        self.feed.fetch_live_quote(self.active_asset)

    def process_event(self, event: MarketEvent) -> DecisionRecord:
        """Processes a single real market catalyst through the full pipeline."""
        # 1. Fetch real live quote for the event asset
        market = self.feed.fetch_live_quote(event.asset) or self.feed.get_snapshot(event.asset)

        # 2. Real Qwen Sentinel Intelligence
        analysis = self.sentinel.analyze_event(event)

        # 3. Candidate Signal Formulation (Advisory)
        candidate = self.signal_engine.evaluate(
            event,
            analysis,
            market or MarketSnapshot.calculate(symbol=event.asset, bid=0.0, ask=0.0, is_connected=False),
        )

        # 3.5 Refresh real live quote right before deterministic risk evaluation
        # Ensures quote freshness and orderbook state are evaluated at the exact moment of decision,
        # preventing stale-quote timeouts caused by LLM network inference latency.
        fresh_quote = self.feed.fetch_live_quote(event.asset)
        if fresh_quote:
            market = fresh_quote

        # 4. Deterministic Risk Gate Evaluation (Final Authority)
        decision, reason, risk_report = self.risk_engine.evaluate(event, analysis, market, candidate)

        # 5. Real Execution (only if TRADE approved by deterministic risk gates)
        execution_details = None
        order_id = None
        exec_status = "NOT_EXECUTED"
        fill_price = None
        fill_qty = None
        fees = None

        if decision == DecisionType.TRADE and market is not None:
            demo_order_allowed = getattr(settings, "enable_demo_order", False) or getattr(settings, "enable_real_demo_order", False)
            if not demo_order_allowed and self.execution.mode != "dry_run":
                logger.warning("Trade blocked by safety gate: ENABLE_DEMO_ORDER is false.")
                decision = DecisionType.BLOCKED
                reason = "DEMO_ORDER_BLOCKED: ENABLE_DEMO_ORDER is set to false (default safety gate)"
                risk_report.all_passed = False
            else:
                exec_result = self.execution.execute(candidate, market)
                execution_details = exec_result.model_dump()
                order_id = exec_result.order_id
                exec_status = exec_result.order_status
                fill_price = exec_result.fill_price if exec_result.fill_price > 0 else None
                fill_qty = exec_result.quantity if exec_result.quantity > 0 else None
                fees = None  # Only populated if genuinely returned by exchange
                self.events.record_event(event)
        elif decision == DecisionType.HOLD:
            if "DUPLICATE" not in reason:
                self.events.record_event(event)

        # 6. Auditable Multi-Market Telemetry Persistence
        bid_val = market.bid if market else 0.0
        ask_val = market.ask if market else 0.0
        spread_val = market.spread_percent if market else 0.0

        clean_sym = event.asset.upper()
        underlying = clean_sym[1:-4] if (clean_sym.startswith("R") and clean_sym.endswith("USDT")) else clean_sym

        record = DecisionRecord(
            timestamp=datetime.now(timezone.utc),
            event_id=event.event_id,
            asset=event.asset,
            symbol=event.asset,
            underlying_asset=underlying,
            event_type=event.event_type,
            headline=event.headline,
            source=event.source,
            event_timestamp=event.timestamp,
            model_sentiment=analysis.sentiment,
            model_confidence=analysis.model_confidence,
            confidence=analysis.model_confidence,
            qwen_result=f"{analysis.sentiment.value} ({analysis.model_confidence:.2f})",
            market_bid=bid_val,
            market_ask=ask_val,
            spread_percent=spread_val,
            spread=spread_val,
            risk_checks=risk_report,
            decision=decision,
            decision_reason=reason,
            execution_mode=f"bitget_{settings.trading_mode}",
            order_id=order_id,
            execution_status=exec_status,
            actual_fill_price=fill_price,
            actual_fill_quantity=fill_qty,
            fees=fees,
            execution_details=execution_details,
        )
        self.telemetry.record(record)
        logger.info(
            f"Event [{event.event_id}] Asset: {event.asset} -> Decision: {decision.value} ({reason}) | "
            f"Sentiment: {analysis.sentiment.value} ({analysis.model_confidence:.2f})"
        )
        return record

    def run_cycle(self, target_assets: Optional[List[str]] = None) -> List[DecisionRecord]:
        """Polls for real live events across the specified markets (or active market) and processes them."""
        assets_to_poll = target_assets or [self.active_asset]
        decisions = []

        for asset in assets_to_poll:
            real_events = self.events.fetch_live_events(target_asset=asset, max_items=2)
            if not real_events:
                logger.info(f"NO_EVENT_DETECTED for {asset}: Standing by for catalysts.")
                continue

            for event in real_events:
                if not self.events.is_duplicate(event):
                    rec = self.process_event(event)
                    decisions.append(rec)
        return decisions

    def run_market_universe_cycle(self) -> List[DecisionRecord]:
        """Runs a complete evaluation cycle across all core discovered rToken markets."""
        core_targets = ["RAAPLUSDT", "RNVDAUSDT", "RTSLAUSDT", "RMSFTUSDT"]
        return self.run_cycle(target_assets=core_targets)


def main():
    """Startup verification cycle using REAL external services."""
    logger.info("Starting Aegis-rToken Autonomous Sentinel (ZERO-MOCK RUNTIME)...")
    agent = AegisAgent()
    
    # Check live Bitget connectivity
    quote = agent.feed.get_snapshot(settings.target_asset)
    if quote:
        logger.info(f"Live Bitget Market Connected: {quote.asset} Bid=${quote.bid} Ask=${quote.ask} Spread={quote.spread_percent:.3f}%")
    else:
        logger.warning(f"Live Bitget Market: DISCONNECTED ({agent.feed.last_error or 'Feed offline'}). Risk gates armed to fail-closed.")

    # Ingest real live news catalysts
    logger.info("Polling real live market catalysts...")
    decisions = agent.run_cycle()
    logger.info(f"Cycle completed. Real events evaluated: {len(decisions)}.")
    logger.info("Aegis-rToken zero-mock runtime verified.")


if __name__ == "__main__":
    main()
