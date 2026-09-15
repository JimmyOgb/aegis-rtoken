"""Execution layer modules for Aegis-rToken.

Executes exclusively through the official Bitget environment (demo/paper or live).
Internal fake/simulated fill engines are strictly prohibited.
"""

from aegis_rtoken.execution.base import BaseExecutionEngine
from aegis_rtoken.execution.bitget_cli import BitgetCliExecutionEngine

__all__ = [
    "BaseExecutionEngine",
    "BitgetCliExecutionEngine",
]
