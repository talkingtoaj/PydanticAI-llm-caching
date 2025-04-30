"""Main caching functionality for LLM agents."""

import asyncio
import pickle
import random
from typing import Any, Optional, Dict
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
import logging
from .types import ExpenseRecorder, noop_expense_recorder
from .config import get_redis_client
from .costs import ModelCosts, calculate_cost
from .exceptions import ConnectionError

log = logging.getLogger(__name__)

# Default TTL for cached responses (15 days)
DEFAULT_TTL = 3600 * 24 * 15

# Default retry configuration
DEFAULT_RETRY_CONFIG = {
    'max_retries': 3,
    'initial_delay': 1.0,
    'max_delay': 10.0,
    'jitter': 0.1
}

class CachedResult:
    """A class to represent cached agent results.
    
    This class provides a consistent interface for cached results, similar to the original
    agent result object but without any non-picklable components.
    """
    def __init__(self, output: Any, usage: Any, model: str, cost: float):
        self.output = output
        self._usage = usage
        self.model = model
        self.cost = cost
        
    def usage(self) -> Any:
        """Get usage data."""
        return self._usage

def _get_model_name(agent: Agent[Any, Any]) -> str:
    """Helper to get the model name from an agent.
    
    This function handles different ways the model name might be stored in the agent:
    1. Direct string in agent.model
    2. Model object with model_name attribute
    3. Model class name as fallback
    """
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
    """Create a cache key from the agent, prompt, and output model schema.
    
    The cache key incorporates the agent configuration, prompt text, message history (if present),
    and output model schema to ensure unique caching per conversation context.
    
    Args:
        agent: The PydanticAI agent to run
        prompt: The prompt to send
        **kwargs: Additional arguments, with special handling for:
                 - message_history: List of messages providing conversation context.
                   Each message's string representation is included in the cache key.
        
    Returns:
        str: A unique cache key incorporating all elements that could affect the response
    """
    # Include relevant kwargs in the cache key if they affect the response
    key_parts = [
        str(agent),
        prompt
    ]
    
    # Include message history in cache key if present
    if "message_history" in kwargs and kwargs["message_history"]:
        # Convert message history to a string representation
        history_str = "|".join(str(msg) for msg in kwargs["message_history"])
        key_parts.append(history_str)
    
    # Include output model schema in cache key
    if hasattr(agent, 'output_type') and agent.output_type:
        try:
            schema = agent.output_type.model_json_schema()
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
    max_wait: float = 10.0,
    initial_wait: float = 1.0,
    expense_recorder: ExpenseRecorder = noop_expense_recorder,
    redis_url: Optional[str] = None,
    custom_costs: Optional[Dict[str, ModelCosts]] = None,
    skip_cache: bool = False, # Can be used to utilize other uses of this wrapper without caching
    retry_config: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Any:
    """Run an agent with Redis caching and rate limit handling.
    
    This function runs a PydanticAI agent with caching support. If a cached result exists
    and hasn't expired, it will be returned. Otherwise, the agent will be run and the
    result cached for future use. The function always returns the complete result object
    from the agent run.
    
    Args:
        agent: The PydanticAI agent to run
        prompt: The prompt to send
        task_name: Name of the task for expense tracking
        ttl: Cache TTL in seconds (default: 15 days)
        max_wait: Maximum wait time before giving up on rate limits (default: 10s)
        initial_wait: Initial wait time for exponential backoff (default: 1s)
        expense_recorder: Function to record expenses (default: noop)
        redis_url: Optional Redis URL (defaults to LLM_CACHE_REDIS_URL env var)
        custom_costs: Optional dictionary of custom costs per model
        retry_config: Optional retry configuration (defaults to DEFAULT_RETRY_CONFIG)
        **kwargs: Additional arguments passed directly to agent.run
        
    Returns:
        The complete agent run result object
        
    Raises:
        UsageLimitExceeded: If rate limits are hit and max_wait is exceeded
        ConnectionError: If connection errors persist after retries
        ConfigurationError: If Redis URL is not configured
        ValueError: If model costs are not found or prompt is empty
    """

    model_name = _get_model_name(agent)

    if not skip_cache:
        redis_client = get_redis_client(redis_url)
        log.debug(f"Using Redis client with TTL: {ttl} seconds")

        # Try to get from cache
        cache_key = create_cache_key(agent, prompt, **kwargs)
        cached_result = None # Initialize to None
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                log.debug(f"Cache hit for key: {cache_key}")
            else:
                log.debug(f"Cache miss for key: {cache_key}")
        except Exception as e:
            log.warning(f"Error getting cache key '{cache_key}' from Redis: {e}")
            # Treat as cache miss, proceed to agent run
            
        if cached_result:
            try:
                result = pickle.loads(bytes(cached_result))
                # Use model_name for expense recorder on cache hit
                await expense_recorder(model_name, task_name, 0)  # Cache hits are free
                return result
            except Exception as e:
                log.warning(f"Error unpickling cached result: {e}")

        # Not in cache, run the agent with exponential backoff
        log.debug(f"Cache miss for key: {cache_key}")
    wait_time = initial_wait
    last_error = None
    
    # Use provided retry config or defaults
    retry_config = retry_config or DEFAULT_RETRY_CONFIG
    max_retries = retry_config['max_retries']
    retry_count = 0

    while retry_count < max_retries:
        try:
            result = await agent.run(prompt, **kwargs)
            # Calculate cost from usage data
            cost = calculate_cost(model_name, result, custom_costs)
            await expense_recorder(model_name, task_name, cost)

            if not skip_cache:
                # Create a cacheable version of the result
                cacheable_result = CachedResult(
                    output=result.output,
                    usage=result.usage(),
                    model=model_name,
                    cost=cost
                )
                redis_client.set(cache_key, pickle.dumps(cacheable_result), ex=ttl)
            return result

        except UsageLimitExceeded as e:
            last_error = e
            log.info(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
            await asyncio.sleep(wait_time)
            wait_time *= 2  # Exponential backoff
            
        except (asyncio.TimeoutError, ConnectionRefusedError, ConnectionResetError) as e:
            retry_count += 1
            if retry_count >= max_retries:
                log.error(f"Connection error after {max_retries} retries: {e}")
                raise ConnectionError(f"Connection error after {max_retries} retries: {e}")
            
            # Calculate delay with jitter
            delay = min(wait_time * (2 ** retry_count), retry_config['max_delay'])
            jitter = random.uniform(-retry_config['jitter'], retry_config['jitter'])
            actual_delay = delay * (1 + jitter)
            
            log.info(f"Connection error. Retry {retry_count}/{max_retries}. Waiting {actual_delay:.2f} seconds...")
            await asyncio.sleep(actual_delay)
            last_error = e

        except Exception as e:
            log.error(f"Unexpected error running agent: {e}")
            raise

    # If we get here, we've exceeded max_retries
    log.error(f"Retries exhausted after {max_retries} attempts")
    if last_error:
        raise last_error
    raise RuntimeError(f"Retries exhausted after {max_retries} attempts")

def cached_agent_run_sync(
    agent: Agent[Any, Any],
    prompt: str,
    task_name: str,
    *args: Any,
    **kwargs: Any
) -> Any:
    """Synchronous version of cached_agent_run.

    This is a convenience wrapper that runs cached_agent_run in a new event loop.
    It accepts the same arguments and provides the same functionality, always returning
    the complete result object from the agent run.
    
    Args:
        agent: The PydanticAI agent to run
        prompt: The prompt to send
        task_name: Name of the task for expense tracking
        *args: Additional positional arguments passed to cached_agent_run
        **kwargs: Additional keyword arguments passed to cached_agent_run, including:
                 - message_history: List of messages providing conversation context
                 - model_settings: Dict of model-specific settings
                 - ttl: Cache TTL in seconds (default: 15 days)
                 - max_wait: Maximum wait time for rate limits (default: 10s)
                 - initial_wait: Initial wait time for backoff (default: 1s)
                 - expense_recorder: Function to record expenses (default: noop)
                 - redis_url: Optional Redis URL
                 - custom_costs: Optional dictionary of custom costs per model
                 Any other kwargs are passed directly to agent.run
    
    Returns:
        The complete agent run result object containing:
        - data: The typed response data
        - usage: Token usage information
        - metadata: Any additional model-specific metadata
        
    Raises:
        UsageLimitExceeded: If rate limits are hit and max_wait is exceeded
        ConfigurationError: If Redis URL is not configured
        ValueError: If model costs are not found or prompt is empty
    """
    return asyncio.run(cached_agent_run(agent, prompt, task_name, *args, **kwargs)) 