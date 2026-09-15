"""Run Script: Starts the Aegis-rToken persistent autonomous agent and API server."""

import sys
from pathlib import Path
import uvicorn

# Add src to python path
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))

from aegis_rtoken.api.server import create_app
from aegis_rtoken.config import settings
from aegis_rtoken.main import AegisAgent


def main():
    print(f"Starting Aegis-rToken Autonomous Sentinel on {settings.api_host}:{settings.api_port}...")
    agent = AegisAgent()
    app = create_app(
        market_feed=agent.feed,
        event_engine=agent.events,
        circuit_breaker=agent.circuit_breaker,
        telemetry=agent.telemetry,
    )
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level=settings.log_level.lower())


if __name__ == "__main__":
    main()
