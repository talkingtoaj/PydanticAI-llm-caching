"""Exceptions for the pyai-caching package."""

class RateLimitError(Exception):
    """Raised when a rate limit is hit."""
    pass

class CacheError(Exception):
    """Raised when there is an error with the cache."""
    pass

class ConnectionError(Exception):
    """Raised when there is a connection-level error."""
    pass 