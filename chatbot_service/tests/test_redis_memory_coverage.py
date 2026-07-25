# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import pytest
from redis.exceptions import RedisError

from memory.redis_memory import _MAX_IN_MEMORY_SESSIONS, ConversationMemoryStore


class FakeRedisClient:
    def __init__(self, *, fail_on=None):
        self._store = {}
        self._ttls = {}
        self._healthy = True
        self._fail_on = fail_on or []
        self._closed = False

    async def rpush(self, key, value):
        if "rpush" in self._fail_on:
            raise RedisError("rpush failed")
        self._store.setdefault(key, []).append(value)

    async def lrange(self, key, start, end):
        if "lrange" in self._fail_on:
            raise RedisError("lrange failed")
        items = self._store.get(key, [])
        if end == -1:
            return items[start:]
        return items[start: end + 1]

    async def expire(self, key, ttl):
        if "expire" in self._fail_on:
            raise OSError("expire failed")
        self._ttls[key] = ttl

    async def delete(self, key):
        if "delete" in self._fail_on:
            raise RedisError("delete failed")
        self._store.pop(key, None)
        self._ttls.pop(key, None)

    async def ping(self):
        if "ping" in self._fail_on:
            raise OSError("ping failed")
        return self._healthy

    async def aclose(self):
        if "aclose" in self._fail_on:
            raise RedisError("aclose failed")
        self._closed = True


class TestInMemoryOnly:
    @pytest.fixture
    def store(self):
        return ConversationMemoryStore(redis_url=None, session_ttl_seconds=86400)

    @pytest.mark.asyncio
    async def test_backend_name(self, store):
        assert store.backend_name == "memory"

    @pytest.mark.asyncio
    async def test_append_get_clear(self, store):
        await store.append_message("s1", "user", "hello")
        history = await store.get_history("s1")
        assert len(history) == 1
        assert history[0]["content"] == "hello"

        await store.clear_session("s1")
        history = await store.get_history("s1")
        assert history == []

    @pytest.mark.asyncio
    async def test_ping(self, store):
        assert await store.ping() is True

    @pytest.mark.asyncio
    async def test_close_no_client(self, store):
        await store.close()
        assert store._client is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self, store):
        for i in range(_MAX_IN_MEMORY_SESSIONS + 10):
            await store.append_message(f"s{i}", "user", f"msg{i}")
        assert len(store._memory) <= _MAX_IN_MEMORY_SESSIONS
        assert "s0" not in store._memory


class TestRedisHealthy:
    @pytest.fixture
    def store(self):
        store = ConversationMemoryStore(redis_url=None, session_ttl_seconds=3600)
        store._client = FakeRedisClient()
        store._redis_healthy = True
        return store

    @pytest.mark.asyncio
    async def test_append_get_clear_with_redis(self, store):
        await store.append_message("s1", "user", "hello", metadata={"key": "val"})
        assert "chat:session:s1" in store._client._store

        history = await store.get_history("s1")
        assert len(history) == 1
        assert history[0]["content"] == "hello"
        assert history[0]["metadata"]["key"] == "val"

        await store.clear_session("s1")
        assert "chat:session:s1" not in store._client._store

    @pytest.mark.asyncio
    async def test_session_ttl_set_on_append(self, store):
        await store.append_message("ttl-s", "user", "test")
        assert store._client._ttls.get("chat:session:ttl-s") == 3600

    @pytest.mark.asyncio
    async def test_lru_eviction_with_redis(self, store):
        for i in range(_MAX_IN_MEMORY_SESSIONS + 5):
            await store.append_message(f"s{i}", "user", f"msg{i}")
        assert len(store._memory) <= _MAX_IN_MEMORY_SESSIONS

    @pytest.mark.asyncio
    async def test_ping_returns_true(self, store):
        assert await store.ping() is True
        assert store._redis_healthy is True

    @pytest.mark.asyncio
    async def test_close_success(self, store):
        await store.close()
        assert store._client._closed
        assert store._redis_healthy is False

    @pytest.mark.asyncio
    async def test_backend_name_redis(self, store):
        assert store.backend_name == "redis"


class TestRedisFailure:
    @pytest.mark.asyncio
    async def test_append_message_failure_falls_back_to_memory(self):
        store = ConversationMemoryStore(redis_url=None)
        store._client = FakeRedisClient(fail_on=["rpush"])
        store._redis_healthy = True

        result = await store.append_message("s1", "user", "fallback test")
        assert result["content"] == "fallback test"
        assert store._redis_healthy is False

        history = await store.get_history("s1")
        assert len(history) == 1
        assert history[0]["content"] == "fallback test"

    @pytest.mark.asyncio
    async def test_append_message_oserror_fallback(self):
        store = ConversationMemoryStore(redis_url=None)
        store._client = FakeRedisClient(fail_on=["expire"])
        store._redis_healthy = True

        result = await store.append_message("s1", "user", "oserror test")
        assert result["content"] == "oserror test"
        assert store._redis_healthy is False

    @pytest.mark.asyncio
    async def test_get_history_failure_falls_back_to_memory(self):
        store = ConversationMemoryStore(redis_url=None)
        store._client = FakeRedisClient(fail_on=["lrange"])
        store._redis_healthy = True

        # First ensure there's data in memory
        await store.append_message("s1", "user", "mem data")
        store._redis_healthy = False
        store._redis_healthy = True

        history = await store.get_history("s1")
        assert len(history) == 1
        assert history[0]["content"] == "mem data"
        assert store._redis_healthy is False

    @pytest.mark.asyncio
    async def test_clear_session_failure_falls_back(self):
        store = ConversationMemoryStore(redis_url=None)
        store._client = FakeRedisClient(fail_on=["delete", "lrange"])
        store._redis_healthy = True

        await store.append_message("s1", "user", "data")
        store._redis_healthy = True

        await store.clear_session("s1")
        assert store._redis_healthy is False

        history = await store.get_history("s1")
        assert history == []  # memory cleared, redis fallback also fails

    @pytest.mark.asyncio
    async def test_ping_failure_returns_false(self):
        store = ConversationMemoryStore(redis_url=None)
        store._client = FakeRedisClient(fail_on=["ping"])
        store._redis_healthy = True

        result = await store.ping()
        assert result is False
        assert store._redis_healthy is False

    @pytest.mark.asyncio
    async def test_close_failure_handled_gracefully(self):
        store = ConversationMemoryStore(redis_url=None)
        store._client = FakeRedisClient(fail_on=["aclose"])
        store._redis_healthy = True

        await store.close()

    @pytest.mark.asyncio
    async def test_backend_name_redis_plus_memory(self):
        store = ConversationMemoryStore(redis_url=None)
        store._client = FakeRedisClient(fail_on=["ping"])
        store._redis_healthy = False
        assert store.backend_name == "redis+memory"


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_history_returns_empty_for_nonexistent_session(self):
        store = ConversationMemoryStore(redis_url=None)
        history = await store.get_history("nonexistent")
        assert history == []

    @pytest.mark.asyncio
    async def test_clear_nonexistent_no_error(self):
        store = ConversationMemoryStore(redis_url=None)
        await store.clear_session("nonexistent")

    @pytest.mark.asyncio
    async def test_append_moves_session_to_end(self):
        store = ConversationMemoryStore(redis_url=None)
        await store.append_message("s1", "user", "first")
        await store.append_message("s2", "user", "second")
        await store.append_message("s1", "user", "third")

        keys = list(store._memory.keys())
        assert keys[-1] == "s1"

    @pytest.mark.asyncio
    async def test_history_respects_limit(self):
        store = ConversationMemoryStore(redis_url=None)
        for i in range(10):
            await store.append_message("s1", "user", f"msg{i}")
        history = await store.get_history("s1", limit=3)
        assert len(history) == 3
        assert history[0]["content"] == "msg7"
        assert history[-1]["content"] == "msg9"

    @pytest.mark.asyncio
    async def test_redis_get_history_empty_returns_memory_fallback(self):
        """When redis returns empty list, should fall back to memory."""
        store = ConversationMemoryStore(redis_url=None)
        store._client = FakeRedisClient(fail_on=[])
        store._redis_healthy = True

        await store.append_message("s1", "user", "mem only")
        history = await store.get_history("s1")
        assert len(history) == 1
