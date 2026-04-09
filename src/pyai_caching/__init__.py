"""
LLM Caching - Redis-based caching for LLM agents with cost tracking
"""

from importlib.metadata import PackageNotFoundError, version

from .agent import cached_agent_run, cached_agent_run_sync
from .config import (
    clear_cache,
    clear_cache_async,
    get_async_redis_client,
    get_redis_client,
)
from .costs import DEFAULT_COSTS, ModelCosts
from .exceptions import (
    CacheError,
    ConfigurationError,
    ConnectionError,
    RateLimitError,
)
from .types import ExpenseRecorder

_DIST_NAME = "pyai-caching"

try:
    __version__ = version(_DIST_NAME)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = [
    "__version__",
    "cached_agent_run",
    "cached_agent_run_sync",
    "get_redis_client",
    "get_async_redis_client",
    "clear_cache",
    "clear_cache_async",
    "ExpenseRecorder",
    "ModelCosts",
    "DEFAULT_COSTS",
    "ConfigurationError",
    "RateLimitError",
    "CacheError",
    "ConnectionError",
]
