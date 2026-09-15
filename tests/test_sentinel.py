"""Unit tests for LLMSentinel: Bitget Qwen provider, wire_api=responses, fail-closed behavior, and redaction."""

from unittest.mock import MagicMock, patch
from aegis_rtoken.llm_sentinel import LLMSentinel
from aegis_rtoken.models import MarketEvent, SentimentType, SignalAction


def test_sentinel_unconfigured_fails_closed():
    """When API key is omitted, Sentinel strictly returns is_available=False."""
    sentinel = LLMSentinel(api_key="")
    event = MarketEvent(
        event_id="test_evt_1",
        asset="BTCUSDT",
        headline="Regulatory approval announced",
    )
    analysis = sentinel.analyze_event(event)
    assert analysis.is_available is False
    assert analysis.model_confidence == 0.0
    assert analysis.trade_bias == SignalAction.HOLD
    assert analysis.error_message == "MODEL_KEY_MISSING"


def test_sentinel_successful_responses_wire_api():
    """Valid Bitget Qwen responses wire API response is parsed into structured analysis."""
    sentinel = LLMSentinel(
        api_key="secret_test_key_123",
        base_url="https://hackathon.bitgetops.com/v1",
        model="qwen3.8-max",
        wire_api="responses",
    )
    event = MarketEvent(
        event_id="test_evt_2",
        asset="RAAPLUSDT",
        headline="Apple reports record earnings across all segments",
    )

    mock_responses_payload = {
        "id": "resp_test_123",
        "model": "qwen3.8-max",
        "object": "response",
        "status": "completed",
        "output": [
            {
                "id": "msg_reasoning",
                "type": "reasoning",
                "summary": [{"type": "summary_text", "text": "Blowout earnings boost demand."}],
            },
            {
                "id": "msg_content",
                "role": "assistant",
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": (
                            '{\n'
                            '  "asset": "RAAPLUSDT",\n'
                            '  "sentiment": "BULLISH",\n'
                            '  "model_confidence": 0.94,\n'
                            '  "impact": "HIGH",\n'
                            '  "horizon": "SHORT_TERM",\n'
                            '  "reasoning": "Record earnings beat drives immediate institutional demand.",\n'
                            '  "trade_bias": "BUY"\n'
                            '}'
                        ),
                    }
                ],
            },
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_responses_payload

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        analysis = sentinel.analyze_event(event)
        assert analysis.is_available is True
        assert analysis.sentiment == SentimentType.BULLISH
        assert analysis.model_confidence == 0.94
        assert analysis.impact == "HIGH"
        assert analysis.trade_bias == SignalAction.BUY
        assert "Record earnings" in analysis.reasoning
        assert analysis.model == "qwen3.8-max"

        # Verify wire_api="responses" uses {base_url}/responses with "input" payload
        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == "https://hackathon.bitgetops.com/v1/responses"
        assert "input" in call_kwargs["json"]
        assert call_kwargs["json"]["model"] == "qwen3.8-max"


def test_sentinel_chat_completions_fallback():
    """Valid legacy chat/completions response format is also handled."""
    sentinel = LLMSentinel(
        api_key="test_key",
        base_url="https://hackathon.bitgetops.com/v1",
        model="qwen3.8-max",
        wire_api="chat/completions",
    )
    event = MarketEvent(
        event_id="test_evt_2b",
        asset="BTCUSDT",
        headline="Institutional inflows surge",
    )

    mock_chat_json = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"sentiment": "BULLISH", "model_confidence": 0.88, '
                        '"impact": "HIGH", "horizon": "SHORT_TERM", '
                        '"reasoning": "Strong institutional demand catalyst", "trade_bias": "BUY"}'
                    )
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_chat_json

    with patch("httpx.Client.post", return_value=mock_resp):
        analysis = sentinel.analyze_event(event)
        assert analysis.is_available is True
        assert analysis.sentiment == SentimentType.BULLISH
        assert analysis.model_confidence == 0.88


def test_sentinel_http_error_redacts_key_and_fails_closed():
    """HTTP error from endpoint strictly causes fail-closed state and redacts secret key."""
    raw_key = "secret_key_abc_987"
    sentinel = LLMSentinel(api_key=raw_key)
    event = MarketEvent(
        event_id="test_evt_3",
        asset="BTCUSDT",
        headline="Market update headline",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = f"Internal Server Error for token {raw_key}"

    with patch("httpx.Client.post", return_value=mock_resp):
        analysis = sentinel.analyze_event(event)
        assert analysis.is_available is False
        assert analysis.model_confidence == 0.0
        assert analysis.error_message == "MODEL_HTTP_ERROR"
        assert raw_key not in analysis.reasoning
        assert "[REDACTED_API_KEY]" in analysis.reasoning


def test_sentinel_malformed_response_fails_closed():
    """Malformed or non-JSON output strictly causes fail-closed state."""
    sentinel = LLMSentinel(api_key="test_key")
    event = MarketEvent(
        event_id="test_evt_4",
        asset="BTCUSDT",
        headline="Market update headline",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"output": [{"type": "message", "content": [{"type": "output_text", "text": "Not valid JSON"}]}]}

    with patch("httpx.Client.post", return_value=mock_resp):
        analysis = sentinel.analyze_event(event)
        assert analysis.is_available is False
        assert analysis.model_confidence == 0.0
        assert analysis.error_message in ("MODEL_INVALID_RESPONSE", "MODEL_ERROR")


def test_sentinel_missing_fields_fails_closed():
    """JSON response missing mandatory schema fields strictly causes fail-closed state."""
    sentinel = LLMSentinel(api_key="test_key")
    event = MarketEvent(
        event_id="test_evt_5",
        asset="BTCUSDT",
        headline="Market update headline",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": '{"sentiment": "BULLISH"}'}],
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        analysis = sentinel.analyze_event(event)
        assert analysis.is_available is False
        assert analysis.error_message == "MODEL_INVALID_RESPONSE"

