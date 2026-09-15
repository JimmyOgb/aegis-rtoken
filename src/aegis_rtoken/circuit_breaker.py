"""Circuit Breaker: Emergency blocking, fault tolerance, and cooldown management."""

from datetime import datetime, timedelta, timezone
from typing import Optional


class CircuitBreaker:
    """Manages emergency shutdown and cooldown states."""

    def __init__(self, cooldown_seconds: int = 300, trip_threshold: int = 3):
        self.cooldown_seconds = cooldown_seconds
        self.trip_threshold = trip_threshold
        self._consecutive_faults: int = 0
        self._is_tripped: bool = False
        self._trip_time: Optional[datetime] = None
        self._trip_reason: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Returns True if the circuit breaker is currently active (tripped & within cooldown)."""
        if not self._is_tripped:
            return False
        if self._trip_time is None:
            return False

        elapsed = (datetime.now(timezone.utc) - self._trip_time).total_seconds()
        if elapsed > self.cooldown_seconds:
            # Auto-reset after cooldown elapsed
            self.reset()
            return False
        return True

    def record_fault(self, reason: str) -> bool:
        """Increments fault counter and trips if threshold is exceeded."""
        self._consecutive_faults += 1
        if self._consecutive_faults >= self.trip_threshold:
            self.trip(f"Consecutive fault threshold ({self.trip_threshold}) reached. Last reason: {reason}")
            return True
        return False

    def record_success(self) -> None:
        """Clears consecutive fault counter on healthy operation."""
        self._consecutive_faults = 0

    def trip(self, reason: str) -> None:
        """Manually or automatically trips the circuit breaker."""
        self._is_tripped = True
        self._trip_time = datetime.now(timezone.utc)
        self._trip_reason = reason

    def reset(self) -> None:
        """Resets the circuit breaker state to normal operations."""
        self._is_tripped = False
        self._trip_time = None
        self._trip_reason = None
        self._consecutive_faults = 0

    def status(self) -> dict:
        remaining = 0.0
        if self._is_tripped and self._trip_time:
            elapsed = (datetime.now(timezone.utc) - self._trip_time).total_seconds()
            remaining = max(0.0, self.cooldown_seconds - elapsed)

        return {
            "is_tripped": self.is_active,
            "consecutive_faults": self._consecutive_faults,
            "trip_reason": self._trip_reason,
            "remaining_cooldown_seconds": round(remaining, 1),
        }
