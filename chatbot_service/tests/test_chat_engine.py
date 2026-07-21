# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent.graph import ChatEngine
from agent.safety_checker import SafetyChecker
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
    def __init__(self, *args, **kwargs):
        pass

    async def ensure_index(self):
        return []

    async def build_index(self, *, force=False):
        return []

    async def stats(self):
        return {"chunks": 1, "categories": 1, "chroma_chunks": 1, "embedding_model": "test"}


class FakeIntentDetector:
    def __init__(self, **kwargs):
        pass
    def detect(self, message):
        msg_lower = message.lower()
        if any(w in msg_lower for w in ("ambulance", "hospital", "accident", "emergency", "sos")):
            return "emergency"
        if any(w in msg_lower for w in ("fine", "challan", "section", "penalty")):
            return "challan"
        if any(w in msg_lower for w in ("first aid", "bleeding", "cpr", "wound")):
            return "first_aid"
        return "general"

    def refine_intent(self, initial_intent, message, history):
        return initial_intent


class FakeRetriever:
    def __init__(self, vectorstore=None, *args, **kwargs):
        self.vectorstore = vectorstore

    async def retrieve(self, query, *, top_k=None, scopes=None):
        return []

class FakeSosTool:
    async def get_payload(self, *, lat, lon):
        return {
            "numbers": {"112": {"service": "Emergency"}},
            "services": [{"name": "City Hospital"}],
        }


class FakeWeatherTool:
    async def lookup(self, *, lat, lon):
        return {"summary": "clear", "temperature": 30}

    async def aclose(self):
        pass


class FakeChallanTool:
    async def infer_and_calculate(self, message, client_ip=None):
        return {"section": "185", "base_fine": 10000, "repeat_fine": 15000, "amount_due": 10000}


class FakeLegalSearchTool:
    def __init__(self, retriever):
        self.retriever = retriever

    async def search(self, message):
        return [
            SimpleNamespace(
                source="kb:legal",
                title="MVA",
                category="legal",
                content=f"Legal: {message}",
                score=0.96,
            )
        ]


class FakeFirstAidTool:
    def lookup(self, message):
        return {"title": "First Aid", "steps": ["Step 1", "Step 2"]}


class FakeRoadInfrastructureTool:
    async def lookup(self, *, lat, lon):
        return {"road_type": "Urban", "road_type_code": "URB"}


class FakeRoadIssuesTool:
    async def lookup(self, *, lat, lon):
        return {"count": 0, "issues": []}


class FakeSubmitReportTool:
    def build_guidance(self, *, issue_type, lat, lon):
        return {"summary": f"Report guidance for {issue_type}."}

    async def aclose(self):
        pass


class FakeDrugInfoTool:
    async def lookup(self, drug):
        return None


class FakeContextAssembler:
    def __init__(self, **kwargs):
        self.retriever = kwargs.get("retriever")

    async def assemble(self, *, session_id, message, intent, lat, lon, client_ip=None, history=None):
        from agent.state import ConversationContext, RetrievedContext, ToolContext

        context = ConversationContext(
            session_id=session_id,
            message=message,
            intent=intent,
            lat=lat,
            lon=lon,
            client_ip=client_ip,
            history=history or [],
        )

        results = await self.retriever.retrieve(message)
        for item in results[:3]:
            context.retrieved.append(
                RetrievedContext(
                    source=item.source,
                    title=item.title,
                    snippet=item.content[:320],
                    score=item.score,
                    category=item.category,
                )
            )

        if intent == "emergency":
            context.tools.append(
                ToolContext(
                    name="sos",
                    summary="Nearby: City Hospital",
                    payload={"services": [{"name": "City Hospital"}]},
                    sources=["tool:sos"],
                )
            )

        return context


class FakeProviderRouter:
    def __init__(self, *, should_fail=False, fail_all=False):
        self.should_fail = should_fail
        self.fail_all = fail_all

    async def generate(self, request):
        if self.fail_all:
            raise RuntimeError("All providers failed")
        if self.should_fail:
            raise RuntimeError("Primary provider failed")
        return ProviderResult(
            text=f"Response for: {request.message}",
            provider="mock",
            model="mock-model",
        )


