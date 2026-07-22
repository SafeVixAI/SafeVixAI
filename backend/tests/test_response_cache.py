# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Response cache tests for SafeVixAI backend."""
from __future__ import annotations

import time

from core.response_cache import (
    ResponseCache,
    generate_cache_key,
    invalidate_cache_pattern,
    response_cache,
)

# ── Response Cache Tests ────────────────────────────────────────────────────

class TestResponseCache:
    """Tests for ResponseCache class."""

    def test_init_default(self):
        """Test default initialization."""
        cache = ResponseCache()
        assert cache._default_ttl == 300
        assert cache._max_size == 1000
        assert cache.size == 0

    def test_set_get(self):
        """Test set and get operations."""
        cache = ResponseCache()
        cache.set("test-key", "test-value")

        result = cache.get("test-key")
        assert result == "test-value"

    def test_get_missing(self):
        """Test get for missing key."""
        cache = ResponseCache()

        result = cache.get("missing-key")
        assert result is None

    def test_delete(self):
        """Test delete operation."""
        cache = ResponseCache()
        cache.set("test-key", "test-value")
        cache.delete("test-key")

        result = cache.get("test-key")
        assert result is None

    def test_clear(self):
        """Test clear operation."""
        cache = ResponseCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.size == 0
        assert cache._hits == 0
        assert cache._misses == 0

    def test_ttl_expiry(self):
        """Test TTL expiry."""
        cache = ResponseCache()
        cache.set("test-key", "test-value", ttl=1)

        # Wait for expiry
        time.sleep(1.1)

        result = cache.get("test-key")
        assert result is None

    def test_no_ttl_uses_default(self):
        """Test set without TTL uses default."""
        cache = ResponseCache(default_ttl=60)
        cache.set("test-key", "test-value")

        # Should not be expired
        result = cache.get("test-key")
        assert result == "test-value"

    def test_max_size_eviction(self):
        """Test max size eviction."""
        cache = ResponseCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict oldest

        assert cache.size <= 3

    def test_hit_rate(self):
        """Test hit rate calculation."""
        cache = ResponseCache()

        cache.set("test-key", "test-value")
        cache.get("test-key")  # Hit
        cache.get("test-key")  # Hit
        cache.get("missing")   # Miss

        assert cache.hit_rate == 0.6666666666666666

    def test_hit_rate_empty(self):
        """Test hit rate with no accesses."""
        cache = ResponseCache()
        assert cache.hit_rate == 0.0

    def test_get_stats(self):
        """Test statistics retrieval."""
        cache = ResponseCache()
        cache.set("test-key", "test-value")
        cache.get("test-key")

        stats = cache.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert "hit_rate" in stats


# ── Cache Key Generation Tests ──────────────────────────────────────────────

class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_generate_key_simple(self):
        """Test simple key generation."""
        key = generate_cache_key("test")
        assert key.startswith("test:")

    def test_generate_key_with_params(self):
        """Test key generation with parameters."""
        key1 = generate_cache_key("test", lat=13.0, lon=80.0)
        key2 = generate_cache_key("test", lat=13.0, lon=80.0)

        assert key1 == key2

    def test_generate_key_different_params(self):
        """Test different parameters generate different keys."""
        key1 = generate_cache_key("test", lat=13.0, lon=80.0)
        key2 = generate_cache_key("test", lat=14.0, lon=80.0)

        assert key1 != key2

    def test_generate_key_ignores_none(self):
        """Test None values are ignored."""
        key1 = generate_cache_key("test", lat=13.0, lon=None)
        key2 = generate_cache_key("test", lat=13.0)

        assert key1 == key2

    def test_generate_key_sorted_params(self):
        """Test parameters are sorted for consistency."""
        key1 = generate_cache_key("test", a=1, b=2, c=3)
        key2 = generate_cache_key("test", c=3, a=1, b=2)

        assert key1 == key2


# ── Cache Invalidation Tests ────────────────────────────────────────────────

class TestCacheInvalidation:
    """Tests for cache invalidation."""

    def test_invalidate_pattern(self):
        """Test pattern-based invalidation."""
        response_cache.set("api:users:123", "user1")
        response_cache.set("api:users:456", "user2")
        response_cache.set("api:posts:789", "post1")

        count = invalidate_cache_pattern("api:users")

        assert count == 2
        assert response_cache.get("api:users:123") is None
        assert response_cache.get("api:users:456") is None
        assert response_cache.get("api:posts:789") is not None

    def test_invalidate_no_match(self):
        """Test invalidation with no matches."""
        response_cache.set("api:users:123", "user1")

        count = invalidate_cache_pattern("nonexistent")

        assert count == 0
        assert response_cache.get("api:users:123") is not None


# ── Global Cache Instance Tests ─────────────────────────────────────────────

class TestGlobalCache:
    """Tests for global cache instance."""

    def test_global_cache_exists(self):
        """Test global cache instance exists."""
        from core.response_cache import response_cache
        assert response_cache is not None
        assert isinstance(response_cache, ResponseCache)

    def test_global_cache_stats(self):
        """Test global cache stats."""
        from core.response_cache import response_cache

        stats = response_cache.get_stats()
        assert "size" in stats
        assert "hits" in stats
        assert "misses" in stats
