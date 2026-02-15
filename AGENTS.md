# AGENTS.md - Agent Coding Guidelines

## Build/Lint/Test Commands

### Installation
```bash
poetry install
poetry run pre-commit install
```

### Running Tests
```bash
# All tests
poetry run pytest

# Single test file
poetry run pytest tests/test_agent.py

# Single test function
poetry run pytest tests/test_agent.py::test_cached_agent_run_with_cache_hit

# With coverage
poetry run pytest --cov

# Run type checker only
poetry run mypy src

# Run linter only
poetry run ruff check .
poetry run ruff format .
```

### Code Quality
```bash
# Format code
poetry run black .

# Run all checks (pre-commit)
poetry run pre-commit run --all-files
```

---

## Code Style Guidelines

### General
- **Line length**: 88 characters
- **Python version**: 3.10+ required, targets 3.9
- **Formatter**: Black
- **Linter**: Ruff (rules: E, F, I, N, W, B, UP, PL, RUF)
- **Type checker**: MyPy (strict mode)

### Type Hints
- All functions must have type hints
- Use `Any` sparingly - prefer concrete types
- Define custom types in `types.py`
- Generate `.pyi` stub files for public APIs

### Imports
```python
# Standard library first
import asyncio
import pickle
from typing import Any, Optional, Dict

# Third-party
from pydantic_ai import Agent
from pydantic import BaseModel, Field
import redis

# Local (use relative imports)
from .types import ExpenseRecorder
from .config import get_redis_client
from .costs import ModelCosts
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `CachedResult`)
- **Functions/methods**: `snake_case` (e.g., `cached_agent_run`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TTL`)
- **Private members**: `_leading_underscore`

### Docstrings
- Required on all public functions and classes
- Use Google-style docstrings with Args, Returns, Raises sections
```python
def function_name(param: str) -> int:
    """Short description.
    
    Longer description if needed.
    
    Args:
        param: Description of parameter.
        
    Returns:
        Description of return value.
        
    Raises:
        CustomError: When specific error occurs.
    """
```

---

## Error Handling

### Custom Exceptions
Define exceptions in `exceptions.py`. The project uses these custom exceptions:

```python
class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""
    pass

class RateLimitError(Exception):
    """Raised when rate limits are hit and max_wait exceeded."""
    pass

class CacheError(Exception):
    """Raised when cache operations fail."""
    pass

class ConnectionError(Exception):
    """Raised when Redis connection fails after retries."""
    pass
```

### Error Handling Patterns

**1. Cache Miss as Normal Flow**
```python
try:
    cached_result = redis_client.get(cache_key)
    if cached_result:
        log.debug(f"Cache hit for key: {cache_key}")
except Exception as e:
    log.warning(f"Error getting cache key: {e}")
    # Treat as cache miss, proceed to agent run
```

**2. Graceful Degradation**
```python
try:
    result = pickle.loads(bytes(cached_result))
    return result
except Exception as e:
    log.warning(f"Error unpickling cached result: {e}")
    # Fall through to run agent normally
```

**3. Retry with Exponential Backoff**
```python
wait_time = initial_wait
last_error = None

while retry_count < max_retries:
    try:
        result = await agent.run(prompt, **kwargs)
        return result
    except UsageLimitExceeded as e:
        last_error = e
        log.info(f"Rate limit hit. Waiting {wait_time} seconds...")
        await asyncio.sleep(wait_time)
        wait_time *= 2  # Exponential backoff
    except (asyncio.TimeoutError, ConnectionRefusedError) as e:
        retry_count += 1
        if retry_count >= max_retries:
            raise ConnectionError(f"Connection error after {max_retries} retries: {e}")
        await asyncio.sleep(min(wait_time * (2 ** retry_count), max_delay))
```

**4. Let Exceptions Propagate**
```python
except Exception as e:
    log.error(f"Unexpected error running agent: {e}")
    raise  # Re-raise unexpected errors
```

---

## Testing Patterns

### Test Structure
- Tests in `tests/` directory
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Fixtures
- Define fixtures in `tests/conftest.py`
- Common fixtures: `mock_expense_recorder`, `redis_url`, `test_agent`

### Mocking
```python
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.fixture
def mock_expense_recorder():
    return AsyncMock()

# Patch Redis client
with patch('pyai_caching.agent.get_redis_client') as mock_get_client:
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    # test code
```

### Async Tests
```python
@pytest.mark.asyncio
async def test_function():
    result = await async_function()
    assert result == expected
```

### Environment Variables for Tests
- Set `LLM_CACHE_REDIS_URL` in `.env` file
- Tests requiring Redis are skipped if URL not configured:
```python
@pytest.fixture
def redis_url():
    url = os.getenv("LLM_CACHE_REDIS_URL")
    if not url:
        pytest.skip("Redis URL not configured")
    return url
```

---

## Project Structure

```
pyai-caching/
├── src/pyai_caching/     # Source code
│   ├── __init__.py       # Public API exports
│   ├── agent.py          # Main caching logic
│   ├── config.py         # Redis configuration
│   ├── costs.py          # Cost calculation
│   ├── exceptions.py     # Custom exceptions
│   ├── types.py          # Type definitions
│   └── *.pyi             # Type stubs
├── tests/                # Test files
│   ├── conftest.py       # Fixtures
│   ├── test_agent.py     # Unit tests
│   ├── test_integration.py
│   ├── test_benchmarks.py
│   └── test_live_agent.py
├── pyproject.toml        # Project config (Poetry)
├── pytest.ini            # Pytest config
├── mypy.ini              # MyPy config
└── .pre-commit-config.yaml
```

---

## Pre-commit Hooks

The project uses pre-commit with these hooks:
- trailing-whitespace
- end-of-file-fixer
- check-yaml
- check-ast
- check-json
- check-merge-conflict
- detect-private-key
- black (formatting)
- ruff (linting + fix)
- ruff-format
- mypy (type checking)

---

## Key Dependencies

- **pydantic**: ^2.6.1
- **pydantic-ai**: ^0.1
- **redis**: ^5.0.1
- **pytest**: ^8.0.0 (dev)
- **pytest-asyncio**: ^0.23.5 (dev)
- **ruff**: ^0.2.1 (dev)
- **black**: ^24.1.1 (dev)
- **mypy**: ^1.8.0 (dev)
