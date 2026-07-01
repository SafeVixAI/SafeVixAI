# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import logging
import time
import uuid
from typing import AsyncGenerator

from core.redis_client import create_cache, CacheHelper

logger = logging.getLogger(__name__)

# Fallback in-memory locks when Redis is unavailable
_memory_locks: dict[str, asyncio.Lock] = {}


class Redlock:
    """Distributed lock implementation using Redis (Redlock algorithm concept)
    with a graceful in-memory asyncio.Lock fallback when Redis is unavailable.
    """

    def __init__(self, name: str, ttl_seconds: int = 10, cache: CacheHelper | None = None) -> None:
        self.name = f"lock:{name}"
        self.ttl_seconds = ttl_seconds
        self.cache = cache or create_cache()
        self.lock_value = str(uuid.uuid4())
        self._has_lock = False

    async def acquire(self) -> bool:
        if self.cache._client:
            try:
                # Use Redis SETNX with EX (set if not exists with TTL)
                result = await self.cache._client.set(
                    self.name, self.lock_value, ex=self.ttl_seconds, nx=True
                )
                if result:
                    self._has_lock = True
                    return True
                return False
            except Exception as e:
                logger.warning("Redis lock acquire failed, falling back to in-memory: %s", e)

        # Fallback to in-memory lock
        if self.name not in _memory_locks:
            _memory_locks[self.name] = asyncio.Lock()
        lock = _memory_locks[self.name]
        try:
            await asyncio.wait_for(lock.acquire(), timeout=0.1)
            self._has_lock = True
            return True
        except asyncio.TimeoutError:
            return False

    async def release(self) -> None:
        if not self._has_lock:
            return

        if self.cache._client:
            try:
                # Lua script to release lock only if value matches
                lua_script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    return redis.call("del", KEYS[1])
                else
                    return 0
                end
                """
                await self.cache._client.eval(lua_script, 1, self.name, self.lock_value)
                self._has_lock = False
                return
            except Exception as e:
                logger.warning("Redis lock release failed, checking in-memory: %s", e)

        if self.name in _memory_locks:
            try:
                _memory_locks[self.name].release()
            except RuntimeError:
                pass
        self._has_lock = False


@asynccontextmanager
async def distributed_lock(
    name: str, ttl_seconds: int = 10, cache: CacheHelper | None = None
) -> AsyncGenerator[bool, None]:
    """Async context manager for acquiring a distributed lock."""
    lock = Redlock(name, ttl_seconds=ttl_seconds, cache=cache)
    acquired = await lock.acquire()
    try:
        yield acquired
    finally:
        if acquired:
            await lock.release()
