"""Base Execution Engine Interface."""

from abc import ABC, abstractmethod
from aegis_rtoken.models import CandidateSignal, ExecutionResult, MarketSnapshot


class BaseExecutionEngine(ABC):
    """Abstract execution interface for trade routing."""

    @abstractmethod
    def execute(self, candidate: CandidateSignal, market: MarketSnapshot) -> ExecutionResult:
        """Routes the candidate signal to the official Bitget execution boundary."""
        raise NotImplementedError
