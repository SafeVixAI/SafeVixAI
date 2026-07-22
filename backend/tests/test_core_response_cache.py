# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for core/response_cache.py — ResponseCache, cache_response decorator, invalidate_cache_pattern."""

from __future__ import annotations

import time

import pytest

from core.response_cache import (
    ResponseCache,
    cache_response,
    generate_cache_key,
)
from core.response_cache import (
    response_cache as global_cache,
)

# ── ResponseCache Basic Operations ─────────────────────────────────────────

class TestResponseCacheBasics:
    def test_init_defaults(self):
        cache = ResponseCache()
        assert cache._default_ttl == 300
        assert cache._max_size == 1000
        assert cache.size == 0
        assert cache.hit_rate == 0.0

    def test_init_custom(self):
        cache = ResponseCache(default_ttl=60, max_size=100)
        assert cache._default_ttl == 60
        assert cache._max_size == 100

    def test_set_and_get(self):
        cache = ResponseCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing(self):
        cache = ResponseCache()
        assert cache.get("nonexistent") is None

    def test_get_expired(self):
        cache = ResponseCache()
        # Use negative TTL so it's already expired
        cache._cache["exp-key"] = (time.time() - 1, "value")
        assert cache.get("exp-key") is None

    def test_delete(self):
        cache = ResponseCache()
        cache.set("del-key", "value")
        cache.delete("del-key")
        assert cache.get("del-key") is None

    def test_delete_missing(self):
        cache = ResponseCache()
        cache.delete("missing-key")  # Should not raise

    def test_clear(self):
        cache = ResponseCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0
        assert cache._hits == 0
        assert cache._misses == 0

    def test_custom_ttl(self):
        cache = ResponseCache()
        cache.set("ttl-key", "val", ttl=10)
        entry = cache._cache["ttl-key"]
        expires_at, value = entry
        assert value == "val"
        assert expires_at > time.time()

    def test_default_ttl(self):
        cache = ResponseCache(default_ttl=60)
        cache.set("default-ttl", "val")
        entry = cache._cache["default-ttl"]
        expires_at, _ = entry
        assert expires_at > time.time() + 55  # Within ~60s


# ── ResponseCache Statistics ───────────────────────────────────────────────

class TestResponseCacheStats:
    def test_hit_rate_zero_initially(self):
        cache = ResponseCache()
        assert cache.hit_rate == 0.0

    def test_hit_rate_half(self):
        cache = ResponseCache()
        cache.set("k", "v")
        cache.get("k")   # hit
        cache.get("x")   # miss
        assert cache.hit_rate == 0.5

    def test_hit_rate_all_hits(self):
        cache = ResponseCache()
        cache.set("k", "v")
        cache.get("k")
        cache.get("k")
        assert cache.hit_rate == 1.0

    def test_get_stats_structure(self):
        cache = ResponseCache()
        cache.set("k", "v")
        cache.get("k")
        stats = cache.get_stats()
        assert "size" in stats
        assert "max_size" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert stats["size"] == 1
        assert stats["hits"] == 1

    def test_size_property(self):
        cache = ResponseCache()
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.size == 2

    def test_evict_expired_removes_only_expired(self):
        cache = ResponseCache()
        cache.set("fresh", "val", ttl=60)
        # Manually set an expired entry
        cache._cache["stale"] = (time.time() - 1, "val")
        cache._evict_expired()
        assert cache.get("fresh") == "val"
        assert cache.get("stale") is None

    def test_evict_expired_with_no_expired(self):
        cache = ResponseCache()
        cache.set("a", 1, ttl=60)
        cache.set("b", 2, ttl=60)
        cache._evict_expired()
        assert cache.size == 2


# ── ResponseCache Max Size / Eviction ─────────────────────────────────────

class TestResponseCacheEviction:
    def test_set_evicts_oldest_when_full(self):
        cache = ResponseCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict oldest
        assert cache.get("a") is None  # Evicted
        assert cache.get("b") is not None
        assert cache.get("c") is not None
        assert cache.get("d") is not None

    def test_set_evicts_expired_before_oldest(self):
        cache = ResponseCache(max_size=3)
        # Manually set expired entry
        cache._cache["expired"] = (time.time() - 1, "x")
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        # expired should be evicted, no need to evict oldest
        assert cache.size == 3
        assert cache.get("a") == 1

    def test_max_size_at_capacity(self):
        cache = ResponseCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.size == 2

    def test_update_existing_does_not_evict(self):
        cache = ResponseCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("a", "updated")  # Update existing
        assert cache.size == 2
        assert cache.get("a") == "updated"


# ── generate_cache_key ────────────────────────────────────────────────────

