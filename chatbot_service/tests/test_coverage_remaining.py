# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import ChatEngine
from agent.multi_agent import (
    ChatState,
    EmergencyDispatchAgent,
    LegalAgent,
    MultiAgentGraph,
    SupervisorAgent,
)
from agent.state import ChatRequest, ConversationContext, RetrievedContext, ToolContext
from providers.base import ProviderResult


class FakeMemoryStore:
    def __init__(self):
        self._memory = {}
    async def append_message(self, session_id, role, content, metadata=None):
        payload = {"role": role, "content": content, "metadata": metadata or {}}
        self._memory.setdefault(session_id, []).append(payload)
        return payload
    async def get_history(self, session_id, *, limit=20):
        return self._memory.get(session_id, [])[-limit:]
    async def ping(self):
        return True

    async def close(self):
        pass

class FakeVectorStore:
    def __init__(self, chunks=1, categories=1):
        self.chunks = chunks
        self.categories = categories

    async def ensure_index(self):
        return []

    async def build_index(self, *, force=False):
        return []
    async def stats(self):
        return {"chunks": self.chunks, "categories": self.categories, "database": "pgvector", "embedding_model": "test"}

class FakeSafetyChecker:
    def __init__(self, blocked=False, response=None, llama_blocked=None):
        self._blocked = blocked
        self._response = response
        self._llama_blocked = llama_blocked
    def evaluate(self, message):
        from agent.safety_checker import SafetyDecision
        return SafetyDecision(blocked=self._blocked, response=self._response)
    def check_output_safety(self, llm_response):
        from agent.safety_checker import SafetyDecision
        return SafetyDecision(blocked=self._blocked, response=self._response)
    async def check_llama_guard(self, message, role):
        from agent.safety_checker import SafetyDecision
        b = self._llama_blocked if self._llama_blocked is not None else self._blocked
        return SafetyDecision(blocked=b, response=self._response)
    def add_medical_disclaimer_if_needed(self, message, response): return response

class FakeSummarizer:
    def get_summary_for_history(self, history):
        if len(history) >= 8:
            return [{"role": "system", "content": "[Summary]"}], {"summary": "Summary"}
        return history, None

class FakeContextAssembler:
    def __init__(self, retrieved=None, tools=None):
        self._retrieved = retrieved if retrieved is not None else [RetrievedContext(source="kb:test", title="Test", snippet="Test", score=0.9, category="general")]
        self._tools = tools if tools is not None else [ToolContext(name="test", summary="Tool", payload={}, sources=["tool:test"])]
    async def assemble(self, **kwargs):
        ctx = ConversationContext(session_id=kwargs["session_id"], message=kwargs["message"], intent=kwargs["intent"])
        for r in self._retrieved:
            ctx.retrieved.append(r)
        for t in self._tools:
            ctx.tools.append(t)
        return ctx

class FakeGovernance:
    def __init__(self, flagged=False):
        self._flagged = flagged
    async def evaluate(self, **kwargs):
        from agent.governance import GovernanceResult
        return GovernanceResult(text=kwargs.get("response_text", ""), hallucination_score=0.8, factuality_score=0.9, citations=["tool:sos"], flagged=self._flagged, prompt_version="v1")
    async def close(self): pass

class FakeProviderRouter:
    def __init__(self, text="Response text"):
        self._text = text
    async def generate(self, request):
        return ProviderResult(text=self._text, provider="mock", model="mock")
    async def stream_generate(self, request):
        yield {"type": "token", "text": "Hello "}
        yield {"type": "token", "text": "world"}
        yield {"type": "done"}

def _make_engine(**overrides):
    defaults = dict(
        memory_store=FakeMemoryStore(),
        vectorstore=FakeVectorStore(),
        intent_detector=MagicMock(detect=MagicMock(return_value="general"), refine_intent=MagicMock(return_value="general")),
        safety_checker=FakeSafetyChecker(),
        context_assembler=FakeContextAssembler(),
        provider_router=FakeProviderRouter(),
    )
    defaults.update(overrides)
    engine = ChatEngine(**defaults)
    engine.governance = FakeGovernance()
    engine.summarizer = FakeSummarizer()
    return engine


class TestGraphLoadUserProviders:
    @pytest.mark.asyncio
    async def test_no_user_id_returns_early(self):
        engine = _make_engine(redis_url="redis://localhost:6379/0")
        await engine._load_user_providers(None)

    @pytest.mark.asyncio
    async def test_no_redis_url_returns_early(self):
        engine = _make_engine(redis_url=None)
        await engine._load_user_providers("user123")

    @pytest.mark.asyncio
    async def test_redis_url_not_set_on_engine(self):
        engine = _make_engine()
        engine.redis_url = None
        import asyncio
        await engine._load_user_providers("user123")

    @pytest.mark.asyncio
    async def test_with_user_id_loads_configs(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps([{"provider_name": "groq", "api_key": "key", "model": "mixtral"}])
        mock_redis.aclose = AsyncMock()
        with patch("redis.asyncio.Redis.from_url", return_value=mock_redis):
            engine = _make_engine(redis_url="redis://localhost:6379/0")
            engine.provider_router = MagicMock()
            await engine._load_user_providers("user123")
            engine.provider_router.configure_user_providers.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_user_id_no_config(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.aclose = AsyncMock()
        with patch("redis.asyncio.Redis.from_url", return_value=mock_redis):
            engine = _make_engine(redis_url="redis://localhost:6379/0")
            await engine._load_user_providers("user123")

    @pytest.mark.asyncio
    async def test_redis_error_logged(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = ConnectionError("redis down")
        mock_redis.aclose = AsyncMock()
        with patch("redis.asyncio.Redis.from_url", return_value=mock_redis):
            engine = _make_engine(redis_url="redis://localhost:6379/0")
            await engine._load_user_providers("user123")


class TestGraphLlamaGuardBlocking:
    @pytest.mark.asyncio
    async def test_chat_llama_guard_blocks(self):
        engine = _make_engine(
            safety_checker=FakeSafetyChecker(blocked=False, llama_blocked=True, response="Llama blocked"),
        )
        result = await engine.chat(ChatRequest(message="test", session_id="lg-block"))
        assert result.intent == "blocked"

    @pytest.mark.asyncio
    async def test_chat_output_safety_blocked(self):
        class SafeEvalBlockOutput(FakeSafetyChecker):
            def evaluate(self, message):
                from agent.safety_checker import SafetyDecision
                return SafetyDecision(blocked=False)
            def check_output_safety(self, llm_response):
                from agent.safety_checker import SafetyDecision
                return SafetyDecision(blocked=True, response="Output blocked")
            async def check_llama_guard(self, message, role):
                from agent.safety_checker import SafetyDecision
                return SafetyDecision(blocked=False)
        engine = _make_engine(safety_checker=SafeEvalBlockOutput())
        result = await engine.chat(ChatRequest(message="test", session_id="out-block"))
        assert result.intent == "blocked_output"

    @pytest.mark.asyncio
    async def test_chat_output_safety_llama_blocks(self):
        class SafeEvalLlamaOutputBlocks(FakeSafetyChecker):
            def evaluate(self, message):
                from agent.safety_checker import SafetyDecision
                return SafetyDecision(blocked=False)
            async def check_llama_guard(self, message, role):
                from agent.safety_checker import SafetyDecision
                if role == "user":
                    return SafetyDecision(blocked=False)
                return SafetyDecision(blocked=True, response="Llama output blocked")
            def check_output_safety(self, llm_response):
                from agent.safety_checker import SafetyDecision
                return SafetyDecision(blocked=False)
        engine = _make_engine(safety_checker=SafeEvalLlamaOutputBlocks())
        result = await engine.chat(ChatRequest(message="test", session_id="llama-out-block"))
        assert result.intent == "blocked_output"


class TestGraphStreamOutputSafety:
    @pytest.mark.asyncio
    async def test_stream_output_safety_blocked(self):
        engine = _make_engine(
            safety_checker=FakeSafetyChecker(blocked=True, response="Blocked."),
        )
        events = [e async for e in engine.stream_chat(ChatRequest(message="test", session_id="st-out-block"))]
        assert events[0]["type"] == "token"

    @pytest.mark.asyncio
    async def test_stream_exception_handling(self):
        engine = _make_engine(provider_router=MagicMock())
        engine.provider_router.stream_generate.side_effect = RuntimeError("Unexpected stream error")
        events = [e async for e in engine.stream_chat(ChatRequest(message="test", session_id="st-exc"))]
        assert len(events) == 1
        assert events[0]["type"] == "error"


class TestChatState:
    def test_defaults(self):
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None)
        assert state.lat is None
        assert state.final_response is None
        assert state.final_sources == []
        assert state.blocked is False

    def test_with_location(self):
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None, lat=13.0, lon=80.0)
        assert state.lat == 13.0


class TestEmergencyDispatchAgent:
    @pytest.mark.asyncio
    async def test_execute_with_geocoding_tool(self):
        ctx = FakeContextAssembler()
        agent = EmergencyDispatchAgent(ctx)
        state = ChatState(session_id="s1", message="help", intent="sos", history=[], summarized_history=[], user_id=None, lat=13.0, lon=80.0)
        await agent.execute(state)
        assert state.final_response is not None
        assert "EMERGENCY" in state.final_response
        assert "policy:emergency-dispatch" in state.final_sources

    @pytest.mark.asyncio
    async def test_execute_no_location_tool(self):
        ctx = FakeContextAssembler(tools=[])
        agent = EmergencyDispatchAgent(ctx)
        state = ChatState(session_id="s1", message="help", intent="sos", history=[], summarized_history=[], user_id=None)
        await agent.execute(state)
        assert "unknown location" in state.final_response


class TestLegalAgent:
    @pytest.mark.asyncio
    async def test_execute_sets_context(self):
        ctx = FakeContextAssembler()
        agent = LegalAgent(ctx)
        state = ChatState(session_id="s1", message="fine?", intent="challan", history=[], summarized_history=[], user_id=None)
        await agent.execute(state)
        assert state.context is not None
        assert len(state.context.retrieved) > 0


class TestSupervisorAgent:
    @pytest.mark.asyncio
    async def test_routes_sos_to_emergency(self):
        ctx = FakeContextAssembler(tools=[])
        agent = SupervisorAgent(
            emergency_agent=EmergencyDispatchAgent(ctx),
            legal_agent=LegalAgent(ctx),
            default_assembler=ctx,
        )
        state = ChatState(session_id="s1", message="help", intent="sos", history=[], summarized_history=[], user_id=None)
        await agent.route_and_execute(state)
        assert "EMERGENCY" in state.final_response

    @pytest.mark.asyncio
    async def test_routes_legal(self):
        ctx = FakeContextAssembler(retrieved=[], tools=[])
        agent = SupervisorAgent(
            emergency_agent=EmergencyDispatchAgent(ctx),
            legal_agent=LegalAgent(ctx),
            default_assembler=ctx,
        )
        state = ChatState(session_id="s1", message="fine?", intent="legal", history=[], summarized_history=[], user_id=None)
        await agent.route_and_execute(state)
        assert state.context is not None

    @pytest.mark.asyncio
    async def test_routes_challan(self):
        ctx = FakeContextAssembler(retrieved=[], tools=[])
        agent = SupervisorAgent(
            emergency_agent=EmergencyDispatchAgent(ctx),
            legal_agent=LegalAgent(ctx),
            default_assembler=ctx,
        )
        state = ChatState(session_id="s1", message="penalty", intent="challan", history=[], summarized_history=[], user_id=None)
        await agent.route_and_execute(state)
        assert state.context is not None

    @pytest.mark.asyncio
    async def test_routes_general(self):
        ctx = FakeContextAssembler(retrieved=[], tools=[])
        agent = SupervisorAgent(
            emergency_agent=EmergencyDispatchAgent(ctx),
            legal_agent=LegalAgent(ctx),
            default_assembler=ctx,
        )
        state = ChatState(session_id="s1", message="hello", intent="general", history=[], summarized_history=[], user_id=None)
        await agent.route_and_execute(state)
        assert state.context is not None


class TestMultiAgentGraph:
    @pytest.mark.asyncio
    async def test_execute_sos_returns_early(self):
        ctx = FakeContextAssembler(tools=[])
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=FakeProviderRouter())
        state = ChatState(session_id="s1", message="help", intent="sos", history=[], summarized_history=[], user_id=None)
        result = await graph.execute(state)
        assert result.final_response is not None
        assert "EMERGENCY" in result.final_response

    @pytest.mark.asyncio
    async def test_execute_weak_retrieval(self):
        ctx = FakeContextAssembler(retrieved=[], tools=[])
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=FakeProviderRouter())
        state = ChatState(session_id="s1", message="obscure", intent="legal", history=[], summarized_history=[], user_id=None)
        result = await graph.execute(state)
        assert "do not know" in result.final_response
        assert result.intent == "weak-retrieval"

    @pytest.mark.asyncio
    async def test_execute_general_skips_weak_retrieval(self):
        ctx = FakeContextAssembler(retrieved=[], tools=[])
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=FakeProviderRouter(text="General answer"))
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None)
        result = await graph.execute(state)
        assert result.final_response == "General answer"

    @pytest.mark.asyncio
    async def test_execute_normal_path(self):
        ctx = FakeContextAssembler()
        router = FakeProviderRouter()
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=router)
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None)
        await graph.execute(state)
        assert state.final_response is not None

    @pytest.mark.asyncio
    async def test_stream_execute_sos_returns_early(self):
        ctx = FakeContextAssembler(tools=[])
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=FakeProviderRouter())
        state = ChatState(session_id="s1", message="help", intent="sos", history=[], summarized_history=[], user_id=None)
        events = [e async for e in graph.stream_execute(state)]
        assert len(events) == 2
        assert events[0]["type"] == "token"

    @pytest.mark.asyncio
    async def test_stream_execute_weak_retrieval(self):
        ctx = FakeContextAssembler(retrieved=[], tools=[])
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=FakeProviderRouter())
        state = ChatState(session_id="s1", message="obscure", intent="legal", history=[], summarized_history=[], user_id=None)
        events = [e async for e in graph.stream_execute(state)]
        assert events[0]["type"] == "token"
        assert events[1]["type"] == "done"

    def test_dispatch_memory_no_agent(self):
        ctx = FakeContextAssembler()
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=FakeProviderRouter())
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None)
        graph._dispatch_memory(state)

    @pytest.mark.asyncio
    async def test_dispatch_memory_with_agent(self):
        ctx = FakeContextAssembler()
        memory_agent = MagicMock()
        memory_agent.extract_and_store = AsyncMock()
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=FakeProviderRouter(), episodic_memory_agent=memory_agent)
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id="real_user")
        state.final_response = "ok"
        graph._dispatch_memory(state)
        memory_agent.extract_and_store.assert_called_once()

    def test_compress_tool_payloads_with_data(self):
        ctx = FakeContextAssembler()
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=FakeProviderRouter())
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None)
        state.context = ConversationContext(session_id="s1", message="hi", intent="general")
        state.context.tools = [ToolContext(name="weather", summary="25C", payload={"temp": 25}, sources=[])]
        summaries = graph._compress_tool_payloads(state)
        assert len(summaries) == 1
        assert "25" in summaries[0]

    def test_compress_tool_no_payload(self):
        ctx = FakeContextAssembler()
        graph = MultiAgentGraph(context_assembler=ctx, provider_router=FakeProviderRouter())
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None)
        state.context = ConversationContext(session_id="s1", message="hi", intent="general")
        state.context.tools = [ToolContext(name="weather", summary="25C", payload=None, sources=[])]
        summaries = graph._compress_tool_payloads(state)
        assert "25C" in summaries[0]
