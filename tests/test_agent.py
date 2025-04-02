"""Tests for the cached_agent_run functionality."""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, call, ANY, MagicMock
from dotenv import load_dotenv, find_dotenv
from llm_caching import cached_agent_run, ConfigurationError, ModelCosts, RateLimitError, CacheError
from pydantic_ai import Agent, models
from pydantic import BaseModel, Field
from typing import List, Any
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from conftest import MockUsage, MockResult


# Try loading with explicit path
env_path = find_dotenv()
if env_path:
    load_dotenv(env_path)
else:
    print("No .env file found!")

# Define TestResult at the module level for pickling
class TestResult(BaseModel):
    response: str = Field(..., description="The response text")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)

@pytest.fixture
def mock_expense_recorder():
    return AsyncMock()

MODEL_NAME = "claude-3-5-haiku-latest"

@pytest.fixture
def custom_costs():
    # Use the actual model name as the key
    return {
        MODEL_NAME: ModelCosts(
            cost_per_million_input_tokens=0.8,
            cost_per_million_output_tokens=4.0,
            cost_per_million_caching_input_tokens=1.0,
            cost_per_million_caching_hit_tokens=0.08,
        )
    }

@pytest.fixture
def redis_url():
    url = os.getenv("LLM_CACHE_REDIS_URL")
    if not url:
        pytest.skip("Redis URL not configured in environment")
    return url

@pytest.fixture
def test_agent():
    """Create a test agent using a real model name, without mocking run."""
    agent = Agent(
        model=MODEL_NAME, 
        result_type=TestResult,
        name="test_agent",
        system_prompt="You are a test agent that provides simple responses."
    )
    # Ensure NO mocking of agent.run is present
    return agent

@pytest.mark.asyncio
async def test_cached_agent_run_basic(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test basic functionality - checks structure, not exact content."""
    result = await cached_agent_run(
        agent=test_agent,
        prompt="Give a simple response with high confidence.", # Prompt that fits the TestResult schema
        task_name="test",
        expense_recorder=mock_expense_recorder,
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    
    assert isinstance(result, TestResult)
    assert isinstance(result.response, str)
    assert isinstance(result.confidence, float)
    assert 0 <= result.confidence <= 1
    mock_expense_recorder.assert_called_once_with(MODEL_NAME, "test", ANY)

@pytest.mark.asyncio
async def test_cached_agent_run_with_cache_hit(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test cached_agent_run when result is in cache, comparing data."""
    prompt = "Give a simple response with high confidence for cache hit test."
    # First call to populate cache
    result1 = await cached_agent_run(
        agent=test_agent,
        prompt=prompt,
        task_name="test",
        expense_recorder=mock_expense_recorder,
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    
    mock_expense_recorder.reset_mock()
    
    # Second call should use cache
    result2 = await cached_agent_run(
        agent=test_agent,
        prompt=prompt, # Use the exact same prompt
        task_name="test",
        expense_recorder=mock_expense_recorder,
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    
    # Compare model dumps for equality, as object IDs will differ after unpickling
    assert result1.model_dump() == result2.model_dump()
    mock_expense_recorder.assert_called_once_with(MODEL_NAME, "test", 0)

@pytest.mark.asyncio
async def test_cached_agent_run_with_history(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test cached_agent_run with message history."""
    history = [{"role": "user", "content": "previous message"}]
    result = await cached_agent_run(
        agent=test_agent,
        prompt="test prompt",
        task_name="test",
        transcript_history=history,
        expense_recorder=mock_expense_recorder,
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    assert isinstance(result, TestResult)
    # Expense recorder assertion might be needed here too

@pytest.mark.asyncio
async def test_cached_agent_run_missing_redis_url():
    """Test that missing Redis URL raises appropriate error."""
    # Store original Redis URL
    original_url = os.environ.get('LLM_CACHE_REDIS_URL')
    try:
        if 'LLM_CACHE_REDIS_URL' in os.environ:
            del os.environ['LLM_CACHE_REDIS_URL']
        with pytest.raises(ConfigurationError) as exc_info:
            # Use the real model name here as well
            await cached_agent_run(
                agent=Agent(model=MODEL_NAME),
                prompt="test",
                task_name="test"
            )
        assert "Redis URL not configured" in str(exc_info.value)
    finally:
        if original_url is not None:
            os.environ['LLM_CACHE_REDIS_URL'] = original_url

@pytest.mark.asyncio
async def test_cached_agent_run_cache_error(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test handling of cache errors."""
    with patch('llm_caching.agent.get_redis_client') as mock_get_client:
        # Make Redis client raise an error
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Redis error")
        mock_get_client.return_value = mock_client
        
        # Should still work even if cache fails
        result = await cached_agent_run(
            agent=test_agent,
            prompt="test prompt",
            task_name="test",
            expense_recorder=mock_expense_recorder,
            redis_url=redis_url,
            custom_costs=custom_costs
        )
        
        # Check result type and attributes
        assert isinstance(result, TestResult)
        assert isinstance(result.response, str)
        assert isinstance(result.confidence, float)

@pytest.mark.asyncio
async def test_cached_agent_run_corrupted_cache(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test handling of corrupted cache data."""
    with patch('llm_caching.agent.get_redis_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get.return_value = b'corrupted data'
        mock_get_client.return_value = mock_client
        
        # Should fall back to running the agent
        result = await cached_agent_run(
            agent=test_agent,
            prompt="test prompt",
            task_name="test",
            expense_recorder=mock_expense_recorder,
            redis_url=redis_url,
            custom_costs=custom_costs
        )
        
        # Check result type and attributes
        assert isinstance(result, TestResult)
        assert isinstance(result.response, str)
        assert isinstance(result.confidence, float)
