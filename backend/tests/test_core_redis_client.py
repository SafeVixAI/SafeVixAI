# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Redis Cache Helper tests for SafeVixAI backend."""
from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.redis_client import CacheHelper, create_cache

# ── Cache Helper Memory Backend Tests ───────────────────────────────────────

class TestCacheHelperMemory:
    """Tests for CacheHelper with memory backend (no Redis)."""

    def test_init_without_redis(self):
        cache = CacheHelper()
        assert cache._client is None
        assert cache.backend_name == "memory"
        assert cache.enabled is True

    def test_memory_set_get(self):
        cache = CacheHelper()
        cache._memory_set("test-key", "test-value")
        result = cache._memory_get("test-key")
        assert result == "test-value"

    def test_memory_get_missing(self):
        cache = CacheHelper()
        result = cache._memory_get("missing-key")
        assert result is None

    def test_memory_delete(self):
        cache = CacheHelper()
        cache._memory_set("test-key", "test-value")
        cache._memory_delete("test-key")
        result = cache._memory_get("test-key")
        assert result is None

    def test_memory_ttl_expiry(self):
        cache = CacheHelper()
        cache._memory_set("test-key", "test-value", ttl_seconds=0)
        time.sleep(0.01)
        result = cache._memory_get("test-key")
        assert result is None

    def test_memory_no_ttl(self):
        cache = CacheHelper()
        cache._memory_set("test-key", "test-value")
        result = cache._memory_get("test-key")
        assert result == "test-value"

    def test_memory_set_lru_eviction(self):
        cache = CacheHelper()
        cache._MEMORY_MAX_ENTRIES = 10
        # Fill beyond capacity
        for i in range(15):
            cache._memory_set(f"key-{i}", f"value-{i}")
        assert len(cache._memory_store) <= 10
        # Oldest keys should be evicted (at least key-0, key-1)
        assert cache._memory_get("key-0") is None
        # Newer keys should remain
        assert cache._memory_get("key-14") == "value-14"

    def test_memory_set_lru_eviction_updates_existing(self):
        cache = CacheHelper()
        cache._MEMORY_MAX_ENTRIES = 5
        for i in range(5):
            cache._memory_set(f"key-{i}", f"value-{i}")
        # Updating existing key should not trigger eviction
        cache._memory_set("key-0", "updated")
        for i in range(5):
            assert cache._memory_get(f"key-{i}") is not None
        assert len(cache._memory_store) == 5

    def test_memory_get_expired_removes_entry(self):
        cache = CacheHelper()
        cache._memory_set("exp-key", "val", ttl_seconds=0)
        time.sleep(0.01)
        result = cache._memory_get("exp-key")
        assert result is None
        assert cache._memory_get("exp-key") is None  # already removed


# ── Cache Helper Async Operations Tests ─────────────────────────────────────

