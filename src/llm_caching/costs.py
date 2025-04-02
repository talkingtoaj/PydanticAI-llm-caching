"""Cost calculation for LLM usage."""

from typing import Any, NamedTuple, Dict, Optional

class ModelCosts(NamedTuple):
    """Cost structure for a model."""
    cost_per_million_input_tokens: float
    cost_per_million_output_tokens: float
    cost_per_million_caching_input_tokens: float
    cost_per_million_caching_hit_tokens: float

class TokenCounts(NamedTuple):
    """Container for different types of token counts from LLM usage."""
    input_tokens: int          # Regular input tokens
    output_tokens: int         # Regular output tokens
    cached_input_tokens: int   # Cached input tokens
    cached_output_tokens: int  # Cached output tokens

# Default cost mappings
DEFAULT_COSTS: Dict[str, ModelCosts] = {
    # Anthropic Models
    "claude-3-7-sonnet-latest": ModelCosts(
        cost_per_million_input_tokens=3.0,
        cost_per_million_output_tokens=15.0,
        cost_per_million_caching_input_tokens=3.75,
        cost_per_million_caching_hit_tokens=0.3,
    ),
    "claude-3-5-haiku-latest": ModelCosts(
        cost_per_million_input_tokens=0.8,
        cost_per_million_output_tokens=4.0,
        cost_per_million_caching_input_tokens=1.0,
        cost_per_million_caching_hit_tokens=0.08,
    ),
    # OpenAI Models
    "gpt-4o-mini": ModelCosts(
        cost_per_million_input_tokens=0.15,
        cost_per_million_output_tokens=0.6,
        cost_per_million_caching_input_tokens=0.0,
        cost_per_million_caching_hit_tokens=0.075,
    ),
    "o3-mini-2025-01-31": ModelCosts(
        cost_per_million_input_tokens=1.1,
        cost_per_million_output_tokens=4.4,
        cost_per_million_caching_input_tokens=0.0,
        cost_per_million_caching_hit_tokens=0.55,
    ),
    # Google Gemini Models
    "gemini-1.5-flash": ModelCosts(
        cost_per_million_input_tokens=0.075,
        cost_per_million_output_tokens=0.30,
        cost_per_million_caching_input_tokens=0.01875,
        cost_per_million_caching_hit_tokens=0.0,
    ),
    "gemini-2.0-flash-lite": ModelCosts(
        cost_per_million_input_tokens=0.075,
        cost_per_million_output_tokens=0.30,
        cost_per_million_caching_input_tokens=0.0,
        cost_per_million_caching_hit_tokens=0.0,
    ),
    "gemini-2.0-flash": ModelCosts(
        cost_per_million_input_tokens=0.10,
        cost_per_million_output_tokens=0.40,
        cost_per_million_caching_input_tokens=0.025,
        cost_per_million_caching_hit_tokens=0.0,
    ),
}

def get_model_costs(model_name: str, custom_costs: Optional[Dict[str, ModelCosts]] = None) -> ModelCosts:
    """Get costs for a model, using custom costs if provided."""
    # Combine default and custom costs, with custom taking precedence
    costs_map = DEFAULT_COSTS.copy()
    if custom_costs:
        costs_map.update(custom_costs)
    
    # Perform an exact lookup for the model_name
    if model_name in costs_map:
        return costs_map[model_name]
            
    # If exact match not found, try searching keys that *start with* model_name
    # (Handles cases like 'gpt-4-turbo' matching 'gpt-4-turbo-2024-04-09')
    # This is less likely now with the _get_model_name helper but kept as fallback
    for key in costs_map:
         if key.startswith(model_name):
             log.warning(f"Exact match for '{model_name}' not found, using costs for '{key}'")
             return costs_map[key]
             
    raise ValueError(
        f"Model '{model_name}' not found in cost mappings. "
        "Please provide custom costs via the custom_costs parameter or add to DEFAULT_COSTS."
    )

def get_token_counts(usage: Any) -> TokenCounts:
    """Get all token counts from usage data, separating regular and cached tokens."""
    # Get total token counts
    total_input = getattr(usage, 'request_tokens', 0) or 0
    total_output = getattr(usage, 'response_tokens', 0) or 0
    
    # Get cached tokens from details
    details = getattr(usage, 'details', None) or {}
    cached_input = details.get('cached_input_tokens', 0)
    cached_output = details.get('cached_output_tokens', 0)
    
    # Calculate regular tokens by subtracting cached tokens
    input_tokens = max(0, total_input - cached_input)
    output_tokens = max(0, total_output - cached_output)
    
    return TokenCounts(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_input,
        cached_output_tokens=cached_output
    )

def calculate_cost(model_name: str, result: Any, custom_costs: Optional[Dict[str, ModelCosts]] = None) -> float:
    """Calculate the cost of an LLM request using provider-specific token rates.
    
    Args:
        model_name: The model identifier (e.g. "claude-3-5-haiku-latest")
        result: The PydanticAI agent result containing usage information
        custom_costs: Optional dictionary of custom costs per model
        
    Returns:
        float: Total cost in dollars
        
    Raises:
        ValueError: If model costs are not found.
    """
    costs = get_model_costs(model_name, custom_costs)

    tokens = get_token_counts(result.usage())
    
    return (
        # Regular token costs
        (tokens.input_tokens * costs.cost_per_million_input_tokens +
         tokens.output_tokens * costs.cost_per_million_output_tokens +
        # Cached token costs
         tokens.cached_input_tokens * costs.cost_per_million_caching_input_tokens +
         tokens.cached_output_tokens * costs.cost_per_million_caching_hit_tokens
        ) / 1e6
    ) 