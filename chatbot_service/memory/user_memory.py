# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""User preference store backed by Redis.

Stores structured user metadata (language, vehicle type, default location, etc.)
that persists across sessions and is used by TieredMemory to personalise responses.
"""

from __future__ import annotations

import json
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

_USER_PREFS_TTL = 86400 * 30  # 30 days


class UserPreferenceStore:
    """Redis-backed user preference store.

    Each user's preferences are stored in a Redis hash under ``user:prefs:{user_id}``.
    Accepts either a ``redis_url`` string or an existing ``Redis`` client instance.
    """

    def __init__(self, redis_url: str | None = None, redis_client: Redis | None = None) -> None:
        if redis_client is not None:
            self._redis = redis_client
        elif redis_url:
            self._redis = Redis.from_url(redis_url, encoding='utf-8', decode_responses=True)
        else:
            self._redis = None

    def _prefs_key(self, user_id: str) -> str:
        return f"user:prefs:{user_id}"

    async def get_preference(self, user_id: str, key: str, default: object = None) -> object:
        """Get a single preference value for a user."""
        if not self._redis:
            return default
        try:
            raw = await self._redis.hget(self._prefs_key(user_id), key)
            if raw is None:
                return default
            return json.loads(raw) if isinstance(raw, str) else raw
        except (RedisError, json.JSONDecodeError, OSError) as exc:
            logger.debug("Failed to get user pref %s for %s: %s", key, user_id, exc)
            return default

    async def set_preference(self, user_id: str, key: str, value: object) -> bool:
        """Set a single preference value for a user."""
        if not self._redis:
            return False
        try:
            pk = self._prefs_key(user_id)
            serialised = json.dumps(value) if not isinstance(value, (str, bytes)) else value
            await self._redis.hset(pk, key, serialised)
            await self._redis.expire(pk, _USER_PREFS_TTL)
            return True
        except (RedisError, OSError) as exc:
            logger.debug("Failed to set user pref %s for %s: %s", key, user_id, exc)
            return False

    async def get_all_preferences(self, user_id: str) -> dict[str, object]:
        """Return all stored preferences for a user as a flat dict."""
        if not self._redis:
            return {}
        try:
            raw = await self._redis.hgetall(self._prefs_key(user_id))
            result: dict[str, object] = {}
            for k, v in raw.items():
                try:
                    result[k] = json.loads(v) if isinstance(v, str) else v
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            return result
        except (RedisError, OSError) as exc:
            logger.debug("Failed to get all prefs for %s: %s", user_id, exc)
            return {}

    async def set_multiple(self, user_id: str, prefs: dict[str, object]) -> int:
        """Set multiple preferences atomically. Returns number of keys set."""
        if not self._redis or not prefs:
            return 0
        try:
            pk = self._prefs_key(user_id)
            mapping = {}
            for k, v in prefs.items():
                mapping[k] = json.dumps(v) if not isinstance(v, (str, bytes)) else v
            await self._redis.hset(pk, mapping=mapping)  # type: ignore[arg-type]
            await self._redis.expire(pk, _USER_PREFS_TTL)
            return len(mapping)
        except (RedisError, OSError) as exc:
            logger.debug("Failed to set multiple prefs for %s: %s", user_id, exc)
            return 0

    async def delete_preference(self, user_id: str, key: str) -> bool:
        """Delete a single preference."""
        if not self._redis:
            return False
        try:
            await self._redis.hdel(self._prefs_key(user_id), key)
            return True
        except (RedisError, OSError) as exc:
            logger.debug("Failed to delete pref %s for %s: %s", key, user_id, exc)
            return False

    async def delete_all(self, user_id: str) -> bool:
        """Delete all preferences for a user."""
        if not self._redis:
            return False
        try:
            await self._redis.delete(self._prefs_key(user_id))
            return True
        except (RedisError, OSError) as exc:
            logger.debug("Failed to delete all prefs for %s: %s", user_id, exc)
            return False

    async def ping(self) -> bool:
        if not self._redis:
            return False
        try:
            await self._redis.ping()
            return True
        except (RedisError, OSError):
            return False

    async def close(self) -> None:
        if self._redis:
            try:
                await self._redis.aclose()
            except (RedisError, OSError) as exc:
                logger.debug("UserPreferenceStore close error: %s", exc)
