# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Redis Cache Helper tests for SafeVixAI backend."""
from __future__ import annotations

import json
import time
from unittest.mock import MagicMock

import pytest

from core.redis_client import CacheHelper, create_cache

# ── Cache Helper Memory Backend Tests ───────────────────────────────────────

class TestCacheHelperMemory:
    """Tests for CacheHelper with memory backend (no Redis)."""

    def test_init_without_redis(self):
        """Test initialization without Redis."""
        cache = CacheHelper()
        assert cache._client is None
        assert cache.backend_name == "memory"
        assert cache.enabled is True

    def test_memory_set_get(self):
        """Test memory set and get operations."""
        cache = CacheHelper()

        cache._memory_set("test-key", "test-value")
        result = cache._memory_get("test-key")

        assert result == "test-value"

    def test_memory_get_missing(self):
        """Test memory get for missing key."""
        cache = CacheHelper()

        result = cache._memory_get("missing-key")
        assert result is None

    def test_memory_delete(self):
        """Test memory delete operation."""
        cache = CacheHelper()

        cache._memory_set("test-key", "test-value")
        cache._memory_delete("test-key")

        result = cache._memory_get("test-key")
        assert result is None

    def test_memory_ttl_expiry(self):
        """Test memory TTL expiry."""
        cache = CacheHelper()

        # Set with 0 second TTL (expired immediately)
        cache._memory_set("test-key", "test-value", ttl_seconds=0)

        # Wait a tiny bit
        time.sleep(0.01)

        result = cache._memory_get("test-key")
        assert result is None

    def test_memory_no_ttl(self):
        """Test memory set without TTL."""
        cache = CacheHelper()

        cache._memory_set("test-key", "test-value")
        result = cache._memory_get("test-key")

        assert result == "test-value"


# ── Cache Helper Async Operations Tests ─────────────────────────────────────

class TestCacheHelperAsyncOps:
    """Tests for CacheHelper async operations."""

    @pytest.mark.asyncio
    async def test_get_json_memory(self):
        """Test get_json from memory."""
        cache = CacheHelper()

        cache._memory_set("test-key", '{"name": "test"}')
        result = await cache.get_json("test-key")

        assert result == {"name": "test"}

    @pytest.mark.asyncio
    async def test_get_json_missing(self):
        """Test get_json for missing key."""
        cache = CacheHelper()

        result = await cache.get_json("missing-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_json_memory(self):
        """Test set_json to memory."""
        cache = CacheHelper()

        await cache.set_json("test-key", {"name": "test"}, ttl_seconds=60)
        result = cache._memory_get("test-key")

        assert result is not None
        assert json.loads(result) == {"name": "test"}

    @pytest.mark.asyncio
    async def test_delete_memory(self):
        """Test delete from memory."""
        cache = CacheHelper()

        cache._memory_set("test-key", "test-value")
        await cache.delete("test-key")

        result = cache._memory_get("test-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_int_memory(self):
        """Test get_int from memory."""
        cache = CacheHelper()

        cache._memory_set("counter", "42")
        result = await cache.get_int("counter")

        assert result == 42

    @pytest.mark.asyncio
    async def test_get_int_missing(self):
        """Test get_int for missing key."""
        cache = CacheHelper()

        result = await cache.get_int("missing-counter", default=10)
        assert result == 10

    @pytest.mark.asyncio
    async def test_get_int_invalid(self):
        """Test get_int with invalid value."""
        cache = CacheHelper()

        cache._memory_set("counter", "not-a-number")
        result = await cache.get_int("counter", default=5)

        assert result == 5

    @pytest.mark.asyncio
    async def test_increment_memory(self):
        """Test increment in memory."""
        cache = CacheHelper()

        cache._memory_set("counter", "5")
        result = await cache.increment("counter")

        assert result == 6

    @pytest.mark.asyncio
    async def test_increment_missing(self):
        """Test increment for missing key."""
        cache = CacheHelper()

        result = await cache.increment("new-counter")

        assert result == 1

    @pytest.mark.asyncio
    async def test_ping_memory(self):
        """Test ping with memory backend."""
        cache = CacheHelper()

        result = await cache.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_close_memory(self):
        """Test close with memory backend."""
        cache = CacheHelper()

        # Should not raise
        await cache.close()


# ── Create Cache Factory Tests ──────────────────────────────────────────────

class TestCreateCache:
    """Tests for create_cache factory function."""

    def test_create_cache_without_url(self):
        """Test create_cache without Redis URL."""
        cache = create_cache(None)
        assert cache._client is None
        assert cache.backend_name == "memory"

    def test_create_cache_with_empty_url(self):
        """Test create_cache with empty URL."""
        cache = create_cache("")
        assert cache._client is None
        assert cache.backend_name == "memory"


# ── Cache Helper Properties Tests ───────────────────────────────────────────

class TestCacheHelperProperties:
    """Tests for CacheHelper properties."""

    def test_enabled_always_true(self):
        """Test enabled property is always True."""
        cache = CacheHelper()
        assert cache.enabled is True

    def test_backend_name_memory(self):
        """Test backend_name for memory backend."""
        cache = CacheHelper()
        assert cache.backend_name == "memory"

    def test_backend_name_redis_healthy(self):
        """Test backend_name for healthy Redis."""
        mock_redis = MagicMock()
        cache = CacheHelper(client=mock_redis)
        assert cache.backend_name == "redis"

    def test_backend_name_redis_unhealthy(self):
        """Test backend_name for unhealthy Redis."""
        mock_redis = MagicMock()
        cache = CacheHelper(client=mock_redis)
        cache._redis_healthy = False
        assert cache.backend_name == "redis+memory"


# ── Cache Helper Bytes Handling Tests ───────────────────────────────────────

class TestCacheHelperBytesHandling:
    """Tests for CacheHelper bytes handling."""

    @pytest.mark.asyncio
    async def test_get_json_bytes_payload(self):
        """Test get_json with bytes payload."""
        cache = CacheHelper()

        cache._memory_set("test-key", b'{"name": "test"}')
        result = await cache.get_json("test-key")

        assert result == {"name": "test"}
