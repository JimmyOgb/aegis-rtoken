"""Connectivity test for Bitget Qwen hackathon provider.

Verifies real HTTP status, model response received, response parsing, structured
sentiment output, latency, and redacted error handling using wire_api="responses".
"""

import os
import sys
import time
import json
from pathlib import Path
import httpx
from dotenv import dotenv_values

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))

from aegis_rtoken.config import settings


def redact_key(text: str, key: str) -> str:
    """Redacts API key from text or error representations."""
    if key and key in text:
        return text.replace(key, "[REDACTED_API_KEY]")
    return text


def run_test():
    # Load configuration
    config = dotenv_values(".env")
    key = os.environ.get("BITGET_QWEN_API_KEY") or config.get("BITGET_QWEN_API_KEY") or settings.effective_llm_key
    base_url = (
        os.environ.get("LLM_BASE_URL")
        or config.get("LLM_BASE_URL")
        or settings.llm_base_url
    ).rstrip("/")
    model = os.environ.get("LLM_MODEL") or config.get("LLM_MODEL") or settings.model
    wire_api = (
        os.environ.get("WIRE_API")
        or config.get("WIRE_API")
        or getattr(settings, "wire_api", "responses")
    ).lower()

    endpoint = f"{base_url}/responses" if wire_api == "responses" else f"{base_url}/chat/completions"

    print("=" * 65)
    print("Bitget Qwen Real Connectivity Test (Hackathon Provider)")
    print("=" * 65)
    print(f"Provider   : {settings.model_provider_name} ({settings.model_provider})")
    print(f"Base URL   : {base_url}")
    print(f"Endpoint   : {endpoint}")
    print(f"Model      : {model}")
    print(f"Wire API   : {wire_api}")
    print(f"Key Config : {'CONFIGURED (REDACTED)' if key else 'MISSING (BITGET_QWEN_API_KEY not found)'}")

    if not key:
        print("\nERROR: No BITGET_QWEN_API_KEY found in environment or .env")
        print("FAIL-CLOSED: Trading intelligence unavailable.")
        return False, None

    prompt = (
        "You are an event-driven quantitative analyst evaluating real U.S. equity and tokenized rToken market catalysts.\n"
        "Evaluate the catalyst objectively. Extract asset, sentiment, model_confidence (0.0 to 1.0), "
        "market impact, horizon, concise reasoning, and trade_bias. Output ONLY raw JSON.\n\n"
        "Asset: RAAPLUSDT\n"
        "Event Type: REGULATORY_APPROVAL\n"
        "Headline: Global regulators grant comprehensive approval for tokenized equity trading expansion\n"
        "Source: FinancialTimes\n"
        "Published: 2026-09-13T12:00:00Z\n\n"
        "Respond strictly in valid JSON format matching this schema:\n"
        "{\n"
        '  "asset": "RAAPLUSDT",\n'
        '  "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",\n'
        '  "model_confidence": <float between 0.0 and 1.0>,\n'
        '  "impact": "LOW" | "MEDIUM" | "HIGH",\n'
        '  "horizon": "SHORT_TERM" | "MEDIUM_TERM" | "LONG_TERM",\n'
        '  "reasoning": "<concise justification>",\n'
        '  "trade_bias": "BUY" | "SELL" | "HOLD"\n'
        "}"
    )

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    if wire_api == "responses":
        payload = {
            "model": model,
            "input": prompt,
            "temperature": 0.1,
        }
    else:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a quantitative financial sentinel. Output ONLY raw JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

    print(f"\nDispatching real request to {endpoint} ...")
    t0 = time.time()
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(endpoint, headers=headers, json=payload)
            latency_ms = (time.time() - t0) * 1000

            print(f"HTTP Status               : {resp.status_code}")
            print(f"Latency                   : {latency_ms:.1f}ms")

            if resp.status_code != 200:
                raw_err = redact_key(resp.text[:300], key)
                print(f"Model Response Received   : NO (HTTP {resp.status_code})")
                print(f"Redacted Error            : {raw_err}")
                print("FAIL-CLOSED               : Strict fail-closed, no synthetic fallback.")
                return False, None

            # Response received
            print("Model Response Received   : YES")

            # Parse response
            raw_content = ""
            try:
                data = resp.json()
                if "output" in data and isinstance(data["output"], list):
                    for item in data["output"]:
                        if isinstance(item, dict) and item.get("type") == "message":
                            for piece in item.get("content", []):
                                if isinstance(piece, dict) and piece.get("type") == "output_text":
                                    raw_content += piece.get("text", "")
                                elif isinstance(piece, str):
                                    raw_content += piece
                                elif isinstance(piece, dict) and "text" in piece:
                                    raw_content += str(piece["text"])

                if not raw_content and "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if isinstance(choice, dict):
                        raw_content = choice.get("message", {}).get("content", "")

                content_clean = raw_content.strip()
                if content_clean.startswith("```"):
                    lines = content_clean.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    content_clean = "\n".join(lines).strip()

                parsed = json.loads(content_clean)
                print("Response Parsing          : SUCCESS")
            except Exception as parse_err:
                print(f"Response Parsing          : FAILED ({redact_key(str(parse_err), key)})")
                print(f"Raw Output Snippet        : {redact_key(raw_content[:200], key)}")
                return False, None

            # Validate structured sentiment output fields
            required = ["sentiment", "model_confidence", "impact", "horizon", "reasoning", "trade_bias"]
            missing = [f for f in required if f not in parsed]
            if missing:
                print(f"Structured Schema Check   : FAILED (Missing fields: {missing})")
                return False, None

            print("Structured Sentiment Output:")
            print(f"  - Asset                 : {parsed.get('asset')}")
            print(f"  - Sentiment             : {parsed.get('sentiment')}")
            print(f"  - Confidence Score      : {parsed.get('model_confidence')}")
            print(f"  - Market Impact         : {parsed.get('impact')}")
            print(f"  - Time Horizon          : {parsed.get('horizon')}")
            print(f"  - Trade Bias            : {parsed.get('trade_bias')}")
            print(f"  - Reasoning             : {parsed.get('reasoning')}")

            print("\n" + "=" * 65)
            print(f"Bitget Qwen Status        : AVAILABLE & VERIFIED ({model} via {wire_api})")
            print("=" * 65)
            return True, parsed

    except httpx.TimeoutException:
        latency_ms = (time.time() - t0) * 1000
        print(f"Latency                   : {latency_ms:.1f}ms (TIMED OUT)")
        print("Model Response Received   : NO (Timeout)")
        print("Redacted Error            : Request timed out after 30.0s")
        return False, None
    except Exception as e:
        latency_ms = (time.time() - t0) * 1000
        print(f"Latency                   : {latency_ms:.1f}ms")
        print("Model Response Received   : NO (Exception)")
        print(f"Redacted Error            : {redact_key(type(e).__name__ + ': ' + str(e), key)}")
        return False, None


if __name__ == "__main__":
    success, _ = run_test()
    sys.exit(0 if success else 1)
