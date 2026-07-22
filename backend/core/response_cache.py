# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Response caching middleware for SafeVixAI backend.

DEPRECATED: Use core.redis_client.CacheHelper instead. Will be removed in v4.0.

Provides:
- In-memory cache with TTL for frequently accessed endpoints
- Cache invalidation helpers
- Cache key generation utilities
- Cache statistics tracking

Phase 3: Performance optimization layer.
"""
from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class ResponseCache:
    """In-memory response cache with TTL support."""

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get cached value if exists and not expired."""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None

        expires_at, value = entry
        if time.time() > expires_at:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cache value with TTL."""
        if len(self._cache) >= self._max_size:
            self._evict_expired()

        if len(self._cache) >= self._max_size:
            # Evict oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]

        ttl = ttl or self._default_ttl
        expires_at = time.time() + ttl
        self._cache[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        """Delete cache entry."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def _evict_expired(self) -> None:
        """Remove expired entries."""
        now = time.time()
        expired_keys = [
            key for key, (expires_at, _) in self._cache.items()
            if now > expires_at
        ]
        for key in expired_keys:
            del self._cache[key]

    @property
    def hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": self.size,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
        }


def generate_cache_key(prefix: str, **kwargs: Any) -> str:
    """Generate cache key from prefix and parameters."""
    key_parts = [prefix]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}={v}")

    key_string = "|".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
    return f"{prefix}:{key_hash}"


# Global cache instance
response_cache = ResponseCache(default_ttl=300, max_size=1000)


def cache_response(ttl: int = 300, key_prefix: str = "api"):
    """Decorator to cache FastAPI endpoint responses.
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and kwargs
            cache_key = generate_cache_key(
                f"{key_prefix}:{func.__name__}",
                **{k: v for k, v in kwargs.items() if v is not None}
            )

            # Check cache
            cached = response_cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for %s", cache_key)
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            response_cache.set(cache_key, result, ttl=ttl)
            logger.debug("Cache set for %s (ttl=%d)", cache_key, ttl)

            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate cache entries matching pattern.
    
    Args:
        pattern: Pattern to match cache keys
        
    Returns:
        Number of invalidated entries
    """
    keys_to_delete = [key for key in response_cache._cache.keys() if pattern in key]
    for key in keys_to_delete:
        del response_cache._cache[key]
    return len(keys_to_delete)
