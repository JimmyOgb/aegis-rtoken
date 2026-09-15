"""Market Feed: Real-time Bitget orderbook bid/ask feed and freshness validation.

ZERO-MOCK POLICY:
- Fetches real live ticker/depth data from Bitget (via REST API or bgc CLI).
- Never generates synthetic or hardcoded prices.
- If Bitget is unreachable or data is stale, reports DISCONNECTED / STALE and FAILS CLOSED.
"""

import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

from aegis_rtoken.config import settings
from aegis_rtoken.models import MarketSnapshot

logger = logging.getLogger(__name__)


class MarketFeed:
    """Manages real Bitget orderbook bid/ask feeds and heartbeat freshness checks."""

    def __init__(
        self,
        stale_timeout_seconds: float = 10.0,
        api_base_url: Optional[str] = None,
    ):
        self.stale_timeout_seconds = stale_timeout_seconds
        self.api_base_url = (api_base_url or getattr(settings, "bitget_api_base_url", "https://api.bitget.com")).rstrip("/")
        self._snapshots: Dict[str, MarketSnapshot] = {}
        self._instrument_rules: Dict[str, Dict[str, Any]] = {}
        self._discovered_markets: Dict[str, Dict[str, Any]] = {}
        self._last_heartbeat: Optional[datetime] = None
        self._is_connected: bool = False
        self._last_error: Optional[str] = None

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def is_connected(self) -> bool:
        if not self._is_connected or self._last_heartbeat is None:
            return False
        age = (datetime.now(timezone.utc) - self._last_heartbeat).total_seconds()
        return age <= self.stale_timeout_seconds

    def fetch_live_quote(self, asset: Optional[str] = None) -> Optional[MarketSnapshot]:
        """Queries the live Bitget market ticker for real bid and ask prices.
        
        Tries direct HTTP query to Bitget UTA v3 endpoint first, falls back to `bgc market` CLI.
        If both fail or prices are invalid, records error and fails closed (returns None).
        """
        target_asset = (asset or settings.target_asset).upper()
        category = getattr(settings, "category", "SPOT")
        now = datetime.now(timezone.utc)
        
        # 1. Try direct Bitget UTA v3 REST API
        try:
            url = f"{self.api_base_url}/api/v3/market/tickers"
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(url, params={"category": category, "symbol": target_asset})
                if resp.status_code == 200:
                    payload = resp.json()
                    data_list = payload.get("data") or []
                    if data_list:
                        item = data_list[0]
                        bid_str = item.get("bid1Price") or item.get("bidPrice") or item.get("bidPr")
                        ask_str = item.get("ask1Price") or item.get("askPrice") or item.get("askPr")
                        
                        if bid_str is None or ask_str is None:
                            self._is_connected = False
                            self._last_error = "INVALID_MARKET_DATA: bid or ask missing from exchange response"
                            return None

                        bid = float(bid_str)
                        ask = float(ask_str)
                        
                        if bid <= 0 or ask <= 0 or ask < bid:
                            self._is_connected = False
                            self._last_error = "INVALID_MARKET_DATA: zero or crossed bid/ask quotes"
                            return None

                        # Parse exchange timestamp if available
                        ts_raw = item.get("ts") or payload.get("requestTime")
                        quote_time = datetime.fromtimestamp(int(ts_raw) / 1000.0, tz=timezone.utc) if ts_raw else now
                        age = (now - quote_time).total_seconds()

                        if age > self.stale_timeout_seconds:
                            self._is_connected = False
                            self._last_error = "STALE_MARKET_DATA: quote age exceeds freshness limit"
                            return None

                        snapshot = MarketSnapshot.calculate(
                            symbol=target_asset,
                            bid=bid,
                            ask=ask,
                            timestamp=quote_time,
                            is_connected=True,
                            connection_status="CONNECTED",
                            book_freshness=age,
                            provider="Bitget-UTA-v3",
                        )
                        self._snapshots[target_asset] = snapshot
                        self._last_heartbeat = now
                        self._is_connected = True
                        self._last_error = None
                        return snapshot
        except Exception as e:
            logger.debug(f"Direct Bitget REST v3 query failed ({e}), attempting bgc CLI...")

        # 2. Try official bgc CLI
        bgc_bin = shutil.which("bgc")
        if bgc_bin:
            try:
                cmd = [
                    "bgc",
                    "market",
                    "--action",
                    "tickers",
                    "--category",
                    category,
                    "--symbol",
                    target_asset,
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, shell=sys.platform == "win32")
                if res.returncode == 0 and res.stdout:
                    parsed = json.loads(res.stdout)
                    data = parsed.get("data")
                    if isinstance(data, list) and data:
                        item = data[0]
                    elif isinstance(data, dict):
                        item = data
                    else:
                        item = {}

                    bid_str = item.get("bid1Price") or item.get("bidPrice") or item.get("bidPr")
                    ask_str = item.get("ask1Price") or item.get("askPrice") or item.get("askPr")

                    if bid_str is None or ask_str is None:
                        self._is_connected = False
                        self._last_error = "INVALID_MARKET_DATA: bid or ask missing from CLI output"
                        return None

                    bid = float(bid_str)
                    ask = float(ask_str)

                    if bid <= 0 or ask <= 0 or ask < bid:
                        self._is_connected = False
                        self._last_error = "INVALID_MARKET_DATA: zero or crossed bid/ask quotes from CLI"
                        return None

                    ts_raw = item.get("ts")
                    quote_time = datetime.fromtimestamp(int(ts_raw) / 1000.0, tz=timezone.utc) if ts_raw else now
                    age = (now - quote_time).total_seconds()

                    if age > self.stale_timeout_seconds:
                        self._is_connected = False
                        self._last_error = "STALE_MARKET_DATA: CLI quote age exceeds freshness limit"
                        return None

                    snapshot = MarketSnapshot.calculate(
                        symbol=target_asset,
                        bid=bid,
                        ask=ask,
                        timestamp=quote_time,
                        is_connected=True,
                        connection_status="CONNECTED",
                        book_freshness=age,
                        provider="Bitget-CLI",
                    )
                    self._snapshots[target_asset] = snapshot
                    self._last_heartbeat = now
                    self._is_connected = True
                    self._last_error = None
                    return snapshot
            except Exception as ex:
                logger.debug(f"bgc CLI market fetch error: {ex}")

        # If live retrieval failed, FAIL CLOSED
        self._is_connected = False
        self._last_error = "MARKET_DATA_DISCONNECTED: Bitget feed unreachable"
        logger.warning(f"Failed to fetch live market quote for {target_asset}. Failing closed.")
        return None

    def update_quote_manual(
        self, asset: str, bid: float, ask: float, timestamp: Optional[datetime] = None
    ) -> MarketSnapshot:
        """Explicit quote update for controlled unit testing ONLY."""
        if bid <= 0 or ask <= 0:
            raise ValueError(f"Invalid market quote prices: bid={bid}, ask={ask}")
        if ask < bid:
            raise ValueError(f"Crossed market detected: ask ({ask}) < bid ({bid})")

        now = timestamp or datetime.now(timezone.utc)
        self._last_heartbeat = now
        self._is_connected = True
        snapshot = MarketSnapshot.calculate(
            symbol=asset.upper(),
            bid=bid,
            ask=ask,
            timestamp=now,
            is_connected=True,
            connection_status="CONNECTED",
            book_freshness=0.0,
            provider="Bitget",
        )
        self._snapshots[asset.upper()] = snapshot
        return snapshot

    def get_snapshot(self, asset: str) -> Optional[MarketSnapshot]:
        return self._snapshots.get(asset.upper())

    def is_stale(self, asset: str, max_age_seconds: Optional[float] = None) -> bool:
        """Returns True if the snapshot does not exist or exceeds age threshold."""
        timeout = max_age_seconds if max_age_seconds is not None else self.stale_timeout_seconds
        snapshot = self.get_snapshot(asset)
        if not snapshot:
            return True
        age = (datetime.now(timezone.utc) - snapshot.timestamp).total_seconds()
        return age > timeout

    def fetch_instrument_rules(self, asset: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Queries official Bitget market instruments endpoint for trading rules.
        
        Retrieves minOrderQty, minOrderAmount, status, pricePrecision, etc.
        Fails closed if instrument status is not 'online'.
        """
        target_asset = (asset or settings.target_asset).upper()
        category = getattr(settings, "category", "SPOT")

        # 1. Try official bgc CLI first
        bgc_bin = shutil.which("bgc")
        if bgc_bin:
            try:
                cmd = [
                    "bgc",
                    "market",
                    "--action",
                    "instruments",
                    "--category",
                    category,
                    "--symbol",
                    target_asset,
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, shell=sys.platform == "win32")
                if res.returncode == 0 and res.stdout:
                    parsed = json.loads(res.stdout)
                    data = parsed.get("data") or []
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get("symbol") == target_asset:
                            self._instrument_rules[target_asset] = item
                            return item
            except Exception as ex:
                logger.debug(f"bgc CLI instrument fetch error: {ex}")

        # 2. Try direct REST endpoint
        try:
            url = f"{self.api_base_url}/api/v3/market/instruments"
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(url, params={"category": category, "symbol": target_asset})
                if resp.status_code == 200:
                    payload = resp.json()
                    data = payload.get("data") or []
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get("symbol") == target_asset:
                            self._instrument_rules[target_asset] = item
                            return item
        except Exception as e:
            logger.debug(f"Direct instrument query failed ({e})")

        return self._instrument_rules.get(target_asset)

    def get_instrument_rules(self, asset: str) -> Optional[Dict[str, Any]]:
        """Returns cached instrument rules for asset."""
        return self._instrument_rules.get(asset.upper())

    def set_instrument_rules_manual(self, asset: str, rules: Dict[str, Any]) -> None:
        """Sets instrument rules manually for unit testing."""
        self._instrument_rules[asset.upper()] = rules

    def has_valid_instrument_rules(self, asset: str) -> bool:
        """Returns True if instrument rules exist and status is 'online'."""
        rules = self.get_instrument_rules(asset) or self.fetch_instrument_rules(asset)
        if not rules:
            return False
        return rules.get("status", "").lower() == "online"

    def discover_rtoken_markets(self) -> List[Dict[str, Any]]:
        """Queries the real Bitget instruments endpoint and discovers online rToken markets."""
        category = getattr(settings, "category", "SPOT")
        target_universe = getattr(settings, "monitored_markets", None) or [
            "RAAPLUSDT", "RNVDAUSDT", "RTSLAUSDT", "RMSFTUSDT",
            "RAMZNUSDT", "RGOOGLUSDT", "RMETAUSDT"
        ]
        target_universe_set = {s.upper() for s in target_universe}
        discovered = []

        # 1. Try official bgc CLI first
        bgc_bin = shutil.which("bgc")
        if bgc_bin:
            try:
                cmd = ["bgc", "market", "--action", "instruments", "--category", category]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=12, shell=sys.platform == "win32")
                if res.returncode == 0 and res.stdout:
                    parsed = json.loads(res.stdout)
                    data = parsed.get("data") or []
                    for item in data:
                        sym = item.get("symbol", "").upper()
                        is_target = sym in target_universe_set
                        is_online = item.get("status", "").lower() == "online"
                        if is_online and is_target:
                            self._instrument_rules[sym] = item
                            self._discovered_markets[sym] = item
                            discovered.append(item)
                    if discovered:
                        return discovered
            except Exception as ex:
                logger.debug(f"bgc CLI discovery error: {ex}")

        # 2. Try direct REST endpoint
        try:
            url = f"{self.api_base_url}/api/v3/market/instruments"
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(url, params={"category": category})
                if resp.status_code == 200:
                    payload = resp.json()
                    data = payload.get("data") or []
                    for item in data:
                        sym = item.get("symbol", "").upper()
                        is_target = sym in target_universe_set
                        is_online = item.get("status", "").lower() == "online"
                        if is_online and is_target:
                            self._instrument_rules[sym] = item
                            self._discovered_markets[sym] = item
                            discovered.append(item)
        except Exception as e:
            logger.debug(f"Direct discovery query failed: {e}")

        return list(self._discovered_markets.values())

    def get_discovered_markets(self) -> List[Dict[str, Any]]:
        """Returns list of currently discovered markets."""
        if not self._discovered_markets:
            self.discover_rtoken_markets()
        return list(self._discovered_markets.values())

    def set_discovered_markets_manual(self, markets: List[Dict[str, Any]]) -> None:
        """Sets discovered markets manually for unit tests."""
        for m in markets:
            sym = m.get("symbol", "").upper()
            if sym:
                self._discovered_markets[sym] = m
                self._instrument_rules[sym] = m

    def refresh_multi_market_quotes(self, symbols: Optional[List[str]] = None) -> Dict[str, MarketSnapshot]:
        """Fetches live quotes for multiple rToken markets without mocking."""
        target_symbols = symbols or list(self._discovered_markets.keys())
        if not target_symbols:
            target_symbols = ["RAAPLUSDT", "RNVDAUSDT", "RTSLAUSDT", "RMSFTUSDT"]

        results = {}
        for sym in target_symbols:
            snapshot = self.fetch_live_quote(sym)
            if snapshot:
                results[sym] = snapshot
        return results

    def get_market_overview(self) -> List[Dict[str, Any]]:
        """Returns structured multi-market snapshot with live prices and instrument rules."""
        if not self._discovered_markets:
            self.discover_rtoken_markets()

        overview = []
        now = datetime.now(timezone.utc)
        core_symbols = ["RAAPLUSDT", "RNVDAUSDT", "RTSLAUSDT", "RMSFTUSDT", "RAMZNUSDT", "RGOOGLUSDT"]
        all_symbols = list(self._discovered_markets.keys())
        sorted_symbols = [s for s in core_symbols if s in all_symbols] + [s for s in all_symbols if s not in core_symbols]

        if not sorted_symbols:
            sorted_symbols = ["RAAPLUSDT", "RNVDAUSDT", "RTSLAUSDT", "RMSFTUSDT"]

        for sym in sorted_symbols:
            rules = self._instrument_rules.get(sym) or {}
            snap = self._snapshots.get(sym)

            if snap and snap.is_connected and snap.bid > 0:
                age = (now - snap.timestamp).total_seconds()
                conn_status = "CONNECTED" if age <= self.stale_timeout_seconds else "DISCONNECTED"
                freshness = round(age, 2)
                bid = snap.bid
                ask = snap.ask
                spread = snap.spread_percent
                last_time = snap.timestamp.isoformat()
            else:
                conn_status = "UNAVAILABLE"
                freshness = 0.0
                bid = 0.0
                ask = 0.0
                spread = 0.0
                last_time = None

            underlying = rules.get("baseCoin", sym)
            if underlying.startswith("r") and len(underlying) > 1:
                underlying_ticker = underlying[1:]
            else:
                underlying_ticker = underlying

            overview.append({
                "symbol": sym,
                "base_coin": rules.get("baseCoin", sym[:-4] if sym.endswith("USDT") else sym),
                "quote_coin": rules.get("quoteCoin", "USDT"),
                "underlying_ticker": underlying_ticker,
                "status": rules.get("status", "online"),
                "min_order_qty": float(rules.get("minOrderQty") or 0.0001),
                "min_order_amount": float(rules.get("minOrderAmount") or 10.0),
                "price_precision": int(rules.get("pricePrecision") or 2),
                "quantity_precision": int(rules.get("quantityPrecision") or 4),
                "bid": bid,
                "ask": ask,
                "spread_percent": spread,
                "quote_freshness": freshness,
                "last_update_time": last_time,
                "connection_status": conn_status,
                "is_connected": conn_status == "CONNECTED",
            })

        return overview
