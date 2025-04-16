"""Tests for the cached_agent_run functionality."""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, call, ANY, MagicMock
from dotenv import load_dotenv, find_dotenv
from pyai_caching import cached_agent_run, ConfigurationError, ModelCosts, RateLimitError, CacheError
from pydantic_ai import Agent, models
from pydantic import BaseModel, Field
from typing import List, Any
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ModelRequest, UserPromptPart
from conftest import MockUsage, MockResult
from pyai_caching.agent import cached_agent_run_sync


# Try loading with explicit path
env_path = find_dotenv()
if env_path:
    load_dotenv(env_path)
else:
    print("No .env file found!")

# Define MockResultData at the module level for pickling
class MockResultData(BaseModel):
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
        result_type=MockResultData,
        name="test_agent",
        system_prompt="You are a test agent that provides simple responses."
    )
    # Ensure NO mocking of agent.run is present
    return agent

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
    
    # Compare data fields for equality
    assert result1.data == result2.data
    mock_expense_recorder.assert_called_once_with(MODEL_NAME, "test", 0)

@pytest.mark.asyncio
async def test_cached_agent_run_with_history(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test cached_agent_run with message history."""
    history = [
        ModelRequest(parts=[UserPromptPart(content="previous message")]),
        ModelResponse(parts=[TextPart(content="previous response")])
    ]
    result = await cached_agent_run(
        agent=test_agent,
        prompt="test prompt",
        task_name="test",
        message_history=history,
        expense_recorder=mock_expense_recorder,
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    assert isinstance(result.data, MockResultData)
    assert isinstance(result.data.response, str)
    assert isinstance(result.data.confidence, float)

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
    with patch('pyai_caching.agent.get_redis_client') as mock_get_client:
        # Use MagicMock for synchronous client
        mock_client = MagicMock()
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
        assert isinstance(result.data, MockResultData)
        assert isinstance(result.data.response, str)
        assert isinstance(result.data.confidence, float)

@pytest.mark.asyncio
async def test_cached_agent_run_custom_ttl(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test custom TTL setting."""
    with patch('pyai_caching.agent.get_redis_client') as mock_get_client:
        # Use MagicMock for synchronous client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
    
        await cached_agent_run(
           agent=test_agent,
           prompt="test prompt",
           task_name="test",
           expense_recorder=mock_expense_recorder,
           redis_url=redis_url,
           custom_costs=custom_costs,
           ttl=60
        )
        
        # Assert Redis client was called with correct TTL
        mock_client.set.assert_called_once()
        # Check the 'ex' keyword argument passed to set()
        args, kwargs = mock_client.set.call_args
        assert kwargs.get('ex') == 60

@pytest.mark.asyncio
async def test_cached_agent_run_corrupted_cache(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test handling of corrupted cache data."""
    with patch('pyai_caching.agent.get_redis_client') as mock_get_client, \
         patch.object(test_agent, 'run', new_callable=AsyncMock) as mock_agent_run:
        
        # Setup Redis mock
        mock_client = MagicMock()
        mock_client.get.return_value = b'corrupted data'
        mock_get_client.return_value = mock_client
        
        # Setup agent.run mock to return a valid MockResultData structure
        # This uses the conftest MockUsage/MockResult structure for consistency
        usage = MockUsage(request_tokens=10, response_tokens=5)
        # Construct the expected result structure (MockResultData)
        expected_data = MockResultData(response="mock response", confidence=0.9)
        # Mock the full ModelResponse structure that agent.run returns
        mock_agent_run.return_value = MockResult(
            data=expected_data, 
            usage=usage
        )
        
        # Should fall back to running the mocked agent
        result = await cached_agent_run(
            agent=test_agent,
            prompt="test prompt",
            task_name="test",
            expense_recorder=mock_expense_recorder,
            redis_url=redis_url,
            custom_costs=custom_costs,
            ttl=60
        )
        
        # Check result type and attributes (should match the mocked agent.run response)
        assert isinstance(result.data, MockResultData)
        assert result.data == expected_data
        mock_agent_run.assert_awaited_once() # Verify agent.run was called

# Test for the synchronous wrapper
def test_cached_agent_run_sync_basic(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test basic sync functionality - checks structure, not exact content."""
    # Note: mock_expense_recorder is still AsyncMock, but asyncio.run handles awaiting it internally
    result = cached_agent_run_sync(
        agent=test_agent,
        prompt="Give a simple synchronous response.", # Prompt for sync test
        task_name="sync_test",
        expense_recorder=mock_expense_recorder,
        redis_url=redis_url,
        custom_costs=custom_costs
    )
    
    assert isinstance(result.data, MockResultData)
    assert isinstance(result.data.response, str)
    assert isinstance(result.data.confidence, float)
    assert 0 <= result.data.confidence <= 1
    # Check that the async expense recorder was eventually called
    mock_expense_recorder.assert_called_once_with(MODEL_NAME, "sync_test", ANY)

@pytest.mark.asyncio
async def test_cache_key_with_different_output_models(test_agent: Agent, mock_expense_recorder: AsyncMock, custom_costs, redis_url):
    """Test that different output models with the same name generate different cache keys."""
    from pyai_caching.agent import create_cache_key
    
    def create_agent_with_model1():
        class OutputModel(BaseModel):
            field1: str
            field2: int
        return Agent(test_agent.model, result_type=OutputModel)
    
    def create_agent_with_model2():
        class OutputModel(BaseModel):
            field1: str
            field3: float  # Different field name and type
        return Agent(test_agent.model, result_type=OutputModel)
    
    # Create agents in separate scopes
    agent1 = create_agent_with_model1()
    agent2 = create_agent_with_model2()
    
    # Same prompt for both agents
    prompt = "Test prompt"
    
    # Generate cache keys
    key1 = create_cache_key(agent1, prompt)
    key2 = create_cache_key(agent2, prompt)
    
    # Keys should be different due to different output model schemas
    assert key1 != key2, "Cache keys should be different for different output model schemas"
    
    # Verify the schema is included in the key
    assert "field2" in key1, "First model's schema should be in key1"
    assert "field3" in key2, "Second model's schema should be in key2"
    assert "field2" not in key2, "First model's schema should not be in key2"
    assert "field3" not in key1, "Second model's schema should not be in key1"
