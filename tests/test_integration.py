"""Integration tests for LLM Caching with different Redis configurations."""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock
from typing import Dict
from pyai_caching import cached_agent_run, ModelCosts
from conftest import Agent, MockUsage, MockResult

@pytest.fixture
def redis_url():
    url = os.getenv("LLM_CACHE_REDIS_URL")
    if not url:
        pytest.skip("Redis URL not configured in environment")
    return url

@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = AsyncMock(spec=Agent)
    agent.run = AsyncMock()
    usage = MockUsage(request_tokens=100, response_tokens=50)
    result = MockResult("test response", usage)
    agent.run.return_value = result
    return agent

@pytest.fixture
def custom_costs():
    """Define custom costs for testing integration."""
    # Use "unknown" because mock_agent doesn't have a real model name
    return {
        "unknown": ModelCosts(
            cost_per_million_input_tokens=0.8,
            cost_per_million_output_tokens=4.0,
            cost_per_million_caching_input_tokens=1.0,
            cost_per_million_caching_hit_tokens=0.08,
        )
    }

@pytest.mark.asyncio
async def test_basic_caching(redis_url, mock_agent, custom_costs):
    """Test basic caching functionality."""
    # First call to populate cache
    result1 = await cached_agent_run(
        agent=mock_agent,
        prompt="test prompt",
        task_name="test",
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    
    # Reset mock to verify cache hit
    mock_agent.run.reset_mock()
    
    # Second call should use cache
    result2 = await cached_agent_run(
        agent=mock_agent,
        prompt="test prompt",
        task_name="test",
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    
    assert result1 == result2 == "test response"
    mock_agent.run.assert_not_called()

@pytest.mark.asyncio
async def test_concurrent_access(redis_url, mock_agent, custom_costs):
    """Test concurrent access to cache."""
    async def run_agent():
        return await cached_agent_run(
            agent=mock_agent,
            prompt="test prompt",
            task_name="test",
            redis_url=redis_url,
            custom_costs=custom_costs
        )
    
    # Run multiple concurrent requests
    results = await asyncio.gather(*[run_agent() for _ in range(5)])
    
    # Verify all results are correct
    assert all(r == "test response" for r in results)
    # Verify agent was only called once
    assert mock_agent.run.call_count == 1

@pytest.mark.asyncio
async def test_cache_expiration(redis_url, mock_agent, custom_costs):
    """Test cache expiration."""
    # First call with short TTL
    await cached_agent_run(
        agent=mock_agent,
        prompt="test prompt",
        task_name="test",
        redis_url=redis_url,
        custom_costs=custom_costs,
        ttl=1  # 1 second TTL
    )
    
    # Reset mock
    mock_agent.run.reset_mock()
    
    # Wait for cache to expire
    await asyncio.sleep(2)
    
    # Should call agent again
    result = await cached_agent_run(
        agent=mock_agent,
        prompt="test prompt",
        task_name="test",
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    
    assert result == "test response"
    mock_agent.run.assert_called_once()
