from typing import Any, NamedTuple, Dict, Optional

class ModelCosts(NamedTuple):
    cost_per_million_input_tokens: float
    cost_per_million_output_tokens: float
    cost_per_million_caching_input_tokens: float
    cost_per_million_caching_hit_tokens: float

class TokenCounts(NamedTuple):
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    cached_output_tokens: int

DEFAULT_COSTS: Dict[str, ModelCosts]

def get_model_costs(model_name: str, custom_costs: Optional[Dict[str, ModelCosts]] = None) -> ModelCosts: ...

def get_token_counts(usage: Any) -> TokenCounts: ...

def calculate_cost(model_name: str, result: Any, custom_costs: Optional[Dict[str, ModelCosts]] = None) -> float: ... 