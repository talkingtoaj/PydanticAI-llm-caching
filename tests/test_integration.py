"""Integration tests for LLM Caching with different Redis configurations."""

import os
from pydantic import BaseModel
import pytest
import asyncio
from pyai_caching import cached_agent_run, ModelCosts
from pydantic_ai import Agent
from test_agent import MockResultData, MODEL_NAME

@pytest.fixture
def redis_url():
    url = os.getenv("LLM_CACHE_REDIS_URL")
    if not url:
        pytest.skip("Redis URL not configured in environment")
    return url

@pytest.fixture
def test_agent():
    """Create a real Claude agent for testing."""
    return Agent(
        model=MODEL_NAME,
        result_type=MockResultData,
        name="test_agent",
        system_prompt="You are a test agent. Always respond with a short message and a confidence score between 0 and 1."
    )

@pytest.fixture
def custom_costs():
    """Define custom costs for testing integration."""
    return {
        MODEL_NAME: ModelCosts(
            cost_per_million_input_tokens=0.8,
            cost_per_million_output_tokens=4.0,
            cost_per_million_caching_input_tokens=1.0,
            cost_per_million_caching_hit_tokens=0.08,
        )
    }

@pytest.mark.asyncio
async def test_basic_caching(redis_url, test_agent, custom_costs):
    """Test basic caching functionality."""

    # choose a prompt unlikely to give the same result unless cached.
    prompt = "Give a simple response of random letters with high confidence."
    # First call to populate cache
    result1 = await cached_agent_run(
        agent=test_agent,
        prompt=prompt,
        task_name="test",
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    
    # Second call with same prompt should hit cache
    result2 = await cached_agent_run(
        agent=test_agent,
        prompt=prompt,
        task_name="test",
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    
    # Results should be equal
    assert result1.data == result2.data

# @pytest.mark.asyncio
# async def test_cache_expiration(redis_url, test_agent, custom_costs):
#     """Test cache expiration."""
#     # First call with short TTL
#     result1 = await cached_agent_run(
#         agent=test_agent,
#         prompt="Give 5 random letters",
#         task_name="test",
#         redis_url=redis_url,
#         custom_costs=custom_costs,
#         ttl=1  # 1 second TTL
#     )
    
#     # Wait for cache to expire
#     await asyncio.sleep(2)
    
#     # Should call agent again with a different prompt
#     result2 = await cached_agent_run(
#         agent=test_agent,
#         prompt="Give 5 random letters",
#         task_name="test",
#         redis_url=redis_url,
#         custom_costs=custom_costs
#     )
    
#     assert isinstance(result1.data, MockResultData)
#     assert isinstance(result2.data, MockResultData)
#     # Results should be different since we used different prompts
#     assert result1.data != result2.data
