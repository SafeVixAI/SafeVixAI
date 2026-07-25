# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from uuid import UUID

import pytest

from agent.graph import ChatEngine, _log_intent_refinement
from agent.state import ChatRequest, ConversationContext, RetrievedContext, ToolContext
from providers.base import ProviderResult


class FakeMemoryStore:
    def __init__(self):
        self._memory = {}

    @property
    def backend_name(self):
        return "memory"

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
    def __init__(self, database_url=None, data_dir=None, chunks=1, categories=1, **kwargs):
        self.database_url = database_url
        self.data_dir = data_dir
        self.chunks = chunks
        self.categories = categories

    async def ensure_index(self):
        return []

    async def build_index(self, *, force=False):
        return []

    async def stats(self):
        return {"chunks": self.chunks, "categories": self.categories, "database": "pgvector", "embedding_model": "test"}

class FakeRetriever:
    def __init__(self, vectorstore, *, default_top_k=5, min_score=0.0, **kwargs):
        self.vectorstore = vectorstore
        self.default_top_k = default_top_k
        self.min_score = min_score

    async def retrieve(self, query: str, *, top_k: int | None = None, scopes=None) -> list:
        return []
class FakeIntentDetector:
    def __init__(self, initial_intent="general", refined_intent=None):
        self._initial = initial_intent
        self._refined = refined_intent or initial_intent

    def detect(self, message):
        return self._initial

    def refine_intent(self, initial_intent, message, history):
        return self._refined


class FakeSafetyChecker:
    def __init__(self, blocked=False, response=None):
        self._blocked = blocked
        self._response = response

    def evaluate(self, message):
        from agent.safety_checker import SafetyDecision
        return SafetyDecision(blocked=self._blocked, response=self._response)

    def check_output_safety(self, llm_response: str):
        from agent.safety_checker import SafetyDecision
        return SafetyDecision(blocked=self._blocked, response=self._response)

    async def check_llama_guard(self, message: str, role: str):
        from agent.safety_checker import SafetyDecision
        return SafetyDecision(blocked=self._blocked, response=self._response)

    def add_medical_disclaimer_if_needed(self, message: str, response: str) -> str:
        return response


class FakeSummarizer:
    def get_summary_for_history(self, history):
        if len(history) >= 8:
            return [{"role": "system", "content": "[Summary]"}], {"summary": "Summary"}
        return history, None


class FakeContextAssembler:
    def __init__(self, retrieved=None, tools=None):
        self._retrieved = retrieved or []
        self._tools = tools or []

    async def assemble(self, **kwargs):
        ctx = ConversationContext(
            session_id=kwargs["session_id"],
            message=kwargs["message"],
            intent=kwargs["intent"],
            lat=kwargs.get("lat"),
            lon=kwargs.get("lon"),
            client_ip=kwargs.get("client_ip"),
            history=kwargs.get("history", []),
        )
        for r in self._retrieved:
            ctx.retrieved.append(r)
        for t in self._tools:
            ctx.tools.append(t)
        return ctx


class FakeProviderRouter:
    def __init__(self, text="Response text", should_fail=False):
        self._text = text
        self._should_fail = should_fail

    async def generate(self, request):
        if self._should_fail:
            raise RuntimeError("Provider failed")
        return ProviderResult(text=self._text, provider="mock", model="mock")

    async def stream_generate(self, request):
        if self._should_fail:
            raise RuntimeError("Stream failed")
        yield {"type": "token", "text": "Hello "}
        yield {"type": "token", "text": "world"}
        yield {"type": "done"}


class FakeGovernance:
    def __init__(self, flagged=False, hallucination_score=0.8, factuality_score=0.9):
        self._flagged = flagged
        self._hallucination_score = hallucination_score
        self._factuality_score = factuality_score

    async def evaluate(self, **kwargs):
        from agent.governance import GovernanceResult
        return GovernanceResult(
            text=kwargs.get("response_text", ""),
            hallucination_score=self._hallucination_score,
            factuality_score=self._factuality_score,
            citations=["tool:sos"],
            flagged=self._flagged,
            prompt_version="v1",
        )

    async def close(self):
        pass


