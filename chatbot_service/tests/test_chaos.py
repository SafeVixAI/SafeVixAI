# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag.evaluation import ndcg_at_k, recall_at_k
from rag.retriever import Retriever


@pytest.mark.asyncio
async def test_rag_retrieve_empty_query():
    vs = MagicMock()
    r = Retriever(vs)
    results = await r.retrieve("")
    assert results == []


@pytest.mark.asyncio
async def test_rag_retrieve_graceful_no_vectorstore():
    vs = MagicMock()
    vs.search = AsyncMock(return_value=[])
    vs.ensure_index = AsyncMock(return_value=[])
    r = Retriever(vs)
    results = await r.retrieve("test")
    assert results == []


@pytest.mark.asyncio
async def test_hyde_fallback_on_exception():
    vs = MagicMock()
    vs.search = AsyncMock(return_value=[])
    vs.ensure_index = AsyncMock(return_value=[])

    def failing_hyde(q: str) -> str:
        raise RuntimeError("LLM down")

    r = Retriever(vs, hyde_generate_fn=failing_hyde)
    results = await r.retrieve("test query")
    assert results == []


@pytest.mark.asyncio
async def test_hyde_pass_through_when_none():
    vs = MagicMock()
    vs.search = AsyncMock(return_value=[])
    vs.ensure_index = AsyncMock(return_value=[])
    r = Retriever(vs)
    results = await r.retrieve("test query")
    assert results == []


def test_ndcg_quality():
    perfect = ndcg_at_k([1.0, 1.0, 1.0], 3)
    assert perfect == pytest.approx(1.0)
    zero = ndcg_at_k([0.0, 0.0, 0.0], 3)
    assert zero == pytest.approx(0.0)


def test_recall_quality():
    full = recall_at_k(5, 5, 5)
    assert full == pytest.approx(1.0)
    none = recall_at_k(0, 5, 5)
    assert none == pytest.approx(0.0)
