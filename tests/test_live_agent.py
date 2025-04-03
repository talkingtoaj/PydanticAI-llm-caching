"""Tests using a real LLM agent to verify caching."""

import os
import pytest
from dotenv import load_dotenv, find_dotenv
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from pyai_caching import cached_agent_run, ModelCosts

# Load environment variables from .env
load_dotenv()

def create_random_letter_agent() -> Agent[None, str]:
    """Create a simple agent that returns 5 random letters."""
    return Agent(
        "anthropic:claude-3-5-haiku-latest",  # Using a fast, cheap model
        result_type=str,
        model_settings={"temperature": 1.0},  # Maximum temperature for randomness
        system_prompt=(
            "You are a random letter generator. "
            "When asked for letters, respond with exactly 5 random uppercase letters. "
            "No explanation, no other text, just the 5 letters."
        )
    )

@pytest.mark.asyncio
async def test_caching_with_live_agent():
    """Test that caching works with a real LLM agent."""
    # Create agent first to get its string representation
    agent = create_random_letter_agent()
    
    # Define custom costs for our model
    custom_costs = {
        str(agent): ModelCosts(
            cost_per_million_input_tokens=0.8,
            cost_per_million_output_tokens=4.0,
            cost_per_million_caching_input_tokens=1.0,
            cost_per_million_caching_hit_tokens=0.08,
        )
    }
    
    # Get Redis URL from environment
    redis_url = os.getenv("LLM_CACHE_REDIS_URL")
    if not redis_url:
        pytest.skip("Redis URL not configured in environment")
    
    # Create second agent instance
    agent2 = create_random_letter_agent()
    
    # First call should hit the API
    result1 = await cached_agent_run(
        agent=agent,
        prompt="Give me 5 random letters.",
        task_name="random_letters",
        custom_costs=custom_costs,
        redis_url=redis_url
    )
    
    print(f"\nFirst call result: {result1}")
    
    # Second call with different agent instance but same prompt should use cache
    result2 = await cached_agent_run(
        agent=agent2,
        prompt="Give me 5 random letters.",
        task_name="random_letters",
        custom_costs=custom_costs,
        redis_url=redis_url
    )
    
    print(f"Second call result: {result2}")
    
    # Results should be identical since second call used cache
    assert result1 == result2, "Cache miss: got different results for same prompt"
    
    # Different prompt should hit API again
    result3 = await cached_agent_run(
        agent=agent,
        prompt="Generate 5 random letters please.",
        task_name="random_letters",
        custom_costs=custom_costs,
        redis_url=redis_url
    )
    
    print(f"Different prompt result: {result3}")
    
    # Results should be different since it's a new API call with high temperature
    assert result1 != result3, "Expected different results for different prompt" 