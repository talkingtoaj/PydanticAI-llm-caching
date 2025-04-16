from typing import Any, Optional, Dict, TypeVar, Generic
from pydantic_ai import Agent
from pydantic_ai.result import FinalResult
from .types import ExpenseRecorder
from .costs import ModelCosts

DEFAULT_TTL: int

T = TypeVar('T')  # Type variable for agent result type

def _get_model_name(agent: Agent[Any, Any]) -> str: ...

def create_cache_key(agent: Agent[Any, Any], prompt: str, **kwargs: Any) -> str: ...

async def cached_agent_run(
    agent: Agent[Any, T],
    prompt: str,
    task_name: str,
    *,
    ttl: int = ...,
    max_wait: float = ...,
    initial_wait: float = ...,
    expense_recorder: ExpenseRecorder = ...,
    redis_url: Optional[str] = None,
    custom_costs: Optional[Dict[str, ModelCosts]] = None,
    **kwargs: Any
) -> FinalResult[T]: ...

def cached_agent_run_sync(
    agent: Agent[Any, T],
    prompt: str,
    task_name: str,
    *args: Any,
    **kwargs: Any
) -> FinalResult[T]: ... 