"""Main caching functionality for LLM agents."""

import asyncio
import pickle
from typing import Any, Optional, Dict
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
import logging
from .types import MessageConverter, ExpenseRecorder, default_message_converter, noop_expense_recorder
from .config import get_redis_client
from .costs import ModelCosts, calculate_cost

log = logging.getLogger(__name__)

# Default TTL
DEFAULT_TTL = 3600 * 24 * 15  # 15 days

def _get_model_name(agent: Agent[Any, Any]) -> str:
    """Helper to get the model name from an agent."""
    if hasattr(agent, 'model') and agent.model:
        model_obj = agent.model
        if isinstance(model_obj, str):
            return model_obj
        elif hasattr(model_obj, 'model_name') and model_obj.model_name:
            return model_obj.model_name
        else:
            return model_obj.__class__.__name__
    return "unknown"

def create_cache_key(agent: Agent[Any, Any], prompt: str, **kwargs: Any) -> str:
    """Create a cache key from the agent, prompt, and output model schema."""
    # Include relevant kwargs in the cache key if they affect the response
    key_parts = [
        str(agent),
        prompt
    ]
    
    # Include message history in cache key if present
    if "transcript_history" in kwargs and kwargs["transcript_history"]:
        # Convert message history to a string representation
        history_str = "|".join(
            msg.get("content", "") if isinstance(msg, dict) else str(msg)
            for msg in kwargs["transcript_history"]
        )
        key_parts.append(history_str)
    
    # Include output model schema in cache key
    if hasattr(agent, 'result_type') and agent.result_type:
        try:
            schema = agent.result_type.model_json_schema()
            # Convert schema to a stable string representation
            schema_str = str(sorted(schema.items()))
            key_parts.append(schema_str)
        except Exception as e:
            log.warning(f"Failed to get output model schema: {e}")
    
    return "|".join(key_parts)

async def cached_agent_run(
    agent: Agent[Any, Any],
    prompt: str,
    task_name: str,
    *,
    ttl: int = DEFAULT_TTL,
    transcript_history: Optional[list[Any]] = None,
    max_wait: float = 10.0,
    initial_wait: float = 1.0,
    message_converter: MessageConverter = default_message_converter,
    expense_recorder: ExpenseRecorder = noop_expense_recorder,
    redis_url: Optional[str] = None,
    custom_costs: Optional[Dict[str, ModelCosts]] = None,
    full_result: bool = False,
    **kwargs: Any
) -> Any:
    """
    Run an agent with Redis caching and rate limit handling.
    
    Args:
        agent: The PydanticAI agent to run
        prompt: The prompt to send
        task_name: Name of the task for expense tracking
        ttl: Cache TTL in seconds
        transcript_history: Optional message history
        max_wait: Maximum wait time before giving up (default 10s)
        initial_wait: Initial wait time for exponential backoff (default 1s)
        message_converter: Function to convert messages to ModelMessage format
        expense_recorder: Function to record expenses
        redis_url: Optional Redis URL (defaults to LLM_CACHE_REDIS_URL env var)
        custom_costs: Optional dictionary of custom costs per model
        full_result: Whether to return the full result object (default False)
        **kwargs: Additional arguments for agent.run
        
    Returns:
        result.data if full_result is False, otherwise result
        
    Raises:
        UsageLimitExceeded: If rate limits are hit and max_wait is exceeded
        ConfigurationError: If Redis URL is not configured
        ValueError: If model costs are not found
    """
    # --- Input Validation ---
    if not prompt:
        raise ValueError("Prompt cannot be empty.")
    # ----------------------

    # Get Redis client
    redis_client = get_redis_client(redis_url)
    
    # Determine model name using the helper function
    model_name = _get_model_name(agent)
    
    # Try to get from cache
    cache_key = create_cache_key(agent, prompt, **kwargs)
    cached_result = None # Initialize to None
    try:
        cached_result = redis_client.get(cache_key)
    except Exception as e:
        log.warning(f"Error getting cache key '{cache_key}' from Redis: {e}")
        # Treat as cache miss, proceed to agent run
        
    if cached_result:
        log.info(f"Cache hit for key: {cache_key}")
        try:
            result = pickle.loads(bytes(cached_result))
            # Use model_name for expense recorder on cache hit
            await expense_recorder(model_name, task_name, 0)  # Cache hits are free
            return result.data if full_result is False else result
        except Exception as e:
            log.warning(f"Error unpickling cached result: {e}")

    # Not in cache, run the agent with exponential backoff
    log.debug(f"Cache miss for key: {cache_key}")
    wait_time = initial_wait
    last_error = None

    # Convert message history if provided
    message_history = message_converter(transcript_history) if transcript_history else None

    while wait_time <= max_wait:
        try:
            result = await agent.run(prompt, message_history=message_history)
            # Calculate cost from usage data
            cost = calculate_cost(model_name, result, custom_costs)
            await expense_recorder(model_name, task_name, cost)
            redis_client.set(cache_key, pickle.dumps(result), ex=ttl)
            return result.data if full_result is False else result

        except UsageLimitExceeded as e:
            last_error = e
            log.info(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
            await asyncio.sleep(wait_time)
            wait_time *= 2  # Exponential backoff

        except Exception as e:
            log.error(f"Unexpected error running agent: {e}")
            raise

    # If we get here, we've exceeded max_wait
    log.error(f"Rate limit retries exhausted after {max_wait} seconds")
    if last_error:
        raise last_error
    raise RuntimeError(f"Rate limit retries exhausted after {max_wait} seconds")

def cached_agent_run_sync(
    agent: Agent[Any, Any],
    prompt: str,
    task_name: str,
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Synchronous version of cached_agent_run.

    Runs an agent with Redis caching and rate limit handling using asyncio.run().
    Accepts the same arguments as cached_agent_run.

    Args:
        agent: The PydanticAI agent to run
        prompt: The prompt to send
        task_name: Name of the task for expense tracking
        *args: Positional arguments passed to cached_agent_run
        **kwargs: Keyword arguments passed to cached_agent_run

    Returns:
        result data

    Raises:
        Exceptions from cached_agent_run
    """
    return asyncio.run(cached_agent_run(agent, prompt, task_name, *args, **kwargs)) 