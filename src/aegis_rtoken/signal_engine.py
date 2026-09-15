"""Signal Engine: Synthesizes real event intelligence and market state into candidate signals.

ZERO-MOCK POLICY:
- If LLM Sentinel is unavailable or in error, automatically produces a HOLD candidate.
- Trade bias from LLM is strictly advisory.
- Risk Engine remains the sole deterministic execution authority.
"""

from aegis_rtoken.config import settings
from aegis_rtoken.models import (
    CandidateSignal,
    MarketEvent,
    MarketSnapshot,
    SentinelAnalysis,
    SentimentType,
    SignalAction,
)


class SignalEngine:
    """Generates candidate trading signals from real event intelligence.
    
    Candidate signals are purely advisory until evaluated by the Risk Engine.
    """

    def __init__(self, min_confidence: float = 0.75, max_allocation: float = 500.0):
        self.min_confidence = min_confidence
        self.max_allocation = max_allocation

    def evaluate(
        self,
        event: MarketEvent,
        analysis: SentinelAnalysis,
        market: MarketSnapshot,
    ) -> CandidateSignal:
        """Constructs an advisory candidate signal."""
        # If Qwen model was unavailable or returned an error, signal engine cannot recommend trade
        if not analysis.is_available:
            return CandidateSignal(
                action=SignalAction.HOLD,
                asset=event.asset,
                sentiment=SentimentType.NEUTRAL,
                model_confidence=0.0,
                reasoning=f"Model intelligence unavailable: {analysis.reasoning}",
                target_allocation_usd=0.0,
            )

        # Gate on real model confidence
        if analysis.model_confidence < self.min_confidence:
            return CandidateSignal(
                action=SignalAction.HOLD,
                asset=event.asset,
                sentiment=analysis.sentiment,
                model_confidence=analysis.model_confidence,
                reasoning=f"Model confidence ({analysis.model_confidence:.2f}) below threshold ({self.min_confidence:.2f})",
                target_allocation_usd=0.0,
            )

        if analysis.sentiment == SentimentType.BULLISH:
            return CandidateSignal(
                action=SignalAction.BUY,
                asset=event.asset,
                sentiment=analysis.sentiment,
                model_confidence=analysis.model_confidence,
                reasoning=f"Bullish real catalyst: {analysis.reasoning}",
                target_allocation_usd=self.max_allocation,
            )
        elif analysis.sentiment == SentimentType.BEARISH:
            return CandidateSignal(
                action=SignalAction.SELL,
                asset=event.asset,
                sentiment=analysis.sentiment,
                model_confidence=analysis.model_confidence,
                reasoning=f"Bearish real catalyst: {analysis.reasoning}",
                target_allocation_usd=self.max_allocation,
            )
        else:
            return CandidateSignal(
                action=SignalAction.HOLD,
                asset=event.asset,
                sentiment=analysis.sentiment,
                model_confidence=analysis.model_confidence,
                reasoning="Neutral sentiment catalyst does not justify execution",
                target_allocation_usd=0.0,
            )
