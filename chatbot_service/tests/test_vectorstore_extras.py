# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag.document_loader import LoadedDocument
from rag.vectorstore import DocumentChunk, LocalVectorStore


class TestLocalVectorStoreEnsureIndexExtras:
    @pytest.mark.asyncio
    async def test_ensure_index_empty_db_calls_build_index(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # count is 0
        mock_conn.fetchval.return_value = 0
        store._pool = mock_pool

        store.build_index = AsyncMock(return_value=[])

        result = await store.ensure_index()
        store.build_index.assert_called_once_with(force=True)


class TestLocalVectorStoreBuildIndexExtras:
    @pytest.mark.asyncio
    async def test_build_index_no_force_returns_cached(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        cached = [DocumentChunk('a', 's', 't', 'c', 'x')]
        store._chunks = cached

        result = await store.build_index(force=False)
        assert result is cached


class TestLocalVectorStoreSearchExtras:
    @pytest.mark.asyncio
    async def test_search_exception_returns_empty_list(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Raise exception on fetch
        mock_conn.fetch.side_effect = RuntimeError("Database error")
        store._pool = mock_pool

        results = await store.search("query text")
        assert results == []


class TestLocalVectorStoreStatsExtras:
    @pytest.mark.asyncio
    async def test_stats_exception_returns_zeros(self):
        store = LocalVectorStore(
            database_url='postgresql://user:pass@localhost:5432/db',
            data_dir=Path('/fake/data'),
            embedding_model='hash'
        )
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mock_conn.fetchval.side_effect = RuntimeError("Database error")
        store._pool = mock_pool

        stats = await store.stats()
        assert stats["chunks"] == 0
        assert stats["categories"] == 0
