# LLM Caching

A Redis-based caching library for PydanticAI LLM agents with cost tracking support.

Caching responses is particularly useful in testing and development scenarios.

Typically for tests, developers mock LLM results to avoid latency and cost issues. However this can
result in tests not detecting incorrect schemas for mocked data nor potential changes in LLM response schemas.

A cached response allows us to run the same prompts time and again without the cost or latency while being 
sure of real-world LLM responses.

Simply use `cached_agent_run` (async) or `cached_agent_run_sync` (sync) as a drop-in replacements for PydanticAI's `agent.run()` and `agent.run_sync()` respectively, to add support for caching, rate-limiting, and cost tracking.

NOTE: `cached_agent_run` and `cached_agent_run_sync` always return the complete result object, including data, usage information, and metadata.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Redis-based caching for PydanticAI Agent responses
- Flexible expense tracking
- Rate limit handling with exponential backoff
- Customizable cost tables for different models
- Type-safe implementation
- Comprehensive test coverage

## Installation

```bash
pip install pyai-caching
```

## Quick Start

Set an Environment variable to point to your redis cache:
```bash
export LLM_CACHE_REDIS_URL="redis://localhost:6379/0"
```

```python
import os
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pyai_caching import cached_agent_run
from typing import List

class UserProfile(BaseModel):
    name: str
    age: int
    interests: List[str]

profiler_agent = Agent(
    model="anthropic:claude-3-5-haiku-latest", 
    output_type=UserProfile,
    name="profiler",
    system_prompt="You read transcripts and extract pertinent details for a profile record on a person."
)

# The function returns the complete result object
result = await cached_agent_run(
    agent=profiler_agent,
    prompt="Make a profile on the user",
    task_name="make_profile",
    message_history=[{
        "role": "user", 
        "content": "Hi, my name is Alex. I'm 30 years old and I enjoy hiking and reading science fiction."
    }]
)

# Access the typed data from the result
profile = result.output
print(type(profile))
# <class '__main__.UserProfile'> (or similar based on execution context)
print(profile)
# name='Alex' age=30 interests=['hiking', 'reading science fiction']

# Access metadata from the result object
print(result.model)  # The model used
print(result.usage)  # Token usage information
print(result.cost)   # The cost of the request
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
# Example using async version
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

## Migration Guide

### Version 0.2.0 Changes

1. Complete Result Objects
   - Both `cached_agent_run` and `cached_agent_run_sync` now always return the complete result object
   - The result object includes:
     - `data`: The typed response data
     - `usage`: Token usage information
     - `metadata`: Any additional model-specific metadata

2. Simplified Parameter Structure
   - Removed `transcript_history` parameter (use `message_history` instead)
   - Removed `message_converter` parameter (message conversion is now handled internally)
   - All additional parameters are passed directly to `agent.run` via `**kwargs`

3. Message History Handling
   - Message history is now passed directly via the `message_history` parameter
   - Messages are automatically converted to the appropriate format
   - The cache key incorporates the message history to ensure unique caching per conversation context

Example of migrating from 0.1.x to 0.2.0:

```python
# Old code (0.1.x)
result = await cached_agent_run(
    agent=agent,
    prompt="Hello",
    task_name="chat",
    transcript_history=["User: Hi", "Assistant: Hello!"],
    message_converter=my_converter,
    full_result=True
)

# New code (0.2.0)
result = await cached_agent_run(
    agent=agent,
    prompt="Hello",
    task_name="chat",
    message_history=[
        ModelRequest(parts=[UserPromptPart(content="Hi")]),
        ModelResponse(parts=[TextPart(content="Hello!")])
    ]
)
```

## Error Handling

The library provides specific exceptions for different error cases:

```python
from pyai_caching.exceptions import UsageLimitExceeded, ConfigurationError

try:
    result = await cached_agent_run(
        agent=your_agent,
        prompt="Hello",
        task_name="chat"
    )
except UsageLimitExceeded:
    print("Rate limit exceeded and max wait time reached")
except ConfigurationError:
    print("Redis URL not configured")
except ValueError as e:
    print(f"Invalid input: {e}")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history. 

## Migration Guide (v0.2.0)

### Breaking Changes

1. Return Value Changes
   - `cached_agent_run` and `cached_agent_run_sync` now always return the complete result object
   - The `full_result` parameter has been removed
   - To access just the data, use `result.output` instead of the result directly

2. Message History Handling
   - The `transcript_history` parameter has been removed in favor of `message_history`
   - Message history is now passed directly through kwargs
   - The `message_converter` parameter has been removed - messages are now handled natively

### Before (v0.1.x)
```python
result = await cached_agent_run(
    agent=agent,
    transcript_history=[{"role": "user", "content": "Hello"}],
    prompt="Reply to the user",
    task_name="chat",
    message_converter=my_converter,
    full_result=False
)
# result contains just the data
```

### After (v0.2.0)
```python
result = await cached_agent_run(
    agent=agent,
    message_history=[{"role": "user", "content": "Hello"}],
    prompt="Reply to the user",
    task_name="chat"
)
# result contains the full result object
data = result.output  # Access just the data
```