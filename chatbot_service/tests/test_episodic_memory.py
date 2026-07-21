# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from agent.context_assembler import ConversationContext
from memory.episodic_memory import EpisodicMemoryAgent
from providers.base import ProviderRequest, ProviderResult
from rag.vectorstore import DocumentChunk

@pytest.fixture
def mock_router():
    router = AsyncMock()
    result = ProviderResult(
        text="User is a diabetic. User drives a Honda City.",
        provider="mock_provider",
        model="mock_model"
    )
    router.generate.return_value = result
    return router

@pytest.fixture
def agent(mock_router, tmp_path):
    with patch("memory.episodic_memory.LocalVectorStore") as mock_vs_cls:
        mock_vs_instance = AsyncMock()
        mock_vs_cls.return_value = mock_vs_instance
        agent = EpisodicMemoryAgent(
            router=mock_router,
            database_url="sqlite+aiosqlite:///:memory:",
            persist_dir=tmp_path
        )
        agent.vectorstore = mock_vs_instance
        return agent

@pytest.mark.asyncio
async def test_extract_and_store_success(agent, mock_router):
    history = [
        {"role": "user", "content": "I am diabetic."},
        {"role": "assistant", "content": "Noted."}
    ]
    await agent.extract_and_store("session_1", "user_123", history)
    
    mock_router.generate.assert_called_once()
    agent.vectorstore._upsert_pg.assert_called_once()
    args = agent.vectorstore._upsert_pg.call_args[0][0]
    assert len(args) == 1
    assert "User is a diabetic" in args[0].content

@pytest.mark.asyncio
async def test_extract_and_store_no_facts(agent, mock_router):
    mock_router.generate.return_value = ProviderResult(
        text="NO_FACTS",
        provider="mock_provider",
        model="mock_model"
    )
    history = [
        {"role": "user", "content": "Hello."},
        {"role": "assistant", "content": "Hi there."}
    ]
    await agent.extract_and_store("session_2", "user_123", history)
    agent.vectorstore._upsert_pg.assert_not_called()

@pytest.mark.asyncio
async def test_extract_and_store_too_short(agent):
    history = [{"role": "user", "content": "Hello"}]
    await agent.extract_and_store("session_3", "user_123", history)
    agent.router.generate.assert_not_called()

@pytest.mark.asyncio
async def test_extract_and_store_exception(agent, mock_router):
    mock_router.generate.side_effect = Exception("API error")
    history = [
        {"role": "user", "content": "I am diabetic."},
        {"role": "assistant", "content": "Noted."}
    ]
    # Should swallow exception
    await agent.extract_and_store("session_4", "user_123", history)
    agent.vectorstore._upsert_pg.assert_not_called()

@pytest.mark.asyncio
async def test_retrieve_memory(agent):
    chunk = DocumentChunk(chunk_id="1", source="s", title="t", category="user_1", content="Fact 1")
    agent.vectorstore.search.return_value = [(chunk, 0.9)]
    
    results = await agent.retrieve_memory("user_1", "What is my condition?")
    agent.vectorstore.search.assert_called_once_with("What is my condition?", top_k=3, scopes={"user_1"})
    assert results == ["Fact 1"]
