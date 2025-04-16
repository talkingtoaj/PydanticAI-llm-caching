"""Type definitions for the pyai-caching package."""

from typing import Protocol
import logging

log = logging.getLogger(__name__)

class ExpenseRecorder(Protocol):
    """Protocol for expense recording functions."""
    async def __call__(self, model: str, task_name: str, cost: float) -> None: ...

async def noop_expense_recorder(model: str, task_name: str, cost: float) -> None:
    """Default do-nothing expense recorder."""
    pass 