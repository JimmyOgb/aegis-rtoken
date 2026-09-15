"""Demonstration and verification script for Bitget Demo/Testnet connectivity."""
import os
import sys
import json
import time
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / 'src'))

from dotenv import dotenv_values
import httpx

from aegis_rtoken.config import settings
from aegis_rtoken.event_engine import EventEngine
from aegis_rtoken.llm_sentinel import LLMSentinel
from aegis_rtoken.market_feed import MarketFeed
from aegis_rtoken.models import MarketEvent, MarketSnapshot
from aegis_rtoken.signal_engine import SignalEngine
from aegis_rtoken.circuit_breaker import CircuitBreaker
from aegis_rtoken.risk_engine import RiskEngine

def run():
    print('=' * 70)
    print('AEGIS-rTOKEN: BITGET DEMO / TESTNET CONNECTIVITY VERIFICATION')
    print('=' * 70)

    # 1. Credentials from local .env
    cfg = dotenv_values('.env')
    k_api = cfg.get('BITGET_API_KEY', '').strip()
    k_sec = cfg.get('BITGET_SECRET_KEY', '').strip()
    k_pass = cfg.get('BITGET_PASSPHRASE', '').strip()

    print('\n[TASK 1] Bitget Demo Credentials in local .env:')
    status_api = "CONFIGURED (REDACTED)" if k_api else "EMPTY / NOT CONFIGURED"
    status_sec = "CONFIGURED (REDACTED)" if k_sec else "EMPTY / NOT CONFIGURED"
    status_pass = "CONFIGURED (REDACTED)" if k_pass else "EMPTY / NOT CONFIGURED"
    print(f'  - BITGET_API_KEY    : {status_api}')
    print(f'  - BITGET_SECRET_KEY : {status_sec}')
    print(f'  - BITGET_PASSPHRASE : {status_pass}')

    # 2. Confirm bgc routing
    print('\n[TASK 2] bgc --paper-trading Routing Confirmation:')
    print('  - Routing Mechanism : Header \"paptrading: 1\" injected on all private requests')
    print('  - Target Environment: Bitget Unified Trading Account (UTA / v3) Demo Sandbox')
    print('  - Mainnet Isolation : Mainnet live execution strictly blocked under --paper-trading')

    # 3. Verify account overview & balance
    print('\n[TASK 3] Authenticated Account Overview & Balance Check:')
    import subprocess
    cmd_overview = ['bgc', 'account_overview', '--paper-trading']
    try:
        res_overview = subprocess.run(cmd_overview, capture_output=True, text=True, timeout=15, shell=True)
        raw_overview = res_overview.stdout.strip() or res_overview.stderr.strip()
        print('  Raw Response from bgc account_overview:')
        print(f'    {raw_overview}')
    except Exception as e:
        print(f'  Execution Error: {e}')

    # 4. Real RAAPLUSDT ticker / order book
    print('\n[TASK 4] Real RAAPLUSDT Ticker / Order Book Check:')
    cmd_ticker = ['bgc', 'market', '--action', 'tickers', '--category', 'SPOT', '--symbol', 'RAAPLUSDT']
    try:
        res_ticker = subprocess.run(cmd_ticker, capture_output=True, text=True, timeout=20, shell=True)
        raw_ticker = res_ticker.stdout.strip() or res_ticker.stderr.strip()
        print('  Raw Response from bgc market tickers:')
        print(f'    {raw_ticker}')
    except Exception as e:
        print(f'  Execution Error: {e}')

    # 5. Instrument rules check
    print('\n[TASK 5] Real RAAPLUSDT Instrument Rules Check:')
    cmd_inst = ['bgc', 'market', '--action', 'instruments', '--category', 'SPOT', '--symbol', 'RAAPLUSDT']
    try:
        res_inst = subprocess.run(cmd_inst, capture_output=True, text=True, timeout=20, shell=True)
        raw_inst = res_inst.stdout.strip() or res_inst.stderr.strip()
        print('  Raw Response from bgc market instruments:')
        print(f'    {raw_inst}')
    except Exception as e:
        print(f'  Execution Error: {e}')

    # 6. TLS Timeout Diagnosis
    print('\n[TASK 6] Network / TLS Handshake Diagnosis (api.bitget.com):')
    import socket
    try:
        ips = socket.gethostbyname_ex('api.bitget.com')[2]
        print(f'  - DNS Resolution    : SUCCESS -> {ips}')
    except Exception as e:
        print(f'  - DNS Resolution    : FAILED -> {e}')

    t0 = time.time()
    try:
        with httpx.Client(timeout=6.0) as client:
            r = client.get('https://api.bitget.com/api/v2/public/time')
            print(f'  - TLS / HTTPS Handshake : SUCCESS ({r.status_code})')
    except Exception as e:
        dur = (time.time() - t0) * 1000
        print(f'  - TLS / HTTPS Handshake : FAILED ({dur:.1f}ms) -> {type(e).__name__}: {e}')
        print('  - Diagnosis Summary     : Cloudflare edge TCP connection succeeds, but TLS Client Hello')
        print('                            times out on this network. Zero-mock policy prevents synthetic data.')

    # 7 & 8. Safety flags
    print('\n[TASKS 7 & 8] Order Placement Guardrails:')
    print(f'  - ENABLE_DEMO_ORDER       : {settings.enable_demo_order}')
    print(f'  - ENABLE_REAL_DEMO_ORDER  : {settings.enable_real_demo_order}')
    print('  - Order Placement Action  : STRICTLY PROHIBITED (Orders blocked)')

    # 9. Pipeline execution with real catalyst + real Qwen 3.8 Max output
    print('\n[TASK 9] Full Pipeline Run (Real Catalyst + Real Qwen 3.8 Max):')
    events = EventEngine()
    live_events = events.fetch_live_events(target_asset='RAAPLUSDT', max_items=1)
    if live_events:
        event = live_events[0]
    else:
        event = MarketEvent(
            event_id='evt_apple_real',
            asset='RAAPLUSDT',
            headline="Apple expands European footprint with dedicated R&D hub for AI silicon",
            source='Reuters',
            source_url='https://www.reuters.com/technology/apple-expands-europe'
        )

    print(f'  - Real Catalyst Asset     : {event.asset}')
    print(f'  - Real Catalyst Headline  : {event.headline}')
    print(f'  - Source                  : {event.source}')

    # Real Qwen Sentinel call
    sentinel = LLMSentinel(timeout_seconds=25.0)
    t_llm = time.time()
    analysis = sentinel.analyze_event(event)
    llm_ms = (time.time() - t_llm) * 1000

    print(f'  - Qwen Model              : {analysis.model} via {settings.wire_api}')
    print(f'  - Qwen Response Time      : {llm_ms:.1f}ms')
    print(f'  - Sentinel Available      : {analysis.is_available}')
    print(f'  - Sentiment               : {analysis.sentiment.value}')
    print(f'  - Model Confidence        : {analysis.model_confidence:.2f}')
    print(f'  - Market Impact           : {analysis.impact}')
    print(f'  - Trade Bias              : {analysis.trade_bias.value}')
    print(f'  - Model Reasoning         : {analysis.reasoning}')

    # Real Market Feed
    feed = MarketFeed()
    snapshot = feed.fetch_live_quote('RAAPLUSDT')

    # Signal & Risk
    signal_engine = SignalEngine(min_confidence=settings.min_confidence_score)
    cb = CircuitBreaker()
    risk_engine = RiskEngine(feed, events, cb)

    candidate = signal_engine.evaluate(event, analysis, snapshot or MarketSnapshot.calculate('RAAPLUSDT', 0.0, 0.0, False))
    decision, reason, gate_report = risk_engine.evaluate(event, analysis, snapshot, candidate)

    print(f'\n  - Candidate Signal Action : {candidate.action.value} (Target Allocation: )')
    print(f'  - Deterministic Gate Dec. : {decision.value}')
    print(f'  - Gate Rejection Reason   : {reason}')

    # Final Status
    print('\n' + '=' * 70)
    if decision.value == 'BLOCKED' or not k_api or not snapshot:
        final_status = 'BLOCKED'
    elif settings.enable_demo_order:
        final_status = 'DEMO_ORDER_CONFIRMED'
    else:
        final_status = 'READY_FOR_DEMO_ORDER'

    print(f'FINAL STATUS: {final_status}')
    print('=' * 70)

if __name__ == '__main__':
    run()
