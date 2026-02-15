"""Configuration settings for pyai-caching."""

import os
from typing import Optional, Union
from urllib.parse import urlparse

from .exceptions import ConfigurationError


def get_redis_url() -> str:
    """Get Redis URL from environment or raise helpful error."""
    redis_url = os.getenv("LLM_CACHE_REDIS_URL")
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
        if parsed.scheme not in ("redis", "rediss", "redis+sentinel"):
            raise ValueError(f"Invalid Redis URL scheme: {parsed.scheme}")
        return redis_url
    except Exception as e:
        raise ConfigurationError(f"Invalid Redis URL format: {e}")


def get_redis_client(url: Optional[str] = None) -> "redis.Redis":
    """Get synchronous Redis client from URL."""
    import redis

    redis_url = url or get_redis_url()
    return redis.from_url(redis_url)


async def get_async_redis_client(url: Optional[str] = None) -> "redis.asyncio.Redis":
    """Get asynchronous Redis client from URL."""
    import redis.asyncio

    redis_url = url or get_redis_url()
    return await redis.asyncio.from_url(redis_url)


def clear_cache(url: Optional[str] = None) -> int:
    """Clear all cached entries from Redis.
    
    Note: This will clear the entire Redis database if using the default
    database number. Use with caution.
    
    Args:
        url: Optional Redis URL (defaults to LLM_CACHE_REDIS_URL env var)
        
    Returns:
        Number of keys deleted
        
    Raises:
        ConfigurationError: If Redis URL is not configured
    """
    client = get_redis_client(url)
    try:
        return client.dbsize()
    finally:
        client.flushdb()


async def clear_cache_async(url: Optional[str] = None) -> int:
    """Clear all cached entries from Redis (async version).
    
    Note: This will clear the entire Redis database if using the default
    database number. Use with caution.
    
    Args:
        url: Optional Redis URL (defaults to LLM_CACHE_REDIS_URL env var)
        
    Returns:
        Number of keys deleted
        
    Raises:
        ConfigurationError: If Redis URL is not configured
    """
    client = await get_async_redis_client(url)
    try:
        count = await client.dbsize()
        await client.flushdb()
        return count
    finally:
        await client.aclose()
