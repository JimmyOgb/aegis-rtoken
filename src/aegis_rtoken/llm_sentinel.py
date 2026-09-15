"""LLM Sentinel: Event intelligence layer powered exclusively by Bitget Qwen hackathon provider.

ZERO-MOCK POLICY:
- If Qwen is unavailable, timed out, unconfigured, or returns an error, the Sentinel
  strictly returns `is_available=False` with error details, leading to execution being BLOCKED.
- NO heuristic fallback, NO synthetic sentiment, and NO manufactured confidence scores.
"""

import json
import logging
from typing import Optional
import httpx

from aegis_rtoken.config import settings
from aegis_rtoken.models import MarketEvent, SentinelAnalysis, SentimentType, SignalAction

logger = logging.getLogger(__name__)


class LLMSentinel:
    """Evaluates market events strictly via configured Bitget Qwen provider.
    
    CRITICAL: This is an intelligence layer ONLY, never an execution authority.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        wire_api: Optional[str] = None,
        timeout_seconds: float = 25.0,
    ):
        self.api_key = (api_key if api_key is not None else settings.effective_llm_key).strip()
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.model
        self.wire_api = (wire_api or settings.wire_api or "responses").lower()
        self.timeout_seconds = timeout_seconds

    def _redact(self, text: str) -> str:
        """Redacts API key from text or error messages to prevent leakage."""
        if self.api_key and self.api_key in text:
            return text.replace(self.api_key, "[REDACTED_API_KEY]")
        return text

    def analyze_event(self, event: MarketEvent) -> SentinelAnalysis:
        """Synchronously analyzes event via real Bitget Qwen endpoint.
        
        Fails closed on any error (no synthetic fallback).
        """
        if not self.api_key:
            logger.warning("Bitget Qwen API key (BITGET_QWEN_API_KEY) not configured. FAILING CLOSED.")
            return SentinelAnalysis(
                asset=event.asset,
                is_available=False,
                sentiment=SentimentType.NEUTRAL,
                model_confidence=0.0,
                impact="UNKNOWN",
                horizon="NONE",
                reasoning="Bitget Qwen API key not configured. Execution blocked.",
                trade_bias=SignalAction.HOLD,
                model=self.model,
                error_message="MODEL_KEY_MISSING",
            )

        prompt = (
            "You are an event-driven quantitative analyst evaluating real U.S. equity and tokenized rToken market catalysts.\n"
            "Evaluate the catalyst objectively. Extract asset, sentiment, model_confidence (0.0 to 1.0), "
            "market impact, horizon, concise reasoning, and trade_bias. Output ONLY raw JSON.\n\n"
            f"Asset: {event.asset}\n"
            f"Event Type: {event.event_type}\n"
            f"Headline: {event.headline}\n"
            f"Source: {event.source}\n"
            f"Published: {event.timestamp.isoformat()}\n\n"
            "Respond strictly in valid JSON format matching this schema:\n"
            "{\n"
            f'  "asset": "{event.asset}",\n'
            '  "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",\n'
            '  "model_confidence": <float between 0.0 and 1.0>,\n'
            '  "impact": "LOW" | "MEDIUM" | "HIGH",\n'
            '  "horizon": "SHORT_TERM" | "MEDIUM_TERM" | "LONG_TERM",\n'
            '  "reasoning": "<concise justification>",\n'
            '  "trade_bias": "BUY" | "SELL" | "HOLD"\n'
            "}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                if self.wire_api == "responses":
                    url = f"{self.base_url}/responses"
                    payload = {
                        "model": self.model,
                        "input": prompt,
                        "temperature": 0.1,
                    }
                else:
                    url = f"{self.base_url}/chat/completions"
                    payload = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a quantitative financial sentinel. Output ONLY raw JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"},
                    }

                resp = client.post(url, headers=headers, json=payload)

                if resp.status_code in (401, 403):
                    logger.error(f"Qwen authentication failure (HTTP {resp.status_code}). FAILING CLOSED.")
                    return SentinelAnalysis(
                        asset=event.asset,
                        is_available=False,
                        sentiment=SentimentType.NEUTRAL,
                        model_confidence=0.0,
                        impact="UNKNOWN",
                        reasoning=f"Qwen authentication failure (HTTP {resp.status_code}). Execution blocked.",
                        trade_bias=SignalAction.HOLD,
                        model=self.model,
                        error_message="MODEL_AUTH_ERROR",
                    )

                if resp.status_code != 200:
                    raw_err = self._redact(resp.text[:300])
                    logger.error(f"Qwen API returned error status: HTTP {resp.status_code}: {raw_err}")
                    return SentinelAnalysis(
                        asset=event.asset,
                        is_available=False,
                        sentiment=SentimentType.NEUTRAL,
                        model_confidence=0.0,
                        impact="UNKNOWN",
                        reasoning=f"Qwen endpoint error (HTTP {resp.status_code}: {raw_err}). Execution blocked.",
                        trade_bias=SignalAction.HOLD,
                        model=self.model,
                        error_message="MODEL_HTTP_ERROR",
                    )

                # Parse response payload based on wire_api format
                try:
                    data = resp.json()
                    content = ""

                    # 1. Responses wire API format: output list with message/output_text
                    if "output" in data and isinstance(data["output"], list):
                        for item in data["output"]:
                            if isinstance(item, dict) and item.get("type") == "message":
                                for piece in item.get("content", []):
                                    if isinstance(piece, dict) and piece.get("type") == "output_text":
                                        content += piece.get("text", "")
                                    elif isinstance(piece, str):
                                        content += piece
                                    elif isinstance(piece, dict) and "text" in piece:
                                        content += str(piece["text"])

                    # 2. Chat completions fallback
                    if not content and "choices" in data and len(data["choices"]) > 0:
                        choice = data["choices"][0]
                        if isinstance(choice, dict):
                            content = choice.get("message", {}).get("content", "")

                    content_clean = content.strip()
                    # Strip markdown code blocks if wrapped by model
                    if content_clean.startswith("```"):
                        lines = content_clean.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].strip() == "```":
                            lines = lines[:-1]
                        content_clean = "\n".join(lines).strip()

                    parsed = json.loads(content_clean)
                except Exception as parse_err:
                    redacted_err = self._redact(str(parse_err))
                    logger.error(f"Malformed Qwen response: {redacted_err}. FAILING CLOSED.")
                    return SentinelAnalysis(
                        asset=event.asset,
                        is_available=False,
                        sentiment=SentimentType.NEUTRAL,
                        model_confidence=0.0,
                        impact="UNKNOWN",
                        reasoning=f"Malformed Qwen JSON response ({redacted_err}). Execution blocked.",
                        trade_bias=SignalAction.HOLD,
                        model=self.model,
                        error_message="MODEL_INVALID_RESPONSE",
                    )

                # Strict validation of required fields
                required_fields = ["sentiment", "model_confidence", "impact", "horizon", "reasoning", "trade_bias"]
                if not all(field in parsed for field in required_fields):
                    logger.error(f"Missing required fields in Qwen response: {parsed.keys()}. FAILING CLOSED.")
                    return SentinelAnalysis(
                        asset=event.asset,
                        is_available=False,
                        sentiment=SentimentType.NEUTRAL,
                        model_confidence=0.0,
                        impact="UNKNOWN",
                        reasoning="Qwen response missing required schema fields. Execution blocked.",
                        trade_bias=SignalAction.HOLD,
                        model=self.model,
                        error_message="MODEL_INVALID_RESPONSE",
                    )

                sentiment_raw = str(parsed.get("sentiment", "")).upper()
                if sentiment_raw not in SentimentType.__members__:
                    logger.error(f"Invalid sentiment '{sentiment_raw}' in Qwen response. FAILING CLOSED.")
                    return SentinelAnalysis(
                        asset=event.asset,
                        is_available=False,
                        sentiment=SentimentType.NEUTRAL,
                        model_confidence=0.0,
                        impact="UNKNOWN",
                        reasoning=f"Invalid sentiment value '{sentiment_raw}'. Execution blocked.",
                        trade_bias=SignalAction.HOLD,
                        model=self.model,
                        error_message="MODEL_INVALID_RESPONSE",
                    )

                bias_raw = str(parsed.get("trade_bias", "")).upper()
                if bias_raw not in SignalAction.__members__:
                    logger.error(f"Invalid trade_bias '{bias_raw}' in Qwen response. FAILING CLOSED.")
                    return SentinelAnalysis(
                        asset=event.asset,
                        is_available=False,
                        sentiment=SentimentType.NEUTRAL,
                        model_confidence=0.0,
                        impact="UNKNOWN",
                        reasoning=f"Invalid trade_bias value '{bias_raw}'. Execution blocked.",
                        trade_bias=SignalAction.HOLD,
                        model=self.model,
                        error_message="MODEL_INVALID_RESPONSE",
                    )

                try:
                    conf = float(parsed.get("model_confidence", 0.0))
                except (ValueError, TypeError):
                    conf = 0.0

                conf = max(0.0, min(1.0, conf))

                return SentinelAnalysis(
                    asset=str(parsed.get("asset") or event.asset),
                    is_available=True,
                    sentiment=SentimentType(sentiment_raw),
                    model_confidence=conf,
                    impact=str(parsed.get("impact", "MEDIUM")),
                    horizon=str(parsed.get("horizon", "SHORT_TERM")),
                    reasoning=str(parsed.get("reasoning", "")),
                    trade_bias=SignalAction(bias_raw),
                    model=self.model,
                    error_message=None,
                )

        except httpx.TimeoutException:
            logger.error("Qwen API request timed out. FAILING CLOSED.")
            return SentinelAnalysis(
                asset=event.asset,
                is_available=False,
                sentiment=SentimentType.NEUTRAL,
                model_confidence=0.0,
                impact="UNKNOWN",
                reasoning="Qwen API request timed out. Execution blocked.",
                trade_bias=SignalAction.HOLD,
                model=self.model,
                error_message="MODEL_TIMEOUT",
            )
        except Exception as e:
            redacted_err = self._redact(str(e))
            logger.error(f"Qwen API invocation failed: {redacted_err}. FAILING CLOSED.")
            return SentinelAnalysis(
                asset=event.asset,
                is_available=False,
                sentiment=SentimentType.NEUTRAL,
                model_confidence=0.0,
                impact="UNKNOWN",
                reasoning=f"Qwen analysis failed: {redacted_err}. Execution blocked.",
                trade_bias=SignalAction.HOLD,
                model=self.model,
                error_message="MODEL_ERROR",
            )
