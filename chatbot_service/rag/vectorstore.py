# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

import asyncpg

from rag.document_loader import LoadedDocument, load_documents
from rag.embeddings import build_embedding_function, normalize_text

logger = logging.getLogger(__name__)

EXCLUDED_INDEX_CATEGORIES = {
    'qa_pairs',
    'pothole_training',
    'speech_finetuning',
}


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    source: str
    title: str
    category: str
    content: str


class LocalVectorStore:
    def __init__(
        self,
        database_url: str,
        data_dir: Path,
        *,
        collection_name: str = 'safevixai_rag',
        embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2',
        embedding_dim: int = 384,
    ) -> None:
        self.database_url = database_url
        self.data_dir = data_dir
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self._embedding_function = build_embedding_function(embedding_model)
        self._pool: asyncpg.Pool | None = None
        self._chunks: list[DocumentChunk] = []

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.database_url)
        return self._pool

    async def init_db(self) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            await conn.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.collection_name} (
                    chunk_id TEXT PRIMARY KEY,
                    source TEXT,
                    title TEXT,
                    category TEXT,
                    content TEXT,
                    embedding vector({self.embedding_dim})
                )
            ''')
            # Create HNSW index for L2 distance (tuned: m=32, ef_construction=200)
            await conn.execute(f'''
                CREATE INDEX IF NOT EXISTS {self.collection_name}_embedding_idx
                ON {self.collection_name} USING hnsw (embedding vector_l2_ops)
                WITH (m = 32, ef_construction = 200)
            ''')

    async def ensure_index(self) -> list[DocumentChunk]:
        if self._chunks:
            return self._chunks

        await self.init_db()
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            count = await conn.fetchval(f'SELECT COUNT(*) FROM {self.collection_name}')

            if count > 0:
                rows = await conn.fetch(f'SELECT chunk_id, source, title, category, content FROM {self.collection_name}')
                self._chunks = [DocumentChunk(**dict(row)) for row in rows]
                return self._chunks

        return await self.build_index(force=True)

    async def build_index(self, *, force: bool = False) -> list[DocumentChunk]:
        if self._chunks and not force:
            return self._chunks

        await self.init_db()

        documents = load_documents(self.data_dir)
        chunks: list[DocumentChunk] = []
        for document in documents:
            chunks.extend(self._chunk_document(document))

        self._chunks = self._filter_chunks(chunks)
        await self._upsert_pg(self._chunks)
        return self._chunks

    @staticmethod
    def _filter_chunks(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        return [chunk for chunk in chunks if chunk.category not in EXCLUDED_INDEX_CATEGORIES]

    async def _upsert_pg(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            return

        pool = await self._get_pool()

        # We need to compute embeddings for all chunks before inserting
        contents = [chunk.content for chunk in chunks]
        try:
            embeddings = await asyncio.to_thread(self._embedding_function, contents)
        except Exception as exc:
            logger.warning('Failed to generate embeddings: %s', exc)
            return

        async with pool.acquire() as conn, conn.transaction():
            for chunk, embedding in zip(chunks, embeddings, strict=False):
                emb_str = f"[{','.join(str(x) for x in embedding)}]"
                await conn.execute(
                    f'''
                    INSERT INTO {self.collection_name} (chunk_id, source, title, category, content, embedding)
                    VALUES ($1, $2, $3, $4, $5, $6::vector)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        source = EXCLUDED.source,
                            title = EXCLUDED.title,
                            category = EXCLUDED.category,
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding
                        ''',
                        chunk.chunk_id, chunk.source, chunk.title, chunk.category, chunk.content, emb_str
                    )

    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        scopes: set[str] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        pool = await self._get_pool()

        try:
            query_results = await asyncio.to_thread(self._embedding_function, [query])
            query_embedding = query_results[0]
            emb_str = f"[{','.join(str(x) for x in query_embedding)}]"
        except Exception as exc:
            logger.warning('Failed to generate query embedding: %s', exc)
            return []

        async with pool.acquire() as conn:
            where_clause = ""
            args = [emb_str, top_k]
            if scopes:
                # Format scopes for SQL IN clause
                placeholders = ', '.join(f'${i+3}' for i in range(len(scopes)))
                where_clause = f"WHERE category IN ({placeholders})"
                args.extend(list(scopes))

            try:
                # Set ef_search for HNSW recall (200 = best balance for legal RAG)
                await conn.execute('SET hnsw.ef_search = 200')
                # Using L2 distance (<->) for similarity scoring
                query_sql = f'''
                    SELECT chunk_id, source, title, category, content,
                            1.0 / (1.0 + (embedding <-> $1::vector)) as score
                    FROM {self.collection_name}
                    {where_clause}
                    ORDER BY embedding <-> $1::vector
                    LIMIT $2
                '''
                rows = await conn.fetch(query_sql, *args)

                matches = []
                for row in rows:
                    if row['category'] in EXCLUDED_INDEX_CATEGORIES:
                        continue
                    chunk = DocumentChunk(
                        chunk_id=row['chunk_id'],
                        source=row['source'],
                        title=row['title'],
                        category=row['category'],
                        content=row['content']
                    )
                    matches.append((chunk, float(row['score'])))
                return matches
            except Exception as exc:
                logger.warning('pgvector query failed: %s', exc)
                return []

    async def stats(self) -> dict[str, int | str]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM {self.collection_name}')
                categories = await conn.fetchval(f'SELECT COUNT(DISTINCT category) FROM {self.collection_name}')
            except Exception as exc:
                logger.warning('Unable to count pgvector chunks: %s', exc)
                count = 0
                categories = 0

        return {
            'chunks': count,
            'categories': categories,
            'embedding_model': self.embedding_model,
            'database': 'pgvector'
        }

    @staticmethod
    def _chunk_document(document: LoadedDocument) -> list[DocumentChunk]:
        paragraphs = [normalize_text(item) for item in document.text.split('\n') if normalize_text(item)]
        if not paragraphs:
            paragraphs = [document.text]
        chunks: list[DocumentChunk] = []
        current: list[str] = []
        current_length = 0
        chunk_index = 1
        for paragraph in paragraphs:
            if current and current_length + len(paragraph) > 900:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f'{document.source}:{chunk_index}',
                        source=document.source,
                        title=document.title,
                        category=document.category,
                        content='\n'.join(current),
                    )
                )
                chunk_index += 1
                current = []
                current_length = 0
            current.append(paragraph)
            current_length += len(paragraph)
        if current:  # pragma: no branch
            chunks.append(
                DocumentChunk(
                    chunk_id=f'{document.source}:{chunk_index}',
                    source=document.source,
                    title=document.title,
                    category=document.category,
                    content='\n'.join(current),
                )
            )
        return chunks
