# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""C9: LLM response cache with Redis backend.

Caches identical queries to avoid redundant LLM API calls.
Uses SHA-256 hash of (message + intent + tool_summaries) as cache key.
TTL defaults to 1 hour for fresh responses.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

_DEFAULT_TTL_SECONDS = 3600  # 1 hour


import asyncpg
from rag.embeddings import build_embedding_function

@dataclass(slots=True)
class CacheEntry:
    text: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponseCache:
    def __init__(
        self,
        redis_url: str | None,
        database_url: str | None = None,
        *,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        similarity_threshold: float = 0.95,
        embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2',
        embedding_dim: int = 384,
    ) -> None:
        self._client = Redis.from_url(redis_url, encoding='utf-8', decode_responses=True) if redis_url else None
        self.database_url = database_url
        self._pool: asyncpg.Pool | None = None
        self._ttl_seconds = ttl_seconds
        self.similarity_threshold = similarity_threshold
        self._healthy = self._client is not None
        self._embedding_function = build_embedding_function(embedding_model) if database_url else None
        self.embedding_dim = embedding_dim

    async def _get_pool(self) -> asyncpg.Pool | None:
        if not self.database_url:
            return None
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.database_url)
            async with self._pool.acquire() as conn:
                await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
                await conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS llm_semantic_cache (
                        hash_key TEXT PRIMARY KEY,
                        message TEXT,
                        intent TEXT,
                        tools TEXT,
                        response_data JSONB,
                        embedding vector({self.embedding_dim}),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # Index for cosine similarity (vector_cosine_ops) -> 1 - cosine_distance
                await conn.execute(f'''
                    CREATE INDEX IF NOT EXISTS llm_semantic_cache_emb_idx
                    ON llm_semantic_cache USING hnsw (embedding vector_cosine_ops)
                ''')
        return self._pool

    @property
    def backend_name(self) -> str:
        if self.database_url and self._healthy:
            return 'pgvector+redis'
        elif self._healthy:
            return 'redis'
        return 'memory'

    def _make_key(self, message: str, intent: str, tool_summaries: list[str]) -> str:
        """Create a deterministic cache key for exact matches."""
        payload = json.dumps({
            'message': message,
            'intent': intent,
            'tools': tool_summaries[:4],
        }, sort_keys=True)
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return f'cache:llm:{digest}'

    async def get(self, message: str, intent: str, tool_summaries: list[str]) -> CacheEntry | None:
        # 1. Try Exact match via Redis
        if self._client:
            try:
                key = self._make_key(message, intent, tool_summaries)
                raw = await self._client.get(key)
                if raw:
                    data = json.loads(raw)
                    self._healthy = True
                    return CacheEntry(**data)
            except (RedisError, json.JSONDecodeError, OSError) as exc:
                logger.warning("LLM cache Exact GET failed: %s", exc)
                self._healthy = False

        # 2. Try Semantic match via pgvector
        pool = await self._get_pool()
        if pool and self._embedding_function:
            try:
                emb = self._embedding_function([message])[0]
                emb_str = f"[{','.join(str(x) for x in emb)}]"
                tools_str = json.dumps(tool_summaries[:4], sort_keys=True)
                
                async with pool.acquire() as conn:
                    # Using cosine similarity (<=> is cosine distance in pgvector)
                    # Similarity = 1 - (<=>)
                    row = await conn.fetchrow('''
                        SELECT response_data, 1.0 - (embedding <=> $1::vector) as similarity
                        FROM llm_semantic_cache
                        WHERE intent = $2 AND tools = $3
                        ORDER BY embedding <=> $1::vector
                        LIMIT 1
                    ''', emb_str, intent, tools_str)
                    
                    if row and row['similarity'] >= self.similarity_threshold:
                        logger.info("Semantic cache hit! Similarity: %.3f", row['similarity'])
                        data = json.loads(row['response_data'])
                        return CacheEntry(**data)
            except Exception as exc:
                logger.warning("LLM semantic cache GET failed: %s", exc)

        return None

    async def set(
        self,
        message: str,
        intent: str,
        tool_summaries: list[str],
        entry: CacheEntry,
    ) -> None:
        # 1. Store Exact match in Redis
        if self._client:
            try:
                key = self._make_key(message, intent, tool_summaries)
                await self._client.setex(key, self._ttl_seconds, json.dumps(asdict(entry)))
                self._healthy = True
            except (RedisError, OSError) as exc:
                logger.warning("LLM cache Exact SET failed: %s", exc)
                self._healthy = False

        # 2. Store Semantic match in pgvector
        pool = await self._get_pool()
        if pool and self._embedding_function:
            try:
                key = self._make_key(message, intent, tool_summaries) # Use exact hash as primary key
                emb = self._embedding_function([message])[0]
                emb_str = f"[{','.join(str(x) for x in emb)}]"
                tools_str = json.dumps(tool_summaries[:4], sort_keys=True)
                
                async with pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO llm_semantic_cache (hash_key, message, intent, tools, response_data, embedding)
                        VALUES ($1, $2, $3, $4, $5, $6::vector)
                        ON CONFLICT (hash_key) DO UPDATE SET
                            response_data = EXCLUDED.response_data,
                            created_at = CURRENT_TIMESTAMP
                    ''', key, message, intent, tools_str, json.dumps(asdict(entry)), emb_str)
            except Exception as exc:
                logger.warning("LLM semantic cache SET failed: %s", exc)

    async def ping(self) -> bool:
        if not self._client:
            return False
        try:
            await self._client.ping()
            self._healthy = True
            return True
        except (RedisError, OSError) as exc:
            logger.warning("LLM cache PING failed: %s", exc)
            self._healthy = False
            return False

    async def get_provider_unavailable_until(self, provider_name: str) -> float | None:
        if not self._client:
            return None
        try:
            val = await self._client.get(f"circuit:unavailable:{provider_name}")
            return float(val) if val else None
        except Exception as exc:
            logger.warning("Failed to get provider availability from Redis: %s", exc)
            return None

    async def set_provider_unavailable_until(self, provider_name: str, until: float, ttl_seconds: int) -> None:
        if not self._client:
            return
        try:
            await self._client.setex(f"circuit:unavailable:{provider_name}", ttl_seconds, str(until))
        except Exception as exc:
            logger.warning("Failed to set provider availability in Redis: %s", exc)

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.aclose()
            except (RedisError, OSError) as exc:
                logger.warning("LLM cache CLOSE failed: %s", exc)
