# LLM Caching

A Redis-based caching library for PydanticAI LLM agents with cost tracking support.

Caching responses is particularly useful in testing and development scenarios.

Typically for tests, developers mock LLM results to avoid latency and cost issues. However this can
result in tests not detecting incorrect schemas for mocked data nor potential changes in LLM response schemas.

A cached response allows us to run the same prompts time and again without the cost or latency while being 
sure of real-world LLM responses.

Simply use `cached_agent_run` (async) or `cached_agent_run_sync` (sync) as a drop-in replacements for PydanticAI's `agent.run()` and `agent.run_sync()` respectively, to add support for caching, rate-limiting, and cost tracking.

NOTE: while `await agent.run()` returns a result, `await cached_agent_run()` will return result.data (i.e. the response without metadata); to obtain the full result object, use `await cached_agent_run(... , full_result=True)`

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Redis-based caching for PydanticAI Agent responses
- Configurable message format conversion
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
    result_type=UserProfile,
    name="profiler",
    system_prompt="You read transcripts and extract pertinent details for a profile record on a person."
)

result = await cached_agent_run(
    agent=profiler_agent,
    transcript_history=[{"role": "user", "content": "Hi, my name is Alex. I'm 30 years old and I enjoy hiking and reading science fiction."}] # Sample user description
    prompt="Make a profile on the user",
    task_name="make_profile"
)

profile = result # Corrected: cached_agent_run returns the data directly
print(type(profile))
# <class '__main__.UserProfile'> (or similar based on execution context)
print(profile)
# name='Alex' age=30 interests=['hiking', 'reading science fiction']
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

### Custom Message Conversion

You can provide custom message conversion logic:

```python
from typing import Any
from pyai_caching.types import ModelMessage

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
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
# Import caching functions and ModelCosts
from pyai_caching import cached_agent_run, cached_agent_run_sync, ModelCosts
# Import specific exceptions
from pyai_caching.exceptions import (
    RateLimitError, 
    CacheError, 
    ConfigurationError
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