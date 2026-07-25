# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import pytest

from memory.redis_memory import ConversationMemoryStore


class FakeRedisClient:
    def __init__(self):
        self._store = {}
        self._ttls = {}
        self._healthy = True

    async def rpush(self, key, value):
        self._store.setdefault(key, []).append(value)

    async def lrange(self, key, start, end):
        items = self._store.get(key, [])
        if end == -1:
            return items[start:]
        return items[start : end + 1]

    async def expire(self, key, ttl):
        self._ttls[key] = ttl

    async def delete(self, key):
        self._store.pop(key, None)
        self._ttls.pop(key, None)

    async def ping(self):
        return self._healthy

    async def aclose(self):
        pass


@pytest.fixture
def memory_store():
    return ConversationMemoryStore(redis_url=None, session_ttl_seconds=86400)


@pytest.fixture
def memory_store_with_redis():
    store = ConversationMemoryStore(redis_url=None, session_ttl_seconds=3600)
    store._client = FakeRedisClient()
    store._redis_healthy = True
    return store


@pytest.mark.asyncio
async def test_append_message(memory_store):
    result = await memory_store.append_message(
        "session-1", "user", "Hello, world!", metadata={"intent": "general"}
    )

    assert result["role"] == "user"
    assert result["content"] == "Hello, world!"
    assert result["metadata"]["intent"] == "general"
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_retrieve_history(memory_store):
    await memory_store.append_message("session-1", "user", "Message 1")
    await memory_store.append_message("session-1", "assistant", "Response 1")
    await memory_store.append_message("session-1", "user", "Message 2")

    history = await memory_store.get_history("session-1")

    assert len(history) == 3
    assert history[0]["content"] == "Message 1"
    assert history[-1]["content"] == "Message 2"


@pytest.mark.asyncio
async def test_history_limit(memory_store):
    for i in range(25):
        await memory_store.append_message("session-1", "user", f"Message {i}")

    history = await memory_store.get_history("session-1", limit=5)

    assert len(history) == 5
    assert history[0]["content"] == "Message 20"


@pytest.mark.asyncio
async def test_session_ttl(memory_store_with_redis):
    await memory_store_with_redis.append_message("ttl-session", "user", "Test message")

    assert memory_store_with_redis._client._ttls.get("chat:session:ttl-session") == 3600


@pytest.mark.asyncio
async def test_clear_session(memory_store):
    await memory_store.append_message("session-1", "user", "Message 1")
    await memory_store.clear_session("session-1")

    history = await memory_store.get_history("session-1")
    assert history == []


@pytest.mark.asyncio
async def test_clear_nonexistent_session(memory_store):
    await memory_store.clear_session("nonexistent-session")
    history = await memory_store.get_history("nonexistent-session")
    assert history == []


@pytest.mark.asyncio
async def test_ping_memory_backend(memory_store):
    result = await memory_store.ping()
    assert result is True


@pytest.mark.asyncio
async def test_ping_redis_backend(memory_store_with_redis):
    result = await memory_store_with_redis.ping()
    assert result is True


@pytest.mark.asyncio
async def test_backend_name_memory(memory_store):
    assert memory_store.backend_name == "memory"


@pytest.mark.asyncio
async def test_backend_name_redis(memory_store_with_redis):
    assert "redis" in memory_store_with_redis.backend_name


@pytest.mark.asyncio
async def test_session_isolation(memory_store):
    await memory_store.append_message("session-a", "user", "Hello A")
    await memory_store.append_message("session-b", "user", "Hello B")

    history_a = await memory_store.get_history("session-a")
    history_b = await memory_store.get_history("session-b")

    assert any("Hello A" in h["content"] for h in history_a)
    assert any("Hello B" in h["content"] for h in history_b)
    assert not any("Hello B" in h["content"] for h in history_a)


@pytest.mark.asyncio
async def test_redis_fallback_to_memory(memory_store_with_redis):
    memory_store_with_redis._client._healthy = False

    await memory_store_with_redis.append_message("fallback-session", "user", "Fallback test")

    history = await memory_store_with_redis.get_history("fallback-session")
    assert len(history) >= 1
    assert history[-1]["content"] == "Fallback test"


@pytest.mark.asyncio
async def test_close_memory_store(memory_store):
    await memory_store.close()
    result = await memory_store.ping()
    assert result is True


@pytest.mark.asyncio
async def test_redis_key_format(memory_store_with_redis):
    await memory_store_with_redis.append_message("key-test", "user", "Test")

    assert "chat:session:key-test" in memory_store_with_redis._client._store