@pytest.fixture
def base_engine():
    memory = FakeMemoryStore()
    vectorstore = FakeVectorStore()
    intent_detector = FakeIntentDetector(initial_intent="general", refined_intent="general")
    safety_checker = FakeSafetyChecker()
    summarizer = FakeSummarizer()
    context_assembler = FakeContextAssembler(
        retrieved=[RetrievedContext(source="kb:test", title="Test", snippet="Test content", score=0.9, category="general")],
        tools=[ToolContext(name="test", summary="Test tool", payload={}, sources=["tool:test"])],
    )
    provider_router = FakeProviderRouter()
    governance = FakeGovernance()

    engine = ChatEngine(
        memory_store=memory,
        vectorstore=vectorstore,
        intent_detector=intent_detector,
        safety_checker=safety_checker,
        context_assembler=context_assembler,
        provider_router=provider_router,
    )
    engine.summarizer = summarizer
    engine.governance = governance
    return engine


class TestLogIntentRefinement:
    def test_does_not_log_when_same(self, caplog):
        caplog.set_level("INFO")
        _log_intent_refinement("general", "general", "hello")
        assert not any("Intent refined" in msg for msg in caplog.messages)

    def test_logs_when_different(self, caplog):
        caplog.set_level("INFO")
        _log_intent_refinement("general", "emergency", "help needed")
        assert any("Intent refined" in msg for msg in caplog.messages)
        assert "general -> emergency" in caplog.messages[0]


class TestChat:
    @pytest.mark.asyncio
    async def test_session_id_generation(self):
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(
                retrieved=[RetrievedContext(source="kb:test", title="Test", snippet="Test", score=0.9, category="general")],
                tools=[],
            ),
            provider_router=FakeProviderRouter(),
        )
        engine.governance = FakeGovernance()

        result = await engine.chat(ChatRequest(message="hello"))
        # Verify a valid UUID was generated
        UUID(result.session_id)

    @pytest.mark.asyncio
    async def test_safety_blocked_path(self):
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(blocked=True, response="Blocked by safety policy."),
            context_assembler=FakeContextAssembler(),
            provider_router=FakeProviderRouter(),
        )
        engine.governance = FakeGovernance()

        result = await engine.chat(ChatRequest(message="bad stuff", session_id="safety-test"))

        assert result.intent == "blocked"
        assert result.sources == ["policy:safety"]
        assert result.response == "Blocked by safety policy."
        history = await memory.get_history("safety-test")
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Blocked by safety policy."

    @pytest.mark.asyncio
    async def test_weak_retrieval_path(self):
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("legal", "legal"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(retrieved=[], tools=[]),
            provider_router=FakeProviderRouter(),
        )
        engine.governance = FakeGovernance()
        engine.summarizer = FakeSummarizer()

        result = await engine.chat(ChatRequest(message="obscure legal question", session_id="weak-test"))

        assert "do not know" in result.response.lower()
        assert result.intent == "weak-retrieval"
        assert "policy:weak-retrieval" in result.sources
        history = await memory.get_history("weak-test")
        assert "policy:weak-retrieval" in history[-1]["metadata"]["sources"]

    @pytest.mark.asyncio
    async def test_weak_retrieval_general_intent_not_triggered(self):
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general", "general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(retrieved=[], tools=[]),
            provider_router=FakeProviderRouter(text="General response"),
        )
        engine.governance = FakeGovernance()
        engine.summarizer = FakeSummarizer()

        result = await engine.chat(ChatRequest(message="general chat", session_id="general-test"))

        # General intent skips weak-retrieval path even with no context
        assert "do not know" not in result.response.lower()
        assert result.response == "General response"

    @pytest.mark.asyncio
    async def test_happy_path(self, base_engine):
        result = await base_engine.chat(ChatRequest(message="test", session_id="happy"))
        assert result.response == "Response text"
        assert result.intent == "general"
        assert "kb:test" in result.sources or "tool:test" in result.sources or "tool:sos" in result.sources
        assert result.session_id == "happy"

    @pytest.mark.asyncio
    async def test_governance_flagged_path(self):
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(
                retrieved=[RetrievedContext(source="kb:test", title="Test", snippet="Test", score=0.9, category="general")],
                tools=[ToolContext(name="test", summary="Tool", payload={}, sources=["tool:test"])],
            ),
            provider_router=FakeProviderRouter(text="Low confidence response"),
        )
        engine.governance = FakeGovernance(flagged=True, hallucination_score=0.3, factuality_score=0.4)
        engine.summarizer = FakeSummarizer()

        result = await engine.chat(ChatRequest(message="test", session_id="flag-test"))

        assert "Low confidence" in result.response
        result2 = await engine.chat(ChatRequest(message="test", session_id="flag-test"))
        assert "Low confidence" in result2.response