class TestCacheHelperAsyncOps:
    """Tests for CacheHelper async operations."""

    @pytest.mark.asyncio
    async def test_get_json_memory(self):
        cache = CacheHelper()
        cache._memory_set("test-key", '{"name": "test"}')
        result = await cache.get_json("test-key")
        assert result == {"name": "test"}

    @pytest.mark.asyncio
    async def test_get_json_missing(self):
        cache = CacheHelper()
        result = await cache.get_json("missing-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_json_memory(self):
        cache = CacheHelper()
        await cache.set_json("test-key", {"name": "test"}, ttl_seconds=60)
        result = cache._memory_get("test-key")
        assert result is not None
        assert json.loads(result) == {"name": "test"}

    @pytest.mark.asyncio
    async def test_delete_memory(self):
        cache = CacheHelper()
        cache._memory_set("test-key", "test-value")
        await cache.delete("test-key")
        result = cache._memory_get("test-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_int_memory(self):
        cache = CacheHelper()
        cache._memory_set("counter", "42")
        result = await cache.get_int("counter")
        assert result == 42

    @pytest.mark.asyncio
    async def test_get_int_missing(self):
        cache = CacheHelper()
        result = await cache.get_int("missing-counter", default=10)
        assert result == 10

    @pytest.mark.asyncio
    async def test_get_int_invalid(self):
        cache = CacheHelper()
        cache._memory_set("counter", "not-a-number")
        result = await cache.get_int("counter", default=5)
        assert result == 5

    @pytest.mark.asyncio
    async def test_increment_memory(self):
        cache = CacheHelper()
        cache._memory_set("counter", "5")
        result = await cache.increment("counter")
        assert result == 6

    @pytest.mark.asyncio
    async def test_increment_missing(self):
        cache = CacheHelper()
        result = await cache.increment("new-counter")
        assert result == 1

    @pytest.mark.asyncio
    async def test_ping_memory(self):
        cache = CacheHelper()
        result = await cache.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_close_memory(self):
        cache = CacheHelper()
        await cache.close()


# ── Create Cache Factory Tests ──────────────────────────────────────────────

class TestCreateCache:
    """Tests for create_cache factory function."""

    def test_create_cache_without_url(self):
        cache = create_cache(None)
        assert cache._client is None
        assert cache.backend_name == "memory"

    def test_create_cache_with_empty_url(self):
        cache = create_cache("")
        assert cache._client is None
        assert cache.backend_name == "memory"


# ── Cache Helper Properties Tests ───────────────────────────────────────────

class TestCacheHelperProperties:
    """Tests for CacheHelper properties."""

    def test_enabled_always_true(self):
        cache = CacheHelper()
        assert cache.enabled is True

    def test_backend_name_memory(self):
        cache = CacheHelper()
        assert cache.backend_name == "memory"

    def test_backend_name_redis_healthy(self):
        mock_redis = MagicMock()
        cache = CacheHelper(client=mock_redis)
        assert cache.backend_name == "redis"

    def test_backend_name_redis_unhealthy(self):
        mock_redis = MagicMock()
        cache = CacheHelper(client=mock_redis)
        cache._redis_healthy = False
        assert cache.backend_name == "redis+memory"


# ── Cache Helper Bytes Handling Tests ───────────────────────────────────────

class TestCacheHelperBytesHandling:
    """Tests for CacheHelper bytes handling."""

    @pytest.mark.asyncio
    async def test_get_json_bytes_payload(self):
        cache = CacheHelper()
        cache._memory_set("test-key", b'{"name": "test"}')
        result = await cache.get_json("test-key")
        assert result == {"name": "test"}


# ── Cache Helper Redis Exception Handling Tests ────────────────────────────

class TestCacheHelperRedisExceptions:
    """Tests for CacheHelper when Redis operations raise exceptions."""

    @pytest.mark.asyncio
    async def test_get_json_redis_raises(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = ConnectionError("Redis down")
        cache = CacheHelper(client=mock_redis)
        # Should fall back to memory
        cache._memory_set("test-key", '{"fallback": true}')
        result = await cache.get_json("test-key")
        assert result == {"fallback": True}
        assert cache._redis_healthy is False

    @pytest.mark.asyncio
    async def test_get_json_redis_raises_no_memory(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = ConnectionError("Redis down")
        cache = CacheHelper(client=mock_redis)
        result = await cache.get_json("missing-key")
        assert result is None
        assert cache._redis_healthy is False

    @pytest.mark.asyncio
    async def test_set_json_redis_raises(self):
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = ConnectionError("Redis down")
        cache = CacheHelper(client=mock_redis)
        await cache.set_json("test-key", {"data": 123}, ttl_seconds=60)
        # Should still be in memory
        assert cache._memory_get("test-key") is not None
        assert cache._redis_healthy is False

    @pytest.mark.asyncio
    async def test_delete_redis_raises(self):
        mock_redis = AsyncMock()
        mock_redis.delete.side_effect = ConnectionError("Redis down")
        cache = CacheHelper(client=mock_redis)
        cache._memory_set("test-key", "val")
        await cache.delete("test-key")
        # Should be deleted from memory regardless
        assert cache._memory_get("test-key") is None
        assert cache._redis_healthy is False

    @pytest.mark.asyncio
    async def test_increment_redis_raises(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # ensure get_int falls to default 0
        mock_redis.incr.side_effect = ConnectionError("Redis down")
        cache = CacheHelper(client=mock_redis)
        result = await cache.increment("counter")
        # Should return the memory-based value (0 + 1)
        assert result == 1
        assert cache._redis_healthy is False

    @pytest.mark.asyncio
    async def test_get_int_redis_raises(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = ConnectionError("Redis down")
        cache = CacheHelper(client=mock_redis)
        cache._memory_set("num", "42")
        result = await cache.get_int("num")
        assert result == 42
        assert cache._redis_healthy is False

    @pytest.mark.asyncio
    async def test_ping_redis_raises(self):
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = ConnectionError("Redis down")
        cache = CacheHelper(client=mock_redis)
        result = await cache.ping()
        assert result is False
        assert cache._redis_healthy is False

    @pytest.mark.asyncio
    async def test_ping_redis_success(self):
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        cache = CacheHelper(client=mock_redis)
        cache._redis_healthy = False
        result = await cache.ping()
        assert result is True
        assert cache._redis_healthy is True

    @pytest.mark.asyncio
    async def test_close_redis_raises(self):
        mock_redis = AsyncMock()
        mock_redis.aclose.side_effect = ConnectionError("Redis down")
        cache = CacheHelper(client=mock_redis)
        await cache.close()
        # Should not raise

    @pytest.mark.asyncio
    async def test_close_redis_success(self):
        mock_redis = AsyncMock()
        cache = CacheHelper(client=mock_redis)
        await cache.close()
        mock_redis.aclose.assert_called_once()
        assert cache._redis_healthy is False


# ── Cache Helper Stale-While-Revalidate Tests ──────────────────────────────

class TestCacheHelperStale:
    """Tests for get_json_stale stale-while-revalidate flow."""

    @pytest.mark.asyncio
    async def test_get_json_stale_missing(self):
        cache = CacheHelper()
        result = await cache.get_json_stale("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_json_stale_expired_but_within_max_age(self):
        cache = CacheHelper()
        cache._memory_set("stale-key", '{"stale": true}', ttl_seconds=0)
        time.sleep(0.01)
        result = await cache.get_json_stale("stale-key", max_age_seconds=3600)
        assert result == {"stale": True}

    @pytest.mark.asyncio
    async def test_get_json_stale_beyond_max_age(self):
        cache = CacheHelper()
        cache._memory_set("old-key", '{"old": true}')
        # Patch created_at to be very old
        cache._memory_store["old-key"] = (
            None,
            time.monotonic() - 99999,
            '{"old": true}',
        )
        result = await cache.get_json_stale("old-key", max_age_seconds=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_json_stale_from_redis(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b'{"from_redis": true}'
        cache = CacheHelper(client=mock_redis)
        result = await cache.get_json_stale("redis-key")
        assert result == {"from_redis": True}

    @pytest.mark.asyncio
    async def test_get_json_stale_redis_raises_fallback_memory(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = ConnectionError("Redis down")
        cache = CacheHelper(client=mock_redis)
        cache._memory_set("fallback", '{"mem": true}')
        result = await cache.get_json_stale("fallback")
        assert result == {"mem": True}


# ── Cache Helper Redis Integration Tests ────────────────────────────────────

class TestCacheHelperRedis:
    """Tests for CacheHelper with a mocked Redis client."""

    @pytest.mark.asyncio
    async def test_get_json_from_redis(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b'{"cached": true}'
        cache = CacheHelper(client=mock_redis)
        result = await cache.get_json("redis-key")
        assert result == {"cached": True}
        assert cache._redis_healthy is True

    @pytest.mark.asyncio
    async def test_set_json_to_redis(self):
        mock_redis = AsyncMock()
        cache = CacheHelper(client=mock_redis)
        await cache.set_json("key", {"val": 1}, ttl_seconds=30)
        mock_redis.setex.assert_called_once()
        assert cache._redis_healthy is True

    @pytest.mark.asyncio
    async def test_delete_from_redis(self):
        mock_redis = AsyncMock()
        cache = CacheHelper(client=mock_redis)
        await cache.delete("some-key")
        mock_redis.delete.assert_called_once_with("some-key")

    @pytest.mark.asyncio
    async def test_increment_on_redis(self):
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 5
        cache = CacheHelper(client=mock_redis)
        result = await cache.increment("visits")
        assert result == 5
        mock_redis.incr.assert_called_once_with("visits")

    @pytest.mark.asyncio
    async def test_get_int_from_redis(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b"99"
        cache = CacheHelper(client=mock_redis)
        result = await cache.get_int("score")
        assert result == 99
