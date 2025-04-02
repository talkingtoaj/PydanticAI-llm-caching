"""Benchmarks for LLM Caching performance."""

import os
import time
import asyncio
import pytest
from unittest.mock import AsyncMock
from llm_caching import cached_agent_run, ModelCosts
from conftest import Agent, MockUsage, MockResult

# Test configurations
TEST_CONFIGS = [
    {
        "name": "small_response",
        "size": 100,  # 100 bytes
        "concurrent_requests": 10
    },
    {
        "name": "medium_response",
        "size": 10000,  # 10KB
        "concurrent_requests": 5
    },
    {
        "name": "large_response",
        "size": 100000,  # 100KB
        "concurrent_requests": 3
    }
]

@pytest.fixture(params=TEST_CONFIGS)
def test_config(request):
    """Fixture to provide different test configurations."""
    return request.param

@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = AsyncMock(spec=Agent)
    agent.run = AsyncMock()
    return agent

@pytest.fixture
def custom_costs():
    """Define custom costs for benchmarking."""
    # Use "unknown" because mock_agent doesn't have a real model name
    return {
        "unknown": ModelCosts(
            cost_per_million_input_tokens=0.8,
            cost_per_million_output_tokens=4.0,
            cost_per_million_caching_input_tokens=1.0,
            cost_per_million_caching_hit_tokens=0.08,
        )
    }

@pytest.fixture
def redis_url():
    """Get Redis URL from environment."""
    url = os.getenv("LLM_CACHE_REDIS_URL")
    if not url:
        pytest.skip("Redis URL not configured in environment")
    return url

async def measure_time(func, *args, **kwargs):
    """Measure execution time of an async function."""
    start_time = time.perf_counter()
    result = await func(*args, **kwargs)
    end_time = time.perf_counter()
    return result, end_time - start_time
