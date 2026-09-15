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
        self._last_mtime: float = 0.0
        self._sync_from_disk()

    def _sync_from_disk(self) -> None:
        """Loads or synchronizes recent decision records from persistent JSONL storage."""
        if not self.log_file.exists():
            return
        try:
            mtime = self.log_file.stat().st_mtime
            if mtime == self._last_mtime and self._recent_records:
                return
            self._last_mtime = mtime

            records: List[DecisionRecord] = []
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        records.append(DecisionRecord.model_validate(data))
                    except Exception:
                        continue

            # Keep newest entries first (log file is append-only, so last lines are newest)
            if records:
                self._recent_records = list(reversed(records[-self._max_in_memory:]))
        except Exception as e:
            logger.error(f"Failed to load telemetry from {self.log_file}: {e}")

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
            if self.log_file.exists():
                self._last_mtime = self.log_file.stat().st_mtime
        except Exception as e:
            logger.error(f"Failed to persist telemetry record to {self.log_file}: {e}")

    def get_recent(self, limit: int = 20) -> List[DecisionRecord]:
        """Returns the most recent decisions."""
        self._sync_from_disk()
        return self._recent_records[:limit]

    def count(self) -> int:
        self._sync_from_disk()
        return len(self._recent_records)
