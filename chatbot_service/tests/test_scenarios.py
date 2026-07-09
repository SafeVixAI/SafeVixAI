# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def base_kwargs():
    return {
        "retriever": MagicMock(retrieve=AsyncMock(return_value=[])),
        "sos_tool": MagicMock(get_payload=AsyncMock(return_value={"numbers": {}, "services": [], "what3words": {"formatted": "filled.fill.fill"}})),
        "challan_tool": MagicMock(infer_and_calculate=AsyncMock(return_value={})),
        "legal_search_tool": MagicMock(search=AsyncMock(return_value=[])),
        "first_aid_tool": MagicMock(),
        "road_infra_tool": MagicMock(),
        "road_issues_tool": MagicMock(),
        "submit_report_tool": MagicMock(),
        "weather_tool": MagicMock(lookup=AsyncMock(return_value=None)),
        "drug_info_tool": MagicMock(),
        "episodic_memory_agent": MagicMock(),
    }


@pytest.mark.asyncio
async def test_emergency_sos_triggers_tool(base_kwargs):
    from agent.context_assembler import ContextAssembler

    assembler = ContextAssembler(**base_kwargs)
    await assembler.assemble(
        session_id="s1", message="accident on highway",
        intent="emergency", lat=12.0, lon=77.0, history=[],
    )
    base_kwargs["sos_tool"].get_payload.assert_called_once()


@pytest.mark.asyncio
async def test_challan_query_uses_retriever(base_kwargs):
    from agent.context_assembler import ContextAssembler

    assembler = ContextAssembler(**base_kwargs)
    await assembler.assemble(
        session_id="s2", message="how much is drunk driving challan",
        intent="challan", lat=12.0, lon=77.0, history=[],
    )
    base_kwargs["legal_search_tool"].search.assert_called()


@pytest.mark.asyncio
async def test_no_vectorstore_graceful():
    from rag.retriever import Retriever
    vs = MagicMock()
    vs.search = AsyncMock(return_value=[])
    vs.ensure_index = AsyncMock(return_value=[])
    r = Retriever(vs)
    results = await r.retrieve("test query")
    assert results == []
