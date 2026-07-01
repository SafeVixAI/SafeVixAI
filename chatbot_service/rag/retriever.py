# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import os
from dataclasses import dataclass

from rag.bm25 import BM25
from rag.vectorstore import LocalVectorStore, DocumentChunk

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
    ) -> None:
        self.vectorstore = vectorstore
        self.default_top_k = default_top_k
        self.min_score = min_score if min_score is not None else float(os.getenv('RAG_MIN_SCORE', '0.55'))
        self.cross_encoder_model = cross_encoder_model
        self._bm25 = None
        self._bm25_chunk_len = 0
        self._bm25_chunks: list[DocumentChunk] = []

    def _get_bm25(self, chunks: list[DocumentChunk]) -> BM25:
        if self._bm25 is None or len(chunks) != self._bm25_chunk_len:
            self._bm25 = BM25([chunk.content for chunk in chunks])
            self._bm25_chunk_len = len(chunks)
            self._bm25_chunks = chunks
        return self._bm25

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        scopes: set[str] | None = None,
    ) -> list[RetrievalResult]:
        if not query.strip():
            return []
            
        k = top_k or self.default_top_k
        # 1. Dense retrieval
        dense_matches = await self.vectorstore.search(query, top_k=k * 2, scopes=scopes)
        
        # 2. Sparse (BM25) retrieval
        chunks = await self.vectorstore.ensure_index()
        if scopes:
            chunks = [c for c in chunks if c.category in scopes]
            
        sparse_matches = []
        if chunks:
            bm25 = self._get_bm25(chunks)
            scores = bm25.get_scores(query)
            sparse_matches = list(zip(chunks, scores))
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
                if not hasattr(self, '_cross_encoder'):
                    self._cross_encoder = CrossEncoder(self.cross_encoder_model)
                pairs = [[query, res.content] for res in results]
                rerank_scores = self._cross_encoder.predict(pairs)
                for res, r_score in zip(results, rerank_scores):
                    res.score = float(r_score)
                results.sort(key=lambda x: x.score, reverse=True)
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning("Cross-Encoder reranking failed: %s", exc)
                
        results = [res for res in results if res.score >= self.min_score]
        return results
