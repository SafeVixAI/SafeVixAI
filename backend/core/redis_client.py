# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import collections
import json
import time
import uuid
import warnings
from typing import Any

from redis.asyncio import Redis


# Max age for stale cache entries (24 hours) — served when live data unavailable
STALE_CACHE_MAX_AGE_SECONDS = 86400


# Shared Redis connection pool (avoids per-request TCP connection overhead)
_redis_pool: redis.asyncio.ConnectionPool | None = None
_redis_pool_url: str | None = None


def get_redis_client(
    redis_url: str | None,
    *,
    tls_enabled: bool = False,
    password: str | None = None,
) -> Redis:
    """Return a Redis client backed by a shared connection pool.

    Reuses a single ConnectionPool across all callers, avoiding the
    overhead of opening/closing a TCP socket per request.
    """
    global _redis_pool, _redis_pool_url
    if not redis_url:
        return None  # type: ignore[return-value]
    if _redis_pool is None or redis_url != _redis_pool_url:
        if _redis_pool is not None:
            try:
                import asyncio
                asyncio.ensure_future(_redis_pool.aclose())
            except Exception:
                pass
        _redis_pool_url = redis_url
        url = redis_url
        if tls_enabled and url.startswith("redis://"):
            url = url.replace("redis://", "rediss://", 1)
        _redis_pool = redis.asyncio.ConnectionPool.from_url(
            url,
            max_connections=20,
            pool_timeout=5,
            retry_on_timeout=True,
            password=password,
            ssl=tls_enabled or None,
        )
    return Redis(connection_pool=_redis_pool)


async def close_redis_pool() -> None:
    """Close the shared Redis connection pool (called during app shutdown)."""
    global _redis_pool, _redis_pool_url
    if _redis_pool is not None:
        try:
            await _redis_pool.aclose()
        except Exception:
            pass
        _redis_pool = None
        _redis_pool_url = None


