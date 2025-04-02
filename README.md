# LLM Caching

A Redis-based caching library for LLM agents with cost tracking support.

[![PyPI version](https://badge.fury.io/py/llm-caching.svg)](https://badge.fury.io/py/llm-caching)
[![Python Versions](https://img.shields.io/pypi/pyversions/llm-caching.svg)](https://pypi.org/project/llm-caching/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://codecov.io/gh/yourusername/llm-caching/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/llm-caching)
[![CI](https://github.com/yourusername/llm-caching/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/llm-caching/actions/workflows/ci.yml)

## Features

- Redis-based caching for LLM responses
- Configurable message format conversion
- Flexible expense tracking
- Rate limit handling with exponential backoff
- Support for multiple LLM providers
- Customizable cost tables for different models
- Type-safe implementation
- Comprehensive test coverage

## Installation

```bash
# Using Poetry (recommended)
poetry add llm-caching

# Using pip
pip install llm-caching
```

## Quick Start

```python
from llm_caching import cached_agent_run
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List

# Basic usage with defaults
result = await cached_agent_run(
    agent=your_agent,
    prompt="Hello",
    task_name="chat"
)

# Using Pydantic models
class UserProfile(BaseModel):
    name: str
    age: int
    interests: List[str]

# Create a profile
profile = UserProfile(
    name="John Doe",
    age=30,
    interests=["AI", "Python", "Machine Learning"]
)

# Pass the Pydantic model in message history
result = await cached_agent_run(
    agent=your_agent,
    prompt="Analyze this profile",
    task_name="profile_analysis",
    transcript_history=[{"role": "user", "content": profile.model_dump_json()}]
)

# Advanced usage with custom message conversion and expense tracking
async def my_expense_recorder(model: str, task_name: str, cost: float) -> None:
    # Your expense recording logic here
    print(f"Cost for {model} on {task_name}: ${cost}")

def my_message_converter(messages: list[Any]) -> list[ModelMessage]:
    # Your message conversion logic here
    return [ModelMessage(role="user", content=str(m)) for m in messages]

result = await cached_agent_run(
    agent=your_agent,
    prompt="Hello",
    task_name="chat",
    message_converter=my_message_converter,
    expense_recorder=my_expense_recorder
)
```

## Configuration

### Redis Configuration

The library requires a Redis URL to be configured. You can provide it in two ways:

1. Environment variable (recommended):
```bash
export LLM_CACHE_REDIS_URL="redis://localhost:6379/0"
```

2. Direct configuration in code:
```python
result = await cached_agent_run(
    agent=your_agent,
    prompt="Hello",
    task_name="chat",
    redis_url="redis://localhost:6379/0"
)
```

Supported URL formats:
- `redis://[[username]:[password]]@localhost:6379/0`
- `rediss://hostname:port/0`  # SSL/TLS connection
- `redis+sentinel://localhost:26379/mymaster/0`

### Cost Configuration

The library comes with default cost tables for popular models. You can provide custom costs for your models:

```python
from llm_caching import cached_agent_run, ModelCosts

# Define custom costs
custom_costs = {
    "my-custom-model": ModelCosts(
        cost_per_million_input_tokens=1.0,
        cost_per_million_output_tokens=2.0,
        cost_per_million_caching_input_tokens=0.5,
        cost_per_million_caching_hit_tokens=0.1,
    )
}

# Use custom costs
result = await cached_agent_run(
    agent=your_agent,
    prompt="Hello",
    task_name="chat",
    custom_costs=custom_costs
)
```

## Advanced Usage

### Rate Limit Handling

The library includes built-in rate limit handling with exponential backoff:

```python
result = await cached_agent_run(
    agent=your_agent,
    prompt="Hello",
    task_name="chat",
    max_wait=30.0,  # Maximum wait time before giving up
    initial_wait=1.0  # Initial wait time for exponential backoff
)
```

### Custom Message Conversion

You can provide custom message conversion logic:

```python
from typing import Any
from llm_caching.types import ModelMessage

def custom_message_converter(messages: list[Any]) -> list[ModelMessage]:
    converted = []
    for msg in messages:
        if isinstance(msg, dict):
            converted.append(ModelMessage(
                role=msg.get("role", "user"),
                content=str(msg.get("content", ""))
            ))
        else:
            converted.append(ModelMessage(
                role="user",
                content=str(msg)
            ))
    return converted

result = await cached_agent_run(
    agent=your_agent,
    prompt="Hello",
    task_name="chat",
    message_converter=custom_message_converter
)
```

### Expense Tracking

Implement custom expense tracking:

```python
import logging
from datetime import datetime

async def expense_tracker(model: str, task_name: str, cost: float) -> None:
    logging.info(f"Expense: {datetime.now()} - Model: {model}, Task: {task_name}, Cost: ${cost}")
    # Add your expense tracking logic here
    # e.g., save to database, send to monitoring service, etc.

result = await cached_agent_run(
    agent=your_agent,
    prompt="Hello",
    task_name="chat",
    expense_recorder=expense_tracker
)
```

## Error Handling

The library provides specific exceptions for different error cases:

```python
from llm_caching.exceptions import (
    ConfigurationError,
    RateLimitError,
    CacheError
)

try:
    result = await cached_agent_run(
        agent=your_agent,
        prompt="Hello",
        task_name="chat"
    )
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except CacheError as e:
    print(f"Cache error: {e}")
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history. 