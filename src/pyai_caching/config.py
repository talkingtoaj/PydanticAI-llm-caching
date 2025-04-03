"""Configuration settings for pyai-caching."""

import os
from typing import Optional
from urllib.parse import urlparse

class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass

def get_redis_url() -> str:
    """Get Redis URL from environment or raise helpful error."""
    redis_url = os.getenv('LLM_CACHE_REDIS_URL')
    if not redis_url:
        raise ConfigurationError(
            "Redis URL not configured. Please set LLM_CACHE_REDIS_URL environment variable.\n"
            "Example formats:\n"
            "  - redis://localhost:6379/0\n"
            "  - redis://username:password@hostname:port/db_number\n"
            "  - redis+sentinel://localhost:26379/mymaster/0\n"
            "  - rediss://hostname:port/0  # SSL/TLS connection"
        )
    
    try:
        parsed = urlparse(redis_url)
        if parsed.scheme not in ('redis', 'rediss', 'redis+sentinel'):
            raise ValueError(f"Invalid Redis URL scheme: {parsed.scheme}")
        return redis_url
    except Exception as e:
        raise ConfigurationError(f"Invalid Redis URL format: {e}")

def get_redis_client(url: Optional[str] = None) -> 'redis.Redis':
    """Get Redis client from URL."""
    import redis
    redis_url = url or get_redis_url()
    return redis.from_url(redis_url) 