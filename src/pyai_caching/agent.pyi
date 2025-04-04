from typing import Any, Optional, Dict, TypeVar
from pydantic_ai import Agent
from .types import MessageConverter, ExpenseRecorder, default_message_converter, noop_expense_recorder
from .costs import ModelCosts

T = TypeVar('T')
R = TypeVar('R')

DEFAULT_TTL: int

def _get_model_name(agent: Agent[Any, Any]) -> str: ...

def create_cache_key(agent: Agent[Any, Any], prompt: str, **kwargs: Any) -> str: ...

async def cached_agent_run(
    agent: Agent[T, R],
    prompt: str,
    task_name: str,
    *,
    ttl: int = ...,
    transcript_history: Optional[list[Any]] = ...,
    max_wait: float = ...,
    initial_wait: float = ...,
    message_converter: MessageConverter = ...,
    expense_recorder: ExpenseRecorder = ...,
    redis_url: Optional[str] = ...,
    custom_costs: Optional[Dict[str, ModelCosts]] = ...,
    full_result: bool = ...,
    **kwargs: Any
) -> Any: ...

def cached_agent_run_sync(
    agent: Agent[T, R],
    prompt: str,
    task_name: str,
    *args: Any,
    **kwargs: Any
) -> Any: ... 