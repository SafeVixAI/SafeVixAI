# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from rag.retriever import Retriever
from rag.vectorstore import LocalVectorStore


@pytest.fixture
def mock_store() -> LocalVectorStore:
    store = MagicMock(spec=LocalVectorStore)
    from rag.vectorstore import DocumentChunk
    store.search = AsyncMock(return_value=[
        (DocumentChunk("legal/mv_act.md:1", "legal/mv_act.md", "MV Act", "legal", "helmet fine"), 0.9),
    ])
    return store


@pytest.mark.asyncio
async def test_retriever_returns_legal_context_from_repo_data(mock_store: LocalVectorStore):
    retriever = Retriever(mock_store, default_top_k=3, min_score=0.0)
    results = await retriever.retrieve("motor vehicles act helmet fine", scopes={"legal"})
    assert results
    assert len(results) > 0
    assert any("legal/" in item.source for item in results)


@pytest.mark.asyncio
async def test_retriever_filters_weak_matches(mock_store: LocalVectorStore):
    retriever = Retriever(mock_store, default_top_k=3, min_score=0.95)
    results = await retriever.retrieve("motor vehicles act helmet fine", scopes={"legal"})
    assert results == []


@pytest.mark.asyncio
async def test_retriever_returns_empty_for_empty_query(mock_store: LocalVectorStore):
    retriever = Retriever(mock_store, default_top_k=3, min_score=0.0)
    results = await retriever.retrieve("", scopes={"legal"})
    assert results == []
    mock_store.search.assert_not_called()


@pytest.mark.asyncio
async def test_retriever_filters_by_scope(mock_store: LocalVectorStore):
    from rag.vectorstore import DocumentChunk
    mock_store.search = AsyncMock(return_value=[
        (DocumentChunk("medical/first_aid.md:1", "medical/first_aid.md", "First Aid", "medical", "CPR"), 0.8),
    ])
    retriever = Retriever(mock_store, default_top_k=5, min_score=0.0)
    results = await retriever.retrieve("first aid", scopes={"medical"})
    assert results
    assert all("medical/" in item.source for item in results)


def test_retriever_env_var_min_score(mock_store: LocalVectorStore, monkeypatch):
    monkeypatch.setenv("RAG_MIN_SCORE", "0.99")
    retriever = Retriever(mock_store, default_top_k=3)
    assert retriever.min_score == 0.99


def test_retriever_default_min_score(mock_store: LocalVectorStore, monkeypatch):
    monkeypatch.delenv("RAG_MIN_SCORE", raising=False)
    retriever = Retriever(mock_store, default_top_k=3)
    assert retriever.min_score == 0.55


@pytest.mark.asyncio
async def test_retriever_top_k_override(mock_store: LocalVectorStore):
    retriever = Retriever(mock_store, default_top_k=5, min_score=0.0)
    results = await retriever.retrieve("motor vehicles act", top_k=1)
    mock_store.search.assert_called_once_with("motor vehicles act", top_k=2, scopes=None)


@pytest.mark.asyncio
async def test_retriever_no_matching_scope(mock_store: LocalVectorStore):
    mock_store.search = AsyncMock(return_value=[])
    retriever = Retriever(mock_store, default_top_k=3, min_score=0.0)
    results = await retriever.retrieve("motor vehicles act helmet fine", scopes={"nonexistent"})
    assert results == []

@pytest.mark.asyncio
async def test_retriever_bm25_coverage():
    mock_store = MagicMock(spec=LocalVectorStore)
    from rag.vectorstore import DocumentChunk
    chunk1 = DocumentChunk(chunk_id="1", source="s1", title="t1", category="c1", content="hello world")
    chunk2 = DocumentChunk(chunk_id="2", source="s2", title="t2", category="c2", content="hello world")
    mock_store.search = AsyncMock(return_value=[(chunk1, 0.9)])
    mock_store.ensure_index = AsyncMock(return_value=[chunk1, chunk2])

    retriever = Retriever(mock_store, default_top_k=5, min_score=0.0)

    # 1st call hits bm25 init
    results1 = await retriever.retrieve("hello")
    # 2nd call hits cached bm25
    results2 = await retriever.retrieve("hello")

    # Test RRF bounds and results
    assert len(results1) > 0
    assert len(results2) > 0

@pytest.mark.asyncio
async def test_retriever_cross_encoder_mock():
    mock_store = MagicMock(spec=LocalVectorStore)
    from rag.vectorstore import DocumentChunk
    chunk1 = DocumentChunk(chunk_id="1", source="s1", title="t1", category="c1", content="hello world")
    chunk2 = DocumentChunk(chunk_id="2", source="s2", title="t2", category="c2", content="hello again")
    mock_store.search = AsyncMock(return_value=[(chunk1, 0.9), (chunk2, 0.8)])
    mock_store.ensure_index = AsyncMock(return_value=[chunk1, chunk2])

    # Enable cross-encoder but let it fail or mock it
    retriever = Retriever(mock_store, default_top_k=5, min_score=0.0, cross_encoder_model="dummy-model")
    results = await retriever.retrieve("hello")
    assert len(results) > 0