class TestStreamChat:
    @pytest.mark.asyncio
    async def test_safety_blocked(self):
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(blocked=True, response="Blocked."),
            context_assembler=FakeContextAssembler(),
            provider_router=FakeProviderRouter(),
        )
        engine.governance = FakeGovernance()
        engine.summarizer = FakeSummarizer()

        events = [e async for e in engine.stream_chat(ChatRequest(message="bad", session_id="stream-safety"))]
        assert events[0] == {"type": "token", "text": "Blocked."}
        assert events[1] == {"type": "done", "intent": "blocked", "sources": ["policy:safety"], "session_id": "stream-safety"}

    @pytest.mark.asyncio
    async def test_weak_retrieval(self):
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("legal", "legal"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(retrieved=[], tools=[]),
            provider_router=FakeProviderRouter(),
        )
        engine.governance = FakeGovernance()
        engine.summarizer = FakeSummarizer()

        events = [e async for e in engine.stream_chat(ChatRequest(message="obscure question", session_id="stream-weak"))]
        assert events[0]["type"] == "token"
        assert "do not know" in events[0]["text"].lower()
        assert events[1]["type"] == "done"
        assert "policy:weak-retrieval" in events[1]["sources"]

    @pytest.mark.asyncio
    async def test_token_and_done_flow(self, base_engine):
        events = [e async for e in base_engine.stream_chat(ChatRequest(message="test", session_id="stream-full"))]
        assert len(events) == 3
        assert events[0] == {"type": "token", "text": "Hello "}
        assert events[1] == {"type": "token", "text": "world"}
        assert events[2]["type"] == "done"
        assert events[2]["session_id"] == "stream-full"
        assert "tool:sos" in events[2].get("sources", "")

    @pytest.mark.asyncio
    async def test_stream_governance_flagged(self):
        memory = FakeMemoryStore()
        ctx_assembler = FakeContextAssembler(
            retrieved=[RetrievedContext(source="kb:test", title="Test", snippet="Test", score=0.9, category="general")],
            tools=[ToolContext(name="test", summary="Tool", payload={}, sources=["tool:test"])],
        )
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=ctx_assembler,
            provider_router=FakeProviderRouter(),
        )
        engine.governance = FakeGovernance(flagged=True, hallucination_score=0.3, factuality_score=0.4)
        engine.summarizer = FakeSummarizer()

        events = [e async for e in engine.stream_chat(ChatRequest(message="test", session_id="stream-gov"))]
        assert events[2]["type"] == "done"
        history = await memory.get_history("stream-gov")
        assert "Low confidence" in history[-1]["content"]

    @pytest.mark.asyncio
    async def test_stream_error_event_forwarded(self):
        memory = FakeMemoryStore()
        class ErrorEventProvider(FakeProviderRouter):
            async def stream_generate(self, request):
                yield {"type": "error", "message": "API rate limited"}
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(
                retrieved=[RetrievedContext(source="kb:test", title="Test", snippet="Test", score=0.9, category="general")],
                tools=[ToolContext(name="test", summary="Tool", payload={}, sources=["tool:test"])],
            ),
            provider_router=ErrorEventProvider(),
        )
        engine.governance = FakeGovernance()
        engine.summarizer = FakeSummarizer()

        events = [e async for e in engine.stream_chat(ChatRequest(message="test", session_id="stream-err-ev"))]
        assert events[0]["type"] == "error"
        assert "rate limited" in events[0]["message"].lower()

    @pytest.mark.asyncio
    async def test_exception_during_stream(self):
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(
                retrieved=[RetrievedContext(source="kb:test", title="Test", snippet="Test", score=0.9, category="general")],
                tools=[ToolContext(name="test", summary="Tool", payload={}, sources=["tool:test"])],
            ),
            provider_router=FakeProviderRouter(should_fail=True),
        )
        engine.governance = FakeGovernance()
        engine.summarizer = FakeSummarizer()

        events = [e async for e in engine.stream_chat(ChatRequest(message="test", session_id="stream-exc"))]
        assert len(events) == 1
        assert events[0]["type"] == "error"
        assert "internal error" in events[0]["message"].lower()


