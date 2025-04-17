from typing import List, Dict, Any
from pydantic_ai import Agent
from pyai_caching import cached_agent_run
from pyai_caching.costs import ModelCosts, TokenCounts, calculate_cost
from pyai_caching.config import get_redis_client
from pydantic import BaseModel

# Test with custom agent types
class MyInput:
    def __init__(self, prompt: str):
        self.prompt = prompt

class MyOutput(BaseModel):
    response: str
    confidence: float

# Create a typed agent
agent: Agent[MyInput, MyOutput] = Agent()  # type: ignore

# Test async function with type hints
async def test_cached_run() -> None:
    # This should type check correctly
    result = await cached_agent_run(
        agent=agent,
        prompt="test prompt",
        task_name="test_task"
    )
    
    # Verify result type
    assert isinstance(result.output, MyOutput)
    assert isinstance(result.output.response, str)
    assert isinstance(result.output.confidence, float)
    
    # This should raise a type error
    result2 = await cached_agent_run(
        agent=agent,
        prompt=123,  # type: ignore  # Wrong type for prompt
        task_name="test_task"
    )

# Test cost calculation with type hints
def test_costs() -> None:
    costs = ModelCosts(
        cost_per_million_input_tokens=0.1,
        cost_per_million_output_tokens=0.2,
        cost_per_million_caching_input_tokens=0.3,
        cost_per_million_caching_hit_tokens=0.4
    )
    
    # This should raise a type error
    bad_costs = ModelCosts(
        cost_per_million_input_tokens="0.1",  # type: ignore  # Wrong type
        cost_per_million_output_tokens=0.2,
        cost_per_million_caching_input_tokens=0.3,
        cost_per_million_caching_hit_tokens=0.4
    )

    tokens = TokenCounts(
        input_tokens=100,
        output_tokens=200,
        cached_input_tokens=300,
        cached_output_tokens=400
    )
    
    # This should raise a type error
    bad_tokens = TokenCounts(
        input_tokens="100",  # type: ignore  # Wrong type
        output_tokens=200,
        cached_input_tokens=300,
        cached_output_tokens=400
    ) 