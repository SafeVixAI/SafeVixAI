# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cache.llm_cache import CacheEntry, LLMResponseCache


class TestCacheEntry:
    def test_cache_entry_defaults(self):
        entry = CacheEntry(text="hello", provider="groq", model="mixtral")
        assert entry.text == "hello"
        assert entry.provider == "groq"
        assert entry.model == "mixtral"
        assert entry.prompt_tokens == 0
        assert entry.completion_tokens == 0
        assert entry.total_tokens == 0

    def test_cache_entry_full(self):
        entry = CacheEntry(text="hello", provider="groq", model="mixtral",
                           prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert entry.total_tokens == 30


class TestLLMResponseCache:
    def test_init_no_redis_no_db(self):
        cache = LLMResponseCache(redis_url=None)
        assert cache._client is None
        assert cache._healthy is False
        assert cache._pool is None
        assert cache._embedding_function is None
        assert cache._ttl_seconds == 3600
        assert cache.similarity_threshold == 0.95

    def test_init_with_redis_url(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        assert cache._client is not None
        assert cache._healthy is True

    def test_backend_name_no_redis(self):
        cache = LLMResponseCache(redis_url=None)
        assert cache.backend_name == "memory"

    def test_backend_name_redis_only(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        assert cache.backend_name == "redis"

    def test_backend_name_redis_unhealthy(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._healthy = False
        assert cache.backend_name == "memory"

    def test_backend_name_pgvector_and_redis(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0",
                                 database_url="postgresql://localhost:5432/test")
        assert cache.backend_name == "pgvector+redis"

    def test_make_key_deterministic(self):
        cache = LLMResponseCache(redis_url=None)
        key1 = cache._make_key("hello", "general", ["tool1", "tool2"])
        key2 = cache._make_key("hello", "general", ["tool1", "tool2"])
        assert key1 == key2
        assert key1.startswith("cache:llm:")

    def test_make_key_different_inputs(self):
        cache = LLMResponseCache(redis_url=None)
        key1 = cache._make_key("hello", "general", [])
        key2 = cache._make_key("world", "general", [])
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_get_no_client(self):
        cache = LLMResponseCache(redis_url=None)
        result = await cache.get("hello", "general", [])
        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_hit(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        entry_data = {"text": "cached", "provider": "groq", "model": "mixtral",
                       "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        cache._client.get = AsyncMock(return_value=json.dumps(entry_data))
        result = await cache.get("hello", "general", [])
        assert result is not None
        assert result.text == "cached"
        assert result.provider == "groq"
        assert cache._healthy is True

    @pytest.mark.asyncio
    async def test_get_redis_miss(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.get = AsyncMock(return_value=None)
        result = await cache.get("hello", "general", [])
        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_error(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.get = AsyncMock(side_effect=ConnectionError("redis down"))
        result = await cache.get("hello", "general", [])
        assert result is None
        assert cache._healthy is False

    @pytest.mark.asyncio
    async def test_ping_no_client(self):
        cache = LLMResponseCache(redis_url=None)
        result = await cache.ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_ping_success(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.ping = AsyncMock(return_value=True)
        result = await cache.ping()
        assert result is True
        assert cache._healthy is True

    @pytest.mark.asyncio
    async def test_ping_failure(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.ping = AsyncMock(side_effect=ConnectionError("down"))
        result = await cache.ping()
        assert result is False
        assert cache._healthy is False

    @pytest.mark.asyncio
    async def test_set_no_client(self):
        cache = LLMResponseCache(redis_url=None)
        entry = CacheEntry(text="hello", provider="groq", model="mixtral")
        # Should not raise
        await cache.set("hello", "general", [], entry)

    @pytest.mark.asyncio
    async def test_set_redis(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.setex = AsyncMock()
        entry = CacheEntry(text="hello", provider="groq", model="mixtral",
                           prompt_tokens=5, completion_tokens=10, total_tokens=15)
        await cache.set("hello", "general", [], entry)
        cache._client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_provider_unavailable_until_no_client(self):
        cache = LLMResponseCache(redis_url=None)
        result = await cache.get_provider_unavailable_until("groq")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_provider_unavailable_until_hit(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.get = AsyncMock(return_value="1234567890.0")
        result = await cache.get_provider_unavailable_until("groq")
        assert result == 1234567890.0

    @pytest.mark.asyncio
    async def test_get_provider_unavailable_until_miss(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.get = AsyncMock(return_value=None)
        result = await cache.get_provider_unavailable_until("groq")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_provider_unavailable_until_error(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.get = AsyncMock(side_effect=RuntimeError("fail"))
        result = await cache.get_provider_unavailable_until("groq")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_provider_unavailable_until_no_client(self):
        cache = LLMResponseCache(redis_url=None)
        await cache.set_provider_unavailable_until("groq", 1234567890.0, 3600)

    @pytest.mark.asyncio
    async def test_set_provider_unavailable_until_success(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.setex = AsyncMock()
        await cache.set_provider_unavailable_until("groq", 1234567890.0, 3600)
        cache._client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_provider_unavailable_until_error(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.setex = AsyncMock(side_effect=RuntimeError("fail"))
        await cache.set_provider_unavailable_until("groq", 1234567890.0, 3600)
        cache._client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_client(self):
        cache = LLMResponseCache(redis_url=None)
        await cache.close()

    @pytest.mark.asyncio
    async def test_close_success(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.aclose = AsyncMock()
        await cache.close()
        cache._client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_error(self):
        cache = LLMResponseCache(redis_url="redis://localhost:6379/0")
        cache._client.aclose = AsyncMock(side_effect=ConnectionError("fail"))
        await cache.close()
        cache._client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pool_no_db_url(self):
        cache = LLMResponseCache(redis_url=None)
        pool = await cache._get_pool()
        assert pool is None

    @pytest.mark.asyncio
    async def test_get_pool_called_twice_reuses(self):
        with patch("cache.llm_cache.asyncpg.create_pool", new_callable=AsyncMock) as mock_create:
            mock_pool = MagicMock()
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            # acquire must be a regular callable that returns an async context manager
            mock_acquire_cm = MagicMock()
            mock_acquire_cm.__aenter__.return_value = mock_conn
            mock_acquire_cm.__aexit__.return_value = None
            mock_pool.acquire.return_value = mock_acquire_cm
            mock_create.return_value = mock_pool
            cache = LLMResponseCache(redis_url=None, database_url="postgresql://localhost:5432/test")
            pool1 = await cache._get_pool()
            pool2 = await cache._get_pool()
            assert pool1 is pool2
            mock_create.assert_called_once()
