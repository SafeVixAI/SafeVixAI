# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import collections.abc
import hashlib
import json
import logging
import os
from dataclasses import dataclass

from redis.asyncio import Redis
from redis.exceptions import RedisError

from core.metrics import chatbot_rag_cache_hit, chatbot_rag_cache_miss
from rag.bm25 import BM25
from rag.vectorstore import DocumentChunk, LocalVectorStore

logger = logging.getLogger(__name__)

_RAG_CACHE_TTL = 300  # 5 minutes

@dataclass(slots=True)
class RetrievalResult:
    source: str
    title: str
    category: str
    content: str
    score: float


class Retriever:
    def __init__(
        self,
        vectorstore: LocalVectorStore,
        *,
        default_top_k: int = 5,
        min_score: float | None = None,
        cross_encoder_model: str | None = None,
        redis_url: str | None = None,
        hyde_generate_fn: collections.abc.Callable[[str], str] | None = None,
    ) -> None:
        self.vectorstore = vectorstore
        self.default_top_k = default_top_k
        self.min_score = min_score if min_score is not None else float(os.getenv('RAG_MIN_SCORE', '0.55'))
        self.cross_encoder_model = cross_encoder_model
        self.hyde_generate_fn = hyde_generate_fn
        self._bm25 = None
        self._bm25_chunk_len = 0
        self._bm25_chunks: list[DocumentChunk] = []
        self._redis: Redis | None = Redis.from_url(redis_url, decode_responses=True) if redis_url else None

    def _get_bm25(self, chunks: list[DocumentChunk]) -> BM25:
        if self._bm25 is None or len(chunks) != self._bm25_chunk_len:
            self._bm25 = BM25([chunk.content for chunk in chunks])
            self._bm25_chunk_len = len(chunks)
            self._bm25_chunks = chunks
        return self._bm25

    def _make_cache_key(self, query: str, scopes: set[str] | None) -> str:
        """Deterministic cache key for RAG retrieval results."""
        scope_str = ",".join(sorted(scopes or []))
        payload = json.dumps({"q": query.strip().lower(), "s": scope_str}, sort_keys=True)
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return f"rag:retrieve:{digest}"

    async def _cache_get(self, query: str, scopes: set[str] | None) -> list[RetrievalResult] | None:
        """Try to fetch cached RAG results from Redis."""
        if not self._redis:
            return None
        try:
            key = self._make_cache_key(query, scopes)
            raw = await self._redis.get(key)
            if raw:
                data = json.loads(raw)
                results = [RetrievalResult(**item) for item in data]
                chatbot_rag_cache_hit.inc()
                logger.debug("RAG cache hit for query=%.40s", query)
                return results
        except (RedisError, json.JSONDecodeError, OSError) as exc:
            logger.debug("RAG cache get failed: %s", exc)
        return None

    async def _cache_set(
        self,
        query: str,
        scopes: set[str] | None,
        results: list[RetrievalResult],
    ) -> None:
        """Store RAG results in Redis cache."""
        if not self._redis or not results:
            return
        try:
            key = self._make_cache_key(query, scopes)
            raw = json.dumps(
                [{"source": r.source, "title": r.title, "category": r.category,
                  "content": r.content, "score": r.score} for r in results]
            )
            await self._redis.setex(key, _RAG_CACHE_TTL, raw)
        except (RedisError, OSError) as exc:
            logger.debug("RAG cache set failed: %s", exc)

    def _generate_hypothetical_document(self, query: str) -> str:
        if self.hyde_generate_fn is not None:
            try:
                return self.hyde_generate_fn(query)
            except Exception as exc:
                logger.debug("HyDE generation failed, falling back to raw query: %s", exc)
        return query

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        scopes: set[str] | None = None,
    ) -> list[RetrievalResult]:
        if not query.strip():
            return []

        # Try cache first
        cached = await self._cache_get(query, scopes)
        if cached is not None:
            return cached

        chatbot_rag_cache_miss.inc()
        k = top_k or self.default_top_k
        # 0. HyDE — generate hypothetical document for better dense retrieval
        hyde_query = self._generate_hypothetical_document(query)
        # 1. Dense retrieval (using HyDE query if available, else original)
        dense_matches = await self.vectorstore.search(hyde_query, top_k=k * 2, scopes=scopes)

        # 2. Sparse (BM25) retrieval
        chunks = await self.vectorstore.ensure_index()
        if scopes:
            chunks = [c for c in chunks if c.category in scopes]

        sparse_matches = []
        if chunks:
            bm25 = self._get_bm25(chunks)
            scores = bm25.get_scores(query)
            sparse_matches = list(zip(chunks, scores, strict=False))
            sparse_matches.sort(key=lambda x: x[1], reverse=True)
            sparse_matches = sparse_matches[:k * 2]

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_k = 60
        fused_scores = {}
        chunk_map = {}

        for rank, (chunk, _score) in enumerate(dense_matches):
            if chunk.chunk_id not in fused_scores:
                fused_scores[chunk.chunk_id] = 0.0
                chunk_map[chunk.chunk_id] = chunk
            fused_scores[chunk.chunk_id] += 1.0 / (rrf_k + rank + 1)

        for rank, (chunk, _score) in enumerate(sparse_matches):
            if chunk.chunk_id not in fused_scores:
                fused_scores[chunk.chunk_id] = 0.0
                chunk_map[chunk.chunk_id] = chunk
            fused_scores[chunk.chunk_id] += 1.0 / (rrf_k + rank + 1)

        fused_results = [(chunk_map[cid], score) for cid, score in fused_scores.items()]
        fused_results.sort(key=lambda x: x[1], reverse=True)

        results = [
            RetrievalResult(
                source=chunk.source,
                title=chunk.title,
                category=chunk.category,
                content=chunk.content,
                score=score,
            )
            for chunk, score in fused_results[:k]
        ]

        # 4. Cross-Encoder Reranking (if enabled)
        if self.cross_encoder_model and len(results) > 1:
            try:
                from sentence_transformers import CrossEncoder
                if not hasattr(self, '_cross_encoder'):  # pragma: no branch
                    self._cross_encoder = CrossEncoder(self.cross_encoder_model)
                pairs = [[query, res.content] for res in results]
                rerank_scores = self._cross_encoder.predict(pairs)
                for res, r_score in zip(results, rerank_scores, strict=False):
                    res.score = float(r_score)
                results.sort(key=lambda x: x.score, reverse=True)
            except Exception as exc:
                logging.getLogger(__name__).warning("Cross-Encoder reranking failed: %s", exc)

        results = [res for res in results if res.score >= self.min_score]

        # Store in cache for future lookups
        await self._cache_set(query, scopes, results)
        return results
