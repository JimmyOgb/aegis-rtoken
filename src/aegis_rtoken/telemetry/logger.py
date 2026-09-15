"""Telemetry Logger: Append-only persistent audit trail of all sentinel decisions."""

import json
import logging
from pathlib import Path
from typing import List, Optional
from aegis_rtoken.config import settings
from aegis_rtoken.models import DecisionRecord

logger = logging.getLogger(__name__)


class TelemetryLogger:
    """Records every decision (TRADE, HOLD, BLOCKED) to persistent storage and in-memory cache."""

    def __init__(self, log_dir: Optional[Path] = None, log_filename: str = "decisions.jsonl"):
        self.log_dir = log_dir or settings.logs_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / log_filename
        self._recent_records: List[DecisionRecord] = []
        self._max_in_memory: int = 100

    def record(self, decision_record: DecisionRecord) -> None:
        """Appends decision record to JSONL and in-memory buffer."""
        # Add to in-memory ring buffer
        self._recent_records.insert(0, decision_record)
        if len(self._recent_records) > self._max_in_memory:
            self._recent_records.pop()

        # Append to persistent JSONL file
        try:
            line = decision_record.model_dump_json()
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            logger.error(f"Failed to persist telemetry record to {self.log_file}: {e}")

    def get_recent(self, limit: int = 20) -> List[DecisionRecord]:
        """Returns the most recent decisions."""
        return self._recent_records[:limit]

    def count(self) -> int:
        return len(self._recent_records)