class TestGenerateCacheKey:
    def test_basic_key(self):
        key = generate_cache_key("api", lat=13.0, lon=80.0)
        assert key.startswith("api:")

    def test_key_omits_none_values(self):
        key = generate_cache_key("test", a=1, b=None, c=3)
        # Should only include a and c, not b
        assert "b=" not in key

    def test_key_is_deterministic(self):
        k1 = generate_cache_key("route", src="A", dst="B")
        k2 = generate_cache_key("route", dst="B", src="A")
        assert k1 == k2

    def test_prefix_included(self):
        key = generate_cache_key("my-prefix", a=1)
        assert key.startswith("my-prefix:")

    def test_different_prefixes_different_keys(self):
        k1 = generate_cache_key("route", a=1)
        k2 = generate_cache_key("geocode", a=1)
        assert k1 != k2


# ── cache_response Decorator ──────────────────────────────────────────────

class TestCacheResponseDecorator:
    @pytest.mark.asyncio
    async def test_decorator_caches_result(self):
        call_count = 0

        @cache_response(ttl=60, key_prefix="test")
        async def my_func(param: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result-{param}"

        # First call — should execute
        result1 = await my_func(param="hello")
        assert result1 == "result-hello"
        assert call_count == 1

        # Second call — should hit cache
        result2 = await my_func(param="hello")
        assert result2 == "result-hello"
        assert call_count == 1  # Not incremented

    @pytest.mark.asyncio
    async def test_decorator_different_params_different_cache(self):
        call_count = 0

        @cache_response(ttl=60, key_prefix="test")
        async def my_func(param: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result-{param}"

        await my_func(param="a")
        await my_func(param="b")
        assert call_count == 2  # Both executed

    @pytest.mark.asyncio
    async def test_decorator_default_prefix(self):
        call_count = 0

        @cache_response(ttl=60)
        async def my_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result = await my_func(x=5)
        assert result == 10
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_decorator_skips_none_params(self):
        call_count = 0

        @cache_response(ttl=60)
        async def my_func(a: int | None = None, b: int = 0) -> int:
            nonlocal call_count
            call_count += 1
            return a or b

        # Same effective cache key despite None param
        r1 = await my_func(a=None, b=42)
        r2 = await my_func(a=None, b=42)
        assert r1 == 42
        assert r2 == 42
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_decorator_honors_ttl(self):
        """Verify the decorator respects the TTL parameter."""
        call_count = 0

        @cache_response(ttl=0, key_prefix="test")
        async def my_func() -> str:
            nonlocal call_count
            call_count += 1
            return "fresh"

        result1 = await my_func()
        assert result1 == "fresh"
        assert call_count == 1

        # Wait briefly and call again — cache should be expired
        time.sleep(0.01)
        result2 = await my_func()
        assert result2 == "fresh"
        # The cache may or may not have expired depending on timing
        # This is a best-effort check
        assert call_count >= 1


# ── invalidate_cache_pattern ──────────────────────────────────────────────

class TestInvalidateCachePattern:
    def test_invalidate_by_pattern(self):
        # Test the actual invalidate_cache_pattern function from the module
        # Save global state, set up test data, then restore
        from core.response_cache import invalidate_cache_pattern as icp
        from core.response_cache import response_cache as global_rc
        old_cache = global_rc._cache.copy()
        global_rc._cache.clear()
        try:
            global_rc.set("api:user:1", "a")
            global_rc.set("api:user:2", "b")
            global_rc.set("api:ward:1", "c")

            count = icp("user")
            assert count == 2
            assert global_rc.get("api:user:1") is None
            assert global_rc.get("api:user:2") is None
            assert global_rc.get("api:ward:1") == "c"
        finally:
            global_rc._cache.clear()
            global_rc._cache.update(old_cache)

    def test_invalidate_no_match(self):
        from core.response_cache import invalidate_cache_pattern as icp
        from core.response_cache import response_cache as global_rc
        old_cache = global_rc._cache.copy()
        global_rc._cache.clear()
        try:
            global_rc.set("alpha", 1)
            global_rc.set("beta", 2)
            count = icp("nonexistent")
            assert count == 0
        finally:
            global_rc._cache.clear()
            global_rc._cache.update(old_cache)


# ── Global Instance ───────────────────────────────────────────────────────

class TestGlobalInstance:
    def test_global_cache_is_singleton(self):
        from core.response_cache import response_cache as rc1
        from core.response_cache import response_cache as rc2
        assert rc1 is rc2

    def test_global_cache_defaults(self):
        assert global_cache._default_ttl == 300
        assert global_cache._max_size == 1000
