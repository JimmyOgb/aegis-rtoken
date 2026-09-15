"""Domain models and data schemas for Aegis-rToken.

ZERO-MOCK POLICY: Every field represents genuine external data.
No synthetic or fabricated trading values.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SentimentType(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class DecisionType(str, Enum):
    TRADE = "TRADE"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


class SignalAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class EventType(str, Enum):
    """Event taxonomy appropriate for U.S. equities and tokenized rTokens."""
    EARNINGS = "EARNINGS"
    GUIDANCE = "GUIDANCE"
    SEC_FILING = "SEC_FILING"
    MATERIAL_NEWS = "MATERIAL_NEWS"
    M_AND_A = "M_AND_A"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE"
    REGULATORY = "REGULATORY"
    ANALYST_ACTION = "ANALYST_ACTION"
    PRODUCT_NEWS = "PRODUCT_NEWS"
    MACRO = "MACRO"
    MACROECONOMIC = "MACROECONOMIC"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    OTHER = "OTHER"


class MarketEvent(BaseModel):
    """Normalized real market catalyst preserving source provenance."""
    event_id: str
    asset: str
    event_type: str = EventType.OTHER.value
    headline: str
    source: str = "feed"
    source_url: str = ""
    published_at: Optional[datetime] = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    novelty_score: float = 1.0
    source_reliability: float = 1.0
    raw_payload: Optional[Dict[str, Any]] = None

    @property
    def timestamp(self) -> datetime:
        return self.published_at or self.ingested_at


class MarketSnapshot(BaseModel):
    """Real market quote snapshot directly from Bitget public market-data interface."""
    provider: str = "Bitget"
    symbol: str
    bid: float
    ask: float
    spread_percent: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    book_freshness: float = 0.0  # Freshness age in seconds
    connection_status: str = "CONNECTED"
    is_connected: bool = True

    @property
    def asset(self) -> str:
        return self.symbol

    @classmethod
    def calculate(
        cls,
        symbol: str,
        bid: float,
        ask: float,
        timestamp: Optional[datetime] = None,
        is_connected: bool = True,
        connection_status: str = "CONNECTED",
        book_freshness: float = 0.0,
        provider: str = "Bitget",
        asset: Optional[str] = None,
    ):
        target_symbol = symbol or asset or ""
        mid = (bid + ask) / 2.0 if (bid + ask) > 0 else 1.0
        spread_pct = ((ask - bid) / mid) * 100.0 if mid > 0 else 0.0
        return cls(
            provider=provider,
            symbol=target_symbol,
            bid=bid,
            ask=ask,
            spread_percent=round(spread_pct, 4),
            timestamp=timestamp or datetime.now(timezone.utc),
            book_freshness=round(book_freshness, 3),
            connection_status=connection_status,
            is_connected=is_connected,
        )


class SentinelAnalysis(BaseModel):
    """Structured Qwen intelligence analysis.
    
    CRITICAL: Trade bias is advisory only. LLM never has execution authority.
    """
    asset: str = ""
    is_available: bool = True
    sentiment: SentimentType = SentimentType.NEUTRAL
    model_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    impact: str = "UNKNOWN"  # LOW, MEDIUM, HIGH
    horizon: str = "SHORT_TERM"
    reasoning: str = ""
    trade_bias: SignalAction = SignalAction.HOLD
    model: str = "qwen"
    error_message: Optional[str] = None

    @property
    def confidence(self) -> float:
        return self.model_confidence


class CandidateSignal(BaseModel):
    """Advisory candidate signal derived from model intelligence and market state."""
    action: SignalAction
    asset: str
    sentiment: SentimentType
    model_confidence: float
    reasoning: str
    target_allocation_usd: float

    @property
    def confidence(self) -> float:
        return self.model_confidence


class RiskGateReport(BaseModel):
    """Deterministic safety verification report."""
    connectivity: bool = True
    freshness: bool = True
    spread_within_limit: bool = True
    confidence_sufficient: bool = True
    allocation_within_limit: bool = True
    deduplication_pass: bool = True
    circuit_breaker_ok: bool = True
    model_available: bool = True
    instrument_rules_ok: bool = True
    demo_auth_ok: bool = True

    @property
    def all_passed(self) -> bool:
        return (
            self.connectivity
            and self.freshness
            and self.spread_within_limit
            and self.confidence_sufficient
            and self.allocation_within_limit
            and self.deduplication_pass
            and self.circuit_breaker_ok
            and self.model_available
            and self.instrument_rules_ok
            and self.demo_auth_ok
        )


class MarketInfo(BaseModel):
    """Normalized tradable rToken market instrument snapshot and metadata."""
    symbol: str
    base_coin: str
    quote_coin: str = "USDT"
    underlying_ticker: str = ""
    status: str = "online"
    min_order_qty: float = 0.0001
    min_order_amount: float = 10.0
    price_precision: int = 2
    quantity_precision: int = 4
    bid: float = 0.0
    ask: float = 0.0
    spread_percent: float = 0.0
    quote_freshness: float = 0.0
    last_update_time: Optional[datetime] = None
    connection_status: str = "CONNECTED"  # CONNECTED | DISCONNECTED | UNAVAILABLE | BLOCKED
    is_connected: bool = True
    latest_event_headline: Optional[str] = None
    latest_qwen_sentiment: Optional[str] = None
    latest_risk_decision: Optional[str] = None


class DecisionRecord(BaseModel):
    """Auditable persistent decision record for every event with full provenance."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str
    asset: str
    symbol: str = ""
    underlying_asset: str = ""
    event_type: str = EventType.OTHER.value
    headline: str
    source: str = "feed"
    event_timestamp: Optional[datetime] = None
    model_sentiment: SentimentType = SentimentType.NEUTRAL
    model_confidence: float = 0.0
    confidence: float = 0.0
    qwen_result: str = ""
    market_bid: float = 0.0
    market_ask: float = 0.0
    spread_percent: float = 0.0
    spread: float = 0.0
    risk_checks: RiskGateReport
    decision: DecisionType
    decision_reason: str = ""
    execution_mode: str = "bitget_demo"
    order_id: Optional[str] = None
    execution_status: str = "NOT_EXECUTED"
    actual_fill_price: Optional[float] = None
    actual_fill_quantity: Optional[float] = None
    fees: Optional[float] = None
    execution_details: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        """Ensures fields are synced across legacy and multi-market properties."""
        if not self.symbol:
            self.symbol = self.asset
        if not self.confidence:
            self.confidence = self.model_confidence
        if not self.spread:
            self.spread = self.spread_percent
        if not self.event_timestamp:
            self.event_timestamp = self.timestamp
        if not self.qwen_result:
            self.qwen_result = f"{self.model_sentiment.value}:{self.confidence:.2f}"
        if not self.underlying_asset and self.symbol:
            clean = self.symbol.upper()
            if clean.startswith("R") and clean.endswith("USDT"):
                self.underlying_asset = clean[1:-4]
            else:
                self.underlying_asset = clean

    # Properties for backward compatibility with frontend and legacy calls
    @property
    def sentiment(self) -> SentimentType:
        return self.model_sentiment

    @property
    def reason(self) -> str:
        return self.decision_reason

    @property
    def bid(self) -> float:
        return self.market_bid

    @property
    def ask(self) -> float:
        return self.market_ask


class ExecutionResult(BaseModel):
    """Genuine execution confirmation from connected Bitget environment."""
    success: bool
    order_id: Optional[str] = None
    symbol: str = ""
    side: str = ""
    quantity: float = 0.0
    order_status: str = "UNKNOWN"
    fill_price: float = 0.0
    allocated_usd: float = 0.0
    mode: str = "demo"
    action: SignalAction = SignalAction.HOLD
    asset: str = ""
    api_error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
