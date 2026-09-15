"""Bitget Official Execution Engine: Integration with Bitget Agent CLI (bgc).

Strictly communicates with the real Bitget environment (demo/paper or live via bgc).
ZERO-MOCK POLICY: If Bitget is unreachable or rejects the order, the system FAILS CLOSED.
Never manufactures synthetic fills.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aegis_rtoken.config import settings
from aegis_rtoken.execution.base import BaseExecutionEngine
from aegis_rtoken.models import CandidateSignal, ExecutionResult, MarketSnapshot, SignalAction

logger = logging.getLogger(__name__)


class BitgetCliExecutionEngine(BaseExecutionEngine):
    """Integrates with the official `bgc` CLI for Bitget Demo/Testnet execution.
    
    ZERO-MOCK POLICY:
    - Never generates synthetic order IDs or fake fill prices.
    - Captures real exchange responses only.
    - Fails closed on any exchange rejection, missing credentials, or network errors.
    """

    def __init__(self, mode: str = "demo"):
        # Supported modes: 'demo' (Bitget Demo/Testnet environment) | 'dry_run'
        # Live execution on mainnet is strictly blocked in this configuration.
        if mode in ("live", "mainnet", "prod", "production"):
            raise ValueError(
                "LIVE TRADING STRICTLY PROHIBITED: Aegis-rToken is exclusively restricted to "
                "Bitget Demo/Paper Trading. Live mainnet orders cannot be submitted."
            )
        self.mode = "demo" if mode in ("demo", "paper") else ("dry_run" if mode == "dry_run" else "demo")

    def build_command(self, candidate: CandidateSignal, market: MarketSnapshot) -> List[str]:
        """Constructs the bgc CLI invocation arguments for Bitget Demo/Testnet."""
        side = "buy" if candidate.action == SignalAction.BUY else "sell"
        category = getattr(settings, "execution_category", "SPOT")
        
        # Spot market order qty:
        # - Market BUY: unit is quote coin (USDT)
        # - Market SELL: unit is base coin (rToken)
        if candidate.action == SignalAction.BUY:
            qty_str = str(round(candidate.target_allocation_usd, 2))
        else:
            base_amount = candidate.target_allocation_usd / market.bid if market.bid > 0 else 0.001
            qty_str = f"{base_amount:.4f}"

        cmd = [
            "bgc",
            "--paper-trading",
            "order",
            "--action",
            "place",
            "--category",
            category,
            "--symbol",
            candidate.asset,
            "--side",
            side,
            "--orderType",
            "market",
            "--qty",
            qty_str,
        ]

        # Invariant: --paper-trading must NEVER be omitted
        if "--paper-trading" not in cmd:
            raise RuntimeError("CRITICAL SAFETY HALT: Execution command is missing mandatory --paper-trading flag.")

        if self.mode == "dry_run":
            cmd.append("--dry-run")

        return cmd

    def execute(self, candidate: CandidateSignal, market: MarketSnapshot) -> ExecutionResult:
        if self.mode not in ("demo", "dry_run"):
            raise RuntimeError("CRITICAL SAFETY HALT: Only Bitget Demo/Paper trading mode is permitted.")
        now = datetime.now(timezone.utc)
        side_str = "buy" if candidate.action == SignalAction.BUY else "sell"

        if candidate.action == SignalAction.HOLD:
            return ExecutionResult(
                success=True,
                order_id="NONE",
                symbol=candidate.asset,
                side="hold",
                quantity=0.0,
                order_status="HOLD_NOOP",
                mode=f"bitget_{self.mode}",
                action=candidate.action,
                asset=candidate.asset,
                fill_price=0.0,
                allocated_usd=0.0,
                api_error=None,
                details={"status": "HOLD_NOOP"},
                timestamp=now,
            )

        bgc_bin = shutil.which("bgc")
        if not bgc_bin:
            logger.error("bgc binary not found in PATH. FAILING CLOSED.")
            return ExecutionResult(
                success=False,
                order_id="FAILED",
                symbol=candidate.asset,
                side=side_str,
                quantity=candidate.target_allocation_usd,
                order_status="EXECUTION_UNAVAILABLE",
                mode=f"bitget_{self.mode}",
                action=candidate.action,
                asset=candidate.asset,
                fill_price=0.0,
                allocated_usd=0.0,
                api_error="Bitget CLI (bgc) not found in system PATH. Execution blocked.",
                details={"error": "BGC_NOT_FOUND"},
                timestamp=now,
            )

        cmd = self.build_command(candidate, market)
        logger.info(f"Executing official Bitget Demo command: {' '.join(cmd)}")

        proc_env = dict(os.environ)
        if settings.bitget_api_key:
            proc_env["BITGET_API_KEY"] = settings.bitget_api_key
        if settings.bitget_secret_key:
            proc_env["BITGET_SECRET_KEY"] = settings.bitget_secret_key
        if settings.bitget_passphrase:
            proc_env["BITGET_PASSPHRASE"] = settings.bitget_passphrase
        if settings.bitget_api_base_url:
            proc_env["BITGET_API_BASE_URL"] = settings.bitget_api_base_url

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
                shell=sys.platform == "win32",
                env=proc_env,
            )

            output_json: Dict[str, Any] = {}
            if res.stdout:
                try:
                    output_json = json.loads(res.stdout)
                except Exception:
                    output_json = {"raw_stdout": res.stdout}

            # Case A: CLI reported an error (non-zero exit or ok=false)
            if res.returncode != 0 or output_json.get("ok") is False:
                err_dict = output_json.get("error")
                if isinstance(err_dict, dict) and err_dict:
                    err_msg = err_dict.get("message") or err_dict.get("type") or str(err_dict)
                    err_cat = err_dict.get("category", "")
                elif err_dict is not None and str(err_dict).strip():
                    err_msg = str(err_dict)
                    err_cat = ""
                else:
                    err_msg = (res.stderr or res.stdout or "Execution failed").strip()
                    err_cat = ""

                # Distinguish environment mismatch vs missing credentials vs order rejected
                err_lower = str(err_msg).lower()
                if "exchange environment is incorrect" in err_lower:
                    status = "DEMO_AUTH_REQUIRED"
                elif "credentials" in err_lower or err_cat == "config":
                    status = "EXECUTION_UNAVAILABLE"
                else:
                    status = "ORDER_REJECTED"

                logger.error(f"Bitget Demo execution failed ({status}): {err_msg}")
                err_details = dict(output_json)
                if "error" not in err_details:
                    err_details["error"] = str(err_msg)

                return ExecutionResult(
                    success=False,
                    order_id="FAILED",
                    symbol=candidate.asset,
                    side=side_str,
                    quantity=candidate.target_allocation_usd,
                    order_status=status,
                    mode=f"bitget_{self.mode}",
                    action=candidate.action,
                    asset=candidate.asset,
                    fill_price=0.0,
                    allocated_usd=0.0,
                    api_error=str(err_msg).strip(),
                    details=err_details,
                    timestamp=now,
                )

            # Case B: Success return code
            data = output_json.get("data") or {}

            # If dry-run mode was requested
            if data.get("dryRun") is True or self.mode == "dry_run":
                logger.info(f"Bitget Demo dry-run successfully validated: {data}")
                return ExecutionResult(
                    success=True,
                    order_id=None,
                    symbol=candidate.asset,
                    side=side_str,
                    quantity=candidate.target_allocation_usd,
                    order_status="DRY_RUN_VALIDATED",
                    mode=f"bitget_{self.mode}",
                    action=candidate.action,
                    asset=candidate.asset,
                    fill_price=0.0,
                    allocated_usd=candidate.target_allocation_usd,
                    api_error=None,
                    details=output_json,
                    timestamp=now,
                )

            # Case C: Real Bitget Demo response
            order_id = data.get("orderId")
            if not order_id:
                logger.warning(f"No orderId returned by Bitget: {output_json}")
                return ExecutionResult(
                    success=False,
                    order_id=None,
                    symbol=candidate.asset,
                    side=side_str,
                    quantity=candidate.target_allocation_usd,
                    order_status="ORDER_UNCONFIRMED",
                    mode=f"bitget_{self.mode}",
                    action=candidate.action,
                    asset=candidate.asset,
                    fill_price=0.0,
                    allocated_usd=0.0,
                    api_error="Exchange response did not contain confirmed orderId",
                    details=output_json,
                    timestamp=now,
                )

            fill_price_raw = data.get("fillPrice")
            fill_price = float(fill_price_raw) if fill_price_raw is not None else 0.0

            return ExecutionResult(
                success=True,
                order_id=str(order_id),
                symbol=candidate.asset,
                side=side_str,
                quantity=float(data.get("baseVolume") or data.get("qty") or candidate.target_allocation_usd),
                order_status="CONFIRMED",
                mode=f"bitget_{self.mode}",
                action=candidate.action,
                asset=candidate.asset,
                fill_price=fill_price,
                allocated_usd=candidate.target_allocation_usd,
                api_error=None,
                details=output_json,
                timestamp=now,
            )

        except Exception as ex:
            logger.exception("Subprocess execution of Bitget CLI failed with exception")
            return ExecutionResult(
                success=False,
                order_id=None,
                symbol=candidate.asset,
                side=side_str,
                quantity=candidate.target_allocation_usd,
                order_status="EXECUTION_UNAVAILABLE",
                mode=f"bitget_{self.mode}",
                action=candidate.action,
                asset=candidate.asset,
                fill_price=0.0,
                allocated_usd=0.0,
                api_error=str(ex),
                details={"exception": str(ex)},
                timestamp=now,
            )
