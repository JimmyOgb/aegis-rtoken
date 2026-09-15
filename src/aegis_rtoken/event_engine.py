"""Event Engine: Ingestion and normalization of REAL market news and events.

ZERO-MOCK POLICY:
- Ingests actual real-world crypto news catalysts (e.g., live RSS feeds from Cointelegraph).
- Preserves genuine source metadata (source, URL, published_at, ingested_at).
- If no real event is available, reports NO_EVENT. Never fabricates headlines.
"""

import email.utils
import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import httpx

from aegis_rtoken.models import EventType, MarketEvent

logger = logging.getLogger(__name__)

# Map of rToken symbols to underlying equity symbols and company name keywords
RTOKEN_EQUITY_MAP = {
    "RAAPLUSDT": {"ticker": "AAPL", "keywords": ["AAPL", "APPLE", "IPHONE", "TIM COOK", "MACBOOK", "IOS", "APP STORE"]},
    "RNVDAUSDT": {"ticker": "NVDA", "keywords": ["NVDA", "NVIDIA", "JENSEN HUANG", "GEFORCE", "BLACKWELL", "CUDA"]},
    "RTSLAUSDT": {"ticker": "TSLA", "keywords": ["TSLA", "TESLA", "ELON MUSK", "CYBERTRUCK", "GIGAFACTORY", "MODEL 3", "MODEL Y"]},
    "RMSFTUSDT": {"ticker": "MSFT", "keywords": ["MSFT", "MICROSOFT", "SATYA NADELLA", "AZURE", "WINDOWS", "OPENAI PARTNER"]},
    "RAMZNUSDT": {"ticker": "AMZN", "keywords": ["AMZN", "AMAZON", "JEFF BEZOS", "ANDY JASSY", "AWS", "PRIME"]},
    "RGOOGLUSDT": {"ticker": "GOOGL", "keywords": ["GOOGL", "GOOG", "ALPHABET", "GOOGLE", "SUNDAR PICHAI", "YOUTUBE", "GEMINI"]},
    "RMETAUSDT": {"ticker": "META", "keywords": ["META", "FACEBOOK", "MARK ZUCKERBERG", "INSTAGRAM", "WHATSAPP", "LLAMA", "OCULUS"]},
    "RSPYUSDT": {"ticker": "SPY", "keywords": ["SPY", "S&P", "S&P 500", "STANDARD & POOR'S", "SP500"]},
    "RQQQUSDT": {"ticker": "QQQ", "keywords": ["QQQ", "NASDAQ", "NASDAQ 100", "TECH STOCKS"]},
}


def get_underlying_ticker(asset: str) -> str:
    info = RTOKEN_EQUITY_MAP.get(asset.upper())
    if info:
        return info["ticker"]
    cleaned = asset.upper()
    if cleaned.startswith("R") and cleaned.endswith("USDT"):
        return cleaned[1:-4]
    return cleaned