class CacheHelper:
    # Max in-memory cache entries before eviction (prevents OOM when Redis is down)
    _MEMORY_MAX_ENTRIES = 1000

    def __init__(self, client: Redis | None = None) -> None:
        self._client = client
        self._memory_store: dict[str, tuple[float | None, float | None, str]] = {}
        self._memory_keys: list[str] = []
        self._redis_healthy = client is not None

    @property
    def enabled(self) -> bool:
        return True

    @property
    def backend_name(self) -> str:
        if self._client is None:
            return 'memory'
        return 'redis' if self._redis_healthy else 'redis+memory'

    def _memory_get(self, key: str) -> str | None:
        entry = self._memory_store.get(key)
        if entry is None:
            return None
        expires_at, _created_at, payload = entry
        if expires_at is not None and expires_at <= time.monotonic():
            self._memory_store.pop(key, None)
            return None
        return payload

    def _memory_set(self, key: str, payload: str, ttl_seconds: int | None = None) -> None:
        # Evict oldest entries when store exceeds max capacity
        if len(self._memory_store) >= self._MEMORY_MAX_ENTRIES and key not in self._memory_store:
            evict_count = max(1, self._MEMORY_MAX_ENTRIES // 10)
            for _ in range(evict_count):
                if self._memory_keys:
                    oldest = self._memory_keys.pop(0)
                    self._memory_store.pop(oldest, None)
        expires_at = None if ttl_seconds is None else time.monotonic() + ttl_seconds
        created_at = time.monotonic()
        self._memory_store[key] = (expires_at, created_at, payload)
        if key not in self._memory_keys:
            self._memory_keys.append(key)

    def _memory_delete(self, key: str) -> None:
        self._memory_store.pop(key, None)

    async def get_json(self, key: str) -> Any | None:
        payload = None
        if self._client:
            try:
                payload = await self._client.get(key)
                self._redis_healthy = True
            except Exception:
                self._redis_healthy = False
                payload = None
        if payload is None:
            payload = self._memory_get(key)
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')
        return json.loads(payload)

    async def get_json_with_stampede_protection(
        self,
        key: str,
        recompute: collections.abc.Callable[[], collections.abc.Awaitable[Any]],
        ttl_seconds: int,
        *,
        mutex_timeout: float = 1.0,
        stale_ttl: int | None = None,
    ) -> Any:
        """Get cached JSON value with stampede protection via Redis mutex.

        On cache miss, acquires a distributed lock to prevent multiple concurrent
        recomputations. Supports stale-while-revalidate when ``stale_ttl`` is set.

        TTL strategy: wall-clock from time.monotonic() for stale detection
        (get_json_stale), Redis EXPIRE/PEXPIRE for cache expiry. The two are
        independent — Redis expiry evicts old keys, monotonic clock detects
        staleness without worrying about clock drift. The mutex lock TTL is
        generous (2x mutex_timeout) to avoid premature lock release during
        recomputation.
        """
        result = await self.get_json(key)
        if result is not None:
            return result

        if stale_ttl is not None:
            stale = await self.get_json_stale(key, max_age_seconds=stale_ttl)
            if stale is not None:
                return stale

        lock_key = f"{key}:lock"
        lock_value = str(uuid.uuid4())
        acquired = False
        try:
            if self._client:
                try:
                    acquired = await self._client.set(lock_key, lock_value, nx=True, ex=int(mutex_timeout * 2))
                    self._redis_healthy = True
                except Exception:
                    self._redis_healthy = False

            if not acquired:
                await asyncio.sleep(0.05)
                retry = await self.get_json(key)
                if retry is not None:
                    return retry
                if stale_ttl is not None:
                    return await self.get_json_stale(key, max_age_seconds=stale_ttl)
                return None

            value = await recompute()
            await self.set_json(key, value, ttl_seconds)
            return value
        finally:
            if acquired and self._client:
                try:
                    await self._client.delete(lock_key)
                except Exception:
                    pass

    async def get_json_stale(self, key: str, max_age_seconds: int = STALE_CACHE_MAX_AGE_SECONDS) -> Any | None:
        """Get cached value even if expired (stale-while-revalidate).
        Returns None if no cache entry exists at all, or if the entry
        is older than max_age_seconds.
        """
        payload = None
        if self._client:
            try:
                payload = await self._client.get(key)
                if payload is None:
                    # Redis auto-deletes expired keys, so stale only from memory
                    pass
                self._redis_healthy = True
            except Exception:
                self._redis_healthy = False
                payload = None
        if payload is None:
            payload = self._memory_get_stale(key, max_age_seconds)
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')
        return json.loads(payload)

    def _memory_get_stale(self, key: str, max_age_seconds: int = STALE_CACHE_MAX_AGE_SECONDS) -> str | None:
        """Like _memory_get but ignores TTL, enforces max_age_seconds instead."""
        entry = self._memory_store.get(key)
        if entry is None:
            return None
        _expires_at, created_at, payload = entry
        if created_at is not None and (time.monotonic() - created_at) > max_age_seconds:
            self._memory_store.pop(key, None)
            return None
        return payload

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        payload = json.dumps(value, default=str)
        self._memory_set(key, payload, ttl_seconds)
        if not self._client:
            return
        try:
            await self._client.setex(key, ttl_seconds, payload)
            self._redis_healthy = True
        except Exception:
            self._redis_healthy = False
            return

    async def delete(self, key: str) -> None:
        self._memory_delete(key)
        if not self._client:
            return
        try:
            await self._client.delete(key)
            self._redis_healthy = True
        except Exception:
            self._redis_healthy = False
            return

    async def increment(self, key: str) -> int | None:
        current = await self.get_int(key, default=0) + 1
        self._memory_set(key, str(current))
        if not self._client:
            return current
        try:
            current = int(await self._client.incr(key))
            self._redis_healthy = True
            self._memory_set(key, str(current))
            return current
        except Exception:
            self._redis_healthy = False
            return current

    async def get_int(self, key: str, default: int = 0) -> int:
        value = None
        if self._client:
            try:
                value = await self._client.get(key)
                self._redis_healthy = True
            except Exception:
                self._redis_healthy = False
                value = None
        if value is None:
            value = self._memory_get(key)
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    async def ping(self) -> bool:
        if not self._client:
            return True
        try:
            await self._client.ping()
            self._redis_healthy = True
            return True
        except Exception:
            self._redis_healthy = False
            return False

    async def hset(self, key: str, mapping: dict[str, Any]) -> None:
        """Set fields in a Redis hash. Gracefully degrades to memory if Redis is unavailable."""
        payloads = {k: json.dumps(v, default=str) for k, v in mapping.items()}
        # Memory fallback: store the entire hash as a JSON string under the key
        current = await self.hgetall(key) or {}
        current.update(mapping)
        self._memory_set(key, json.dumps(current, default=str))
        
        if not self._client:
            return
        try:
            await self._client.hset(key, mapping=payloads)
            self._redis_healthy = True
        except Exception:
            self._redis_healthy = False
            return
            
    async def hgetall(self, key: str) -> dict[str, Any]:
        """Get all fields from a Redis hash."""
        if self._client:
            try:
                raw = await self._client.hgetall(key)
                self._redis_healthy = True
                if raw:
                    return {k: json.loads(v) for k, v in raw.items()}
            except Exception:
                self._redis_healthy = False
        
        # Memory fallback
        payload = self._memory_get(key)
        if payload:
            try:
                return json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    async def hdel(self, key: str, *fields: str) -> None:
        """Delete fields from a Redis hash."""
        current = await self.hgetall(key)
        if current:
            for field in fields:
                current.pop(field, None)
            self._memory_set(key, json.dumps(current, default=str))

        if not self._client:
            return
        try:
            if fields:
                await self._client.hdel(key, *fields)
            self._redis_healthy = True
        except Exception:
            self._redis_healthy = False
            return

    async def close(self) -> None:
        if not self._client:
            return
        try:
            await self._client.aclose()
            self._redis_healthy = False
        except Exception:
            return


def create_cache(
    redis_url: str | None = None,
    *,
    tls_enabled: bool = False,
    password: str | None = None,
) -> CacheHelper:
    if not redis_url:
        return CacheHelper()
    client = get_redis_client(redis_url, tls_enabled=tls_enabled, password=password)
    if client is None:
        return CacheHelper()
    return CacheHelper(client)