@pytest.fixture
def engine():
    memory = FakeMemoryStore()
    vectorstore = FakeVectorStore()
    intent_detector = FakeIntentDetector()
    safety_checker = SafetyChecker()
    retriever = FakeRetriever()
    provider_router = FakeProviderRouter()

    from agent.context_assembler import ContextAssembler

    real_assembler = ContextAssembler(
        retriever=retriever,
        sos_tool=FakeSosTool(),
        challan_tool=FakeChallanTool(),
        legal_search_tool=FakeLegalSearchTool(retriever),
        first_aid_tool=FakeFirstAidTool(),
        road_infra_tool=FakeRoadInfrastructureTool(),
        road_issues_tool=FakeRoadIssuesTool(),
        submit_report_tool=FakeSubmitReportTool(),
        weather_tool=FakeWeatherTool(),
        drug_info_tool=FakeDrugInfoTool(),
    )

    return ChatEngine(
        memory_store=memory,
        vectorstore=vectorstore,
        intent_detector=intent_detector,
        safety_checker=safety_checker,
        context_assembler=real_assembler,
        provider_router=provider_router,
    )


@pytest.mark.asyncio
async def test_full_pipeline_emergency(engine):
    from agent.state import ChatRequest

    payload = ChatRequest(
        message="I need an ambulance after an accident near Anna Nagar",
        session_id="emergency-session",
        lat=13.0878,
        lon=80.2087,
    )

    response = await engine.chat(payload)

    assert response.session_id == "emergency-session"
    assert response.intent == "emergency"
    assert "tool:sos" in response.sources


@pytest.mark.asyncio
async def test_full_pipeline_challan(engine):
    from agent.state import ChatRequest

    payload = ChatRequest(
        message="What is the fine for not wearing a helmet?",
        session_id="challan-session",
    )

    response = await engine.chat(payload)

    assert response.session_id == "challan-session"
    assert response.intent == "challan"


@pytest.mark.asyncio
async def test_full_pipeline_first_aid(engine):
    from agent.state import ChatRequest

    payload = ChatRequest(
        message="How to do first aid for bleeding?",
        session_id="first-aid-session",
    )

    response = await engine.chat(payload)

    assert response.session_id == "first-aid-session"
    assert response.intent == "first_aid"


@pytest.mark.asyncio
async def test_safety_block_halts_pipeline(engine):
    from agent.state import ChatRequest

    payload = ChatRequest(
        message="How to fake an accident and escape?",
        session_id="blocked-session",
    )

    response = await engine.chat(payload)

    assert response.intent == "blocked"
    assert response.sources == ["policy:safety"]
    assert "112" in response.response


@pytest.mark.asyncio
async def test_intent_detection_accuracy(engine):
    test_cases = [
        ("I need an ambulance", "emergency"),
        ("What is the fine for helmet?", "challan"),
        ("How to do first aid?", "first_aid"),
        ("What is road safety?", "general"),
        ("Call 112 emergency", "emergency"),
        ("Section 185 penalty", "challan"),
    ]

    for message, expected_intent in test_cases:
        detected = engine.intent_detector.detect(message)
        assert detected == expected_intent, f"Failed for: {message}"


@pytest.mark.asyncio
async def test_memory_persistence(engine):
    from agent.state import ChatRequest

    payload = ChatRequest(
        message="What is the speed limit?",
        session_id="memory-session",
    )

    await engine.chat(payload)

    history = await engine.memory_store.get_history("memory-session")
    assert len(history) >= 2
    assert history[0]["role"] == "user"
    assert history[-1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_session_isolation(engine):
    from agent.state import ChatRequest

    await engine.chat(ChatRequest(message="Hello A", session_id="session-a"))
    await engine.chat(ChatRequest(message="Hello B", session_id="session-b"))

    history_a = await engine.memory_store.get_history("session-a")
    history_b = await engine.memory_store.get_history("session-b")

    assert any("Hello A" in h["content"] for h in history_a)
    assert any("Hello B" in h["content"] for h in history_b)
    assert not any("Hello B" in h["content"] for h in history_a)


@pytest.mark.asyncio
async def test_get_history(engine):
    from agent.state import ChatRequest

    await engine.chat(ChatRequest(message="Message 1", session_id="history-session"))
    await engine.chat(ChatRequest(message="Message 2", session_id="history-session"))

    history = await engine.get_history("history-session")
    assert len(history) >= 4


@pytest.mark.asyncio
async def test_stats(engine):
    stats = await engine.stats()
    assert "chunks" in stats
    assert "categories" in stats


def test_dedupe_sources():
    result = ChatEngine._dedupe_sources(["tool:sos", "tool:sos", "kb:general", "kb:general"])
    assert result == ["tool:sos", "kb:general"]