class EventEngine:
    """Ingests, normalizes, deduplicates, and classifies real U.S. equity catalysts."""

    def __init__(self, deduplication_window_seconds: int = 3600):
        self.deduplication_window_seconds = deduplication_window_seconds
        self._seen_hashes: Set[str] = set()
        self._event_history: List[MarketEvent] = []

    def compute_event_hash(self, headline: str, asset: str) -> str:
        """Computes a normalized deterministic hash for an event."""
        clean_text = re.sub(r"\s+", " ", headline.strip().lower())
        raw_key = f"{asset.upper()}:{clean_text}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def is_relevant_to_asset(self, headline: str, target_asset: str) -> bool:
        """Determines whether a headline specifically references the target equity/rToken."""
        target_clean = target_asset.upper()
        mapping = RTOKEN_EQUITY_MAP.get(target_clean)
        headline_upper = headline.upper()

        if target_clean in headline_upper:
            return True

        # Support crypto targets in tests or explicit config
        if target_clean == "BTCUSDT" and any(k in headline_upper for k in ["BTC", "BITCOIN", "CRYPTO", "ETF"]):
            return True
        if target_clean == "ETHUSDT" and any(k in headline_upper for k in ["ETH", "ETHEREUM"]):
            return True
        if target_clean == "SOLUSDT" and any(k in headline_upper for k in ["SOL", "SOLANA"]):
            return True

        if mapping:
            ticker = mapping["ticker"]
            if re.search(rf"\b{re.escape(ticker)}\b", headline_upper):
                return True
            for kw in mapping["keywords"]:
                if kw in headline_upper:
                    return True
            return False

        underlying = get_underlying_ticker(target_clean)
        return bool(re.search(rf"\b{re.escape(underlying)}\b", headline_upper))

    def extract_asset(self, text: str, default: str = "RAAPLUSDT") -> str:
        """Extracts asset ticker from text or falls back to default."""
        text_upper = text.upper()
        for symbol, info in RTOKEN_EQUITY_MAP.items():
            if symbol in text_upper or info["ticker"] in text_upper:
                return symbol
            for kw in info["keywords"]:
                if kw in text_upper:
                    return symbol
        if "BITCOIN" in text_upper or "BTC" in text_upper:
            return "BTCUSDT"
        if "ETHEREUM" in text_upper or "ETH" in text_upper:
            return "ETHUSDT"
        if "SOLANA" in text_upper or "SOL" in text_upper:
            return "SOLUSDT"
        return default

    def classify_event(self, event: MarketEvent) -> str:
        return self.classify_event_text(event.headline)

    def classify_event_text(self, text: str) -> str:
        """Classifies the headline into the U.S. equity event taxonomy.
        
        Do not claim an event is an earnings event unless the real source supports that classification.
        """
        h = text.upper()

        # SECURITY_INCIDENT: Exploit, hack, vulnerability, drain
        if any(term in h for term in ["EXPLOIT", "HACK", "SECURITY INCIDENT", "DRAINED", "VULNERABILITY", "BREACH"]):
            return EventType.SECURITY_INCIDENT.value

        # EARNINGS: Strictly requires explicit earnings/profit reporting indicators
        if any(term in h for term in ["EARNINGS REPORT", "Q1 EARNINGS", "Q2 EARNINGS", "Q3 EARNINGS", "Q4 EARNINGS", "EPS BEAT", "EPS MISS", "REVENUE BEAT", "REVENUE MISS", "QUARTERLY EARNINGS", "QUARTERLY PROFIT", "POSTS EARNINGS", "REPORTS Q"]):
            return EventType.EARNINGS.value

        # GUIDANCE: Forward looking financial projections
        if any(term in h for term in ["GUIDANCE", "RAISES OUTLOOK", "CUTS OUTLOOK", "LOWERS OUTLOOK", "RAISES VIEW", "FORECASTS PROFIT", "FULL-YEAR FORECAST"]):
            return EventType.GUIDANCE.value

        # SEC_FILING: Regulatory forms and official disclosures
        if any(term in h for term in ["SEC FILING", "FORM 10-K", "FORM 10-Q", "FORM 8-K", "FORM 4", "13D", "13G", "EDGAR"]):
            return EventType.SEC_FILING.value

        # M_AND_A: Mergers, acquisitions, buyouts
        if any(term in h for term in ["ACQUIRES", "ACQUISITION", "TO BUY", "MERGER", "MERGES WITH", "TAKEOVER", "BUYOUT", "PURCHASE OF"]):
            return EventType.M_AND_A.value

        # MANAGEMENT_CHANGE: C-level and board moves
        if any(term in h for term in ["CEO", "CFO", "COO", "CTO", "STEPS DOWN", "RESIGNS", "APPOINTED", "NAMES NEW", "EXECUTIVE DEPARTURE", "BOARD OF DIRECTORS"]):
            return EventType.MANAGEMENT_CHANGE.value

        # REGULATORY: Antitrust, probes, lawsuits, fines
        if any(term in h for term in ["ANTITRUST", "DOJ", "FTC", "REGULATOR", "INVESTIGATION", "PROBE", "LAWSUIT", "LEGAL ACTION", "PATENT INFRINGEMENT", "FINED", "SETTLEMENT"]):
            return EventType.REGULATORY.value

        # ANALYST_ACTION: Ratings, upgrades, downgrades, price targets
        if any(term in h for term in ["UPGRADE", "DOWNGRADE", "PRICE TARGET", "OVERWEIGHT", "UNDERWEIGHT", "BUY RATING", "NEUTRAL RATING", "ANALYST ACTION", "INITIATES COVERAGE"]):
            return EventType.ANALYST_ACTION.value

        # PRODUCT_NEWS: Product launches, chip reveals, software releases
        if any(term in h for term in ["UNVEILS", "LAUNCHES", "ANNOUNCES NEW", "NEXT-GEN", "CHIP", "M4", "AI MODEL", "HARDWARE", "SOFTWARE UPDATE"]):
            return EventType.PRODUCT_NEWS.value

        # MACRO: Broader economic conditions
        if any(term in h for term in ["FEDERAL RESERVE", "FED CUTS", "FED HIKES", "INFLATION", "CPI", "JOBS DATA", "TREASURY YIELDS", "RECESSION", "INTEREST RATES"]):
            return EventType.MACROECONOMIC.value

        # MATERIAL_NEWS: General material business news
        if any(term in h for term in ["HALT", "RECALL", "BANKRUPTCY", "DEFAULT", "FACTORY SHUTDOWN", "SUPPLY CHAIN DISRUPTION"]):
            return EventType.MATERIAL_NEWS.value

        return EventType.OTHER.value

    def normalize(self, raw_data: Dict[str, Any], default_asset: str = "RAAPLUSDT") -> MarketEvent:
        """Normalizes external U.S. equity news payloads preserving provenance."""
        headline = str(raw_data.get("headline") or raw_data.get("title") or raw_data.get("text") or "").strip()
        asset = str(raw_data.get("asset") or default_asset).upper()
        source = str(raw_data.get("source") or "financial_feed")
        source_url = str(raw_data.get("source_url") or raw_data.get("link") or "")
        
        event_id = raw_data.get("event_id") or f"evt_{self.compute_event_hash(headline, asset)[:12]}"
        
        published_at = raw_data.get("published_at")
        if not isinstance(published_at, datetime):
            pub_date_str = raw_data.get("pubDate")
            if pub_date_str:
                try:
                    parsed_tuple = email.utils.parsedate_to_datetime(pub_date_str)
                    published_at = parsed_tuple.astimezone(timezone.utc)
                except Exception:
                    published_at = None
            else:
                published_at = None

        ingested_at = datetime.now(timezone.utc)
        event_type = raw_data.get("event_type") or self.classify_event_text(headline)

        event = MarketEvent(
            event_id=str(event_id),
            asset=asset,
            event_type=str(event_type),
            headline=headline,
            source=source,
            source_url=source_url,
            published_at=published_at,
            ingested_at=ingested_at,
            novelty_score=1.0,
            source_reliability=1.0,
            raw_payload=raw_data,
        )
        return event

    def fetch_live_events(
        self,
        feed_urls: Optional[List[str]] = None,
        target_asset: str = "RAAPLUSDT",
        max_items: int = 10,
    ) -> List[MarketEvent]:
        """Fetches real live events from external financial news feeds.
        
        Filters for events specifically relevant to the target equity / rToken.
        If no relevant live event is found, returns empty list (NO FAKE EVENTS).
        """
        underlying_ticker = get_underlying_ticker(target_asset)
        
        urls = feed_urls or [
            f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={underlying_ticker}&region=US&lang=en-US",
            "https://finance.yahoo.com/news/rssindex",
            "https://www.cnbc.com/id/10000664/device/rss/rss.html",
            "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        ]

        live_events: List[MarketEvent] = []
        headers = {"User-Agent": "Aegis-rToken-Research/1.0 (contact@aegis.local)"}

        for url in urls:
            try:
                with httpx.Client(timeout=6.0, follow_redirects=True, headers=headers) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.content)
                        items = root.findall(".//item")
                        for item in items:
                            title = (item.findtext("title") or "").strip()
                            link = (item.findtext("link") or "").strip()
                            pub_date = (item.findtext("pubDate") or "").strip()
                            
                            if not title:
                                continue

                            is_ticker_feed = f"s={underlying_ticker}" in url
                            if not is_ticker_feed and not self.is_relevant_to_asset(title, target_asset):
                                continue

                            event = self.normalize(
                                {
                                    "title": title,
                                    "source": "Yahoo-Finance" if "yahoo" in url else ("CNBC" if "cnbc" in url else "MarketWatch"),
                                    "source_url": link,
                                    "pubDate": pub_date,
                                    "asset": target_asset,
                                },
                                default_asset=target_asset,
                            )

                            if not self.is_duplicate(event):
                                live_events.append(event)
                                if len(live_events) >= max_items:
                                    break
            except Exception as e:
                logger.debug(f"Live event fetch from {url} error: {e}")

            if len(live_events) >= max_items:
                break

        return live_events

    def is_duplicate(self, event: MarketEvent) -> bool:
        """Checks if an event with identical content hash was previously observed."""
        evt_hash = self.compute_event_hash(event.headline, event.asset)
        return evt_hash in self._seen_hashes

    def record_event(self, event: MarketEvent) -> None:
        """Records an event into seen cache and history."""
        evt_hash = self.compute_event_hash(event.headline, event.asset)
        self._seen_hashes.add(evt_hash)
        self._event_history.append(event)
        if len(self._event_history) > 1000:
            self._event_history.pop(0)