class TestDedupeSources:
    def test_empty_list(self):
        assert ChatEngine._dedupe_sources([]) == []

    def test_none_values_skipped(self):
        result = ChatEngine._dedupe_sources(["a", None, "b", "", "c"])
        assert result == ["a", "b", "c"]

    def test_duplicates_removed(self):
        result = ChatEngine._dedupe_sources(["a", "b", "a", "c", "b"])
        assert result == ["a", "b", "c"]

    def test_all_same(self):
        result = ChatEngine._dedupe_sources(["x", "x", "x"])
        assert result == ["x"]

    def test_mixed_empty_and_none(self):
        result = ChatEngine._dedupe_sources(["a", "", None, "b", "", None])
        assert result == ["a", "b"]


class TestGetHistory:
    @pytest.mark.asyncio
    async def test_get_history_delegates_to_memory(self, base_engine):
        await base_engine.chat(ChatRequest(message="msg1", session_id="hist-sess"))
        await base_engine.chat(ChatRequest(message="msg2", session_id="hist-sess"))

        history = await base_engine.get_history("hist-sess")
        assert len(history) >= 4


class TestRebuildIndex:
    @pytest.mark.asyncio
    async def test_rebuild_index_calls_vectorstore(self):
        vs = FakeVectorStore(chunks=10, categories=3)
        engine = ChatEngine(
            memory_store=FakeMemoryStore(),
            vectorstore=vs,
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(),
            provider_router=FakeProviderRouter(),
        )
        result = await engine.rebuild_index()
        assert result["chunks"] == 10
        assert result["categories"] == 3


class TestStats:
    @pytest.mark.asyncio
    async def test_stats_delegates_to_vectorstore(self):
        vs = FakeVectorStore(chunks=5, categories=2)
        engine = ChatEngine(
            memory_store=FakeMemoryStore(),
            vectorstore=vs,
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(),
            provider_router=FakeProviderRouter(),
        )
        result = await engine.stats()
        assert result["chunks"] == 5


class TestClose:
    @pytest.mark.asyncio
    async def test_close_calls_governance_close(self):
        class CloseTrackingGovernance(FakeGovernance):
            closed = False
            async def close(self):
                CloseTrackingGovernance.closed = True

        engine = ChatEngine(
            memory_store=FakeMemoryStore(),
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=FakeContextAssembler(),
            provider_router=FakeProviderRouter(),
        )
        engine.governance = CloseTrackingGovernance()
        await engine.close()
        assert CloseTrackingGovernance.closed
