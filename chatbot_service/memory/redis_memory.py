# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
import logging
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

# S21/C13: Cap in-memory fallback to avoid unbounded growth when Redis is down.
_MAX_IN_MEMORY_SESSIONS = 500


class ConversationMemoryStore:
    def __init__(self, redis_url: str | None, *, session_ttl_seconds: int = 86400) -> None:
        self._client = Redis.from_url(redis_url, encoding='utf-8', decode_responses=True) if redis_url else None
        # Use OrderedDict so we can evict the oldest session (LRU-lite) when the cap is hit
        self._memory: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
        self._redis_healthy = self._client is not None
        self._session_ttl_seconds = session_ttl_seconds

    @property
    def backend_name(self) -> str:
        if self._client is None:
            return 'memory'
        return 'redis' if self._redis_healthy else 'redis+memory'

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str | list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            'role': role,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        # LRU-lite: move touched session to end; evict oldest if cap exceeded
        if session_id in self._memory:
            self._memory.move_to_end(session_id)
        self._memory.setdefault(session_id, []).append(payload)
        while len(self._memory) > _MAX_IN_MEMORY_SESSIONS:
            self._memory.popitem(last=False)  # evict the oldest session
        if self._client is not None:
            try:
                await self._client.rpush(self._key(session_id), json.dumps(payload))
                await self._client.expire(self._key(session_id), self._session_ttl_seconds)
                self._redis_healthy = True
            except (RedisError, OSError) as exc:
                logger.warning("Redis append_message failed: %s", exc)
                self._redis_healthy = False
        return payload

    async def get_history(self, session_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        if self._client is not None:
            try:
                items = await self._client.lrange(self._key(session_id), -limit, -1)
                self._redis_healthy = True
                if items:
                    return [json.loads(item) for item in items]
            except (RedisError, json.JSONDecodeError, OSError) as exc:
                logger.warning("Redis get_history failed: %s", exc)
                self._redis_healthy = False
        history = self._memory.get(session_id, [])
        return history[-limit:]

    async def clear_session(self, session_id: str) -> None:
        self._memory.pop(session_id, None)
        if self._client is not None:
            try:
                await self._client.delete(self._key(session_id))
                self._redis_healthy = True
            except (RedisError, OSError) as exc:
                logger.warning("Redis clear_session failed: %s", exc)
                self._redis_healthy = False

    async def ping(self) -> bool:
        if self._client is None:
            return True  # in-memory fallback is always available
        try:
            await self._client.ping()
            self._redis_healthy = True
            return True
        except (RedisError, OSError) as exc:
            logger.warning("Redis ping failed: %s", exc)
            self._redis_healthy = False
            return False  # Redis is genuinely unreachable

    async def close(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.aclose()
            self._redis_healthy = False
        except (RedisError, OSError) as exc:
            logger.warning("Redis close failed: %s", exc)
            return

    @staticmethod
    def _key(session_id: str) -> str:
        return f'chat:session:{session_id}'
