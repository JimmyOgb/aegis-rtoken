"""FastAPI Read-Oriented Server for Aegis Command Center."""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aegis_rtoken.config import settings
from aegis_rtoken.circuit_breaker import CircuitBreaker
from aegis_rtoken.event_engine import EventEngine
from aegis_rtoken.market_feed import MarketFeed
from aegis_rtoken.telemetry.logger import TelemetryLogger


def create_app(
    market_feed: Optional[MarketFeed] = None,
    event_engine: Optional[EventEngine] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    telemetry: Optional[TelemetryLogger] = None,
) -> FastAPI:
    """Creates the read-oriented dashboard API app."""
    app = FastAPI(
        title="Aegis-rToken Sentinel API",
        description="Read-oriented telemetry and status gateway for Aegis Command Center.",
        version="0.1.0",
    )

    # Enable CORS for Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

    # Shared instances (fallback to defaults if omitted)
    _feed = market_feed or MarketFeed()
    _events = event_engine or EventEngine()
    _cb = circuit_breaker or CircuitBreaker()
    _telemetry = telemetry or TelemetryLogger()

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "service": "aegis-rtoken",
            "mode": settings.trading_mode,
            "target_asset": settings.target_asset,
        }

    @app.get("/api/status")
    def get_status() -> Dict[str, Any]:
        from aegis_rtoken.event_engine import RTOKEN_EQUITY_MAP
        
        market_conn = _feed.is_connected()
        qwen_ok = bool(settings.effective_llm_key.strip())
        is_supported_asset = settings.target_asset.upper() in RTOKEN_EQUITY_MAP or (
            settings.target_asset.upper().startswith("R") and settings.target_asset.upper().endswith("USDT")
        )

        # Determine Bitget Demo status honestly (Zero-Mock Policy)
        # Credentials returning HTTP 400 exchange environment error are reported as BLOCKED / DEMO_AUTH_REQUIRED
        demo_creds_present = bool(settings.bitget_api_key.strip() and settings.bitget_secret_key.strip())
        demo_auth_verified = False  # Set to False due to confirmed Bitget exchange environment mismatch
        
        if not demo_creds_present:
            bitget_demo_label = "Bitget Demo: CREDENTIALS_MISSING"
        elif not demo_auth_verified:
            bitget_demo_label = "Bitget Demo: BLOCKED (DEMO_AUTH_REQUIRED)"
        else:
            bitget_demo_label = "Bitget Demo: CONNECTED"

        # Determine order label from recent decisions honestly
        recent_records = _telemetry.get_recent(limit=5)
        if any(r.execution_status == "CONFIRMED" for r in recent_records):
            order_label = "Demo Order Confirmed"
        elif any(r.decision.value == "BLOCKED" for r in recent_records):
            order_label = "Execution Blocked (Fail-Closed)"
        elif not demo_auth_verified:
            order_label = "Orders Blocked: Demo Auth Required"
        else:
            order_label = "0 Orders Placed (Demo Only)"

        # High-level aggregate status label
        if not is_supported_asset:
            status_label = "Unsupported Asset"
        elif not qwen_ok:
            status_label = "Qwen Unavailable"
        elif not market_conn:
            status_label = "Market Data Unavailable"
        elif not demo_auth_verified:
            status_label = "BLOCKED: DEMO_AUTH_REQUIRED"
        else:
            status_label = "Bitget Demo Active"

        # Discovered multi-market universe
        overview = _feed.get_market_overview()
        monitored_symbols = [m["symbol"] for m in overview]

        return {
            "agent_status": "MONITORING",
            "status_label": status_label,
            "bitget_demo_status": bitget_demo_label,
            "qwen_status": "Qwen Connected" if qwen_ok else "Qwen Unavailable",
            "market_data_status": "Market Data Connected" if market_conn else "Market Data Unavailable",
            "asset_support_status": f"Monitored Markets ({len(monitored_symbols)} rTokens)",
            "monitored_markets": monitored_symbols,
            "active_market": settings.target_asset.upper(),
            "market_universe_count": len(monitored_symbols),
            "order_status_label": order_label,
            "target_asset": settings.target_asset,
            "category": getattr(settings, "category", "SPOT"),
            "trading_mode": settings.trading_mode,
            "execution_environment": "BITGET_DEMO_PAPER",
            "live_trading_enabled": False,
            "demo_auth_verified": demo_auth_verified,
            "market_connected": market_conn,
            "circuit_breaker": _cb.status(),
            "telemetry_count": _telemetry.count(),
        }

    @app.get("/api/markets")
    def get_markets() -> List[Dict[str, Any]]:
        """Returns the real discovered rToken market universe with live quotes and telemetry."""
        overview = _feed.get_market_overview()
        recent_records = _telemetry.get_recent(limit=50)

        # Map latest decisions per symbol
        decision_map = {}
        for rec in reversed(recent_records):
            sym = (rec.symbol or rec.asset).upper()
            decision_map[sym] = rec

        enriched = []
        for m in overview:
            sym = m["symbol"].upper()
            rec = decision_map.get(sym)
            m_copy = dict(m)
            if rec:
                m_copy["latest_event"] = rec.headline
                m_copy["latest_qwen"] = f"{rec.model_sentiment.value} ({rec.model_confidence:.2f})"
                m_copy["latest_risk"] = rec.decision.value
            else:
                m_copy["latest_event"] = None
                m_copy["latest_qwen"] = None
                m_copy["latest_risk"] = "PENDING_CATALYST"
            enriched.append(m_copy)

        return enriched

    @app.get("/api/market")
    def get_market(symbol: Optional[str] = None) -> Dict[str, Any]:
        target = (symbol or settings.target_asset).upper()
        snapshot = _feed.get_snapshot(target) or _feed.fetch_live_quote(target)
        rules = _feed.get_instrument_rules(target) or _feed.fetch_instrument_rules(target) or {}

        if not snapshot:
            return {
                "asset": target,
                "symbol": target,
                "status": "UNAVAILABLE",
                "connected": False,
                "bid": 0.0,
                "ask": 0.0,
                "spread_percent": 0.0,
                "quote_freshness": 0.0,
                "min_order_qty": float(rules.get("minOrderQty") or 0.0001),
                "min_order_amount": float(rules.get("minOrderAmount") or 10.0),
                "base_coin": rules.get("baseCoin", target[:-4] if target.endswith("USDT") else target),
                "quote_coin": rules.get("quoteCoin", "USDT"),
            }

        dump = snapshot.model_dump()
        dump["min_order_qty"] = float(rules.get("minOrderQty") or 0.0001)
        dump["min_order_amount"] = float(rules.get("minOrderAmount") or 10.0)
        dump["base_coin"] = rules.get("baseCoin", target[:-4] if target.endswith("USDT") else target)
        dump["quote_coin"] = rules.get("quoteCoin", "USDT")
        dump["market_status"] = rules.get("status", "online")
        return dump

    @app.get("/api/decisions")
    def get_decisions(limit: int = 20, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        records = _telemetry.get_recent(limit=limit * 2 if symbol else limit)
        if symbol:
            target = symbol.upper()
            records = [r for r in records if (r.symbol or r.asset).upper() == target][:limit]
        return [r.model_dump() for r in records]

    @app.get("/api/circuit-breaker")
    def get_circuit_breaker() -> Dict[str, Any]:
        return _cb.status()

    return app


app = create_app()
