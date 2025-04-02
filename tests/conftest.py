"""Test configuration and fixtures."""

from typing import Any, Optional, Protocol
from dataclasses import dataclass
import pytest
from unittest.mock import AsyncMock, MagicMock

@dataclass
class MockUsage:
    """Mock usage data for testing."""
    request_tokens: int = 0
    response_tokens: int = 0
    details: Optional[dict] = None

class Agent(Protocol):
    """Protocol for agent interface."""
    async def run(self, prompt: str, message_history: Optional[list[Any]] = None) -> Any: ...

class MockResult:
    """Mock result from agent run."""
    def __init__(self, data: Any, usage: MockUsage):
        self.data = data
        self._usage = usage

    def usage(self) -> MockUsage:
        """Get usage data."""
        return self._usage

@pytest.fixture
def mock_agent() -> Agent:
    """Create a mock agent for testing."""
    agent = MagicMock()
    agent.run = AsyncMock()
    # Set up default response
    usage = MockUsage(
        request_tokens=100,
        response_tokens=50,
        details={
            'cached_input_tokens': 0,
            'cached_output_tokens': 0
        }
    )
    agent.run.return_value = MockResult("test response", usage)
    return agent

@pytest.fixture
def mock_expense_recorder() -> AsyncMock:
    """Create a mock expense recorder."""
    return AsyncMock() 