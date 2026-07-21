# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import main
from providers.base import ProviderResult


class FakeBackendToolClient:
    def __init__(self, settings):
        self.settings = settings

    async def aclose(self):
        pass


class FakeConversationMemoryStore:
    def __init__(self, redis_url=None, *, session_ttl_seconds=86400):
        self.redis_url = redis_url
        self.session_ttl_seconds = session_ttl_seconds
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


class FakeRetriever:
    def __init__(self, vectorstore=None, *args, **kwargs):
        self.vectorstore = vectorstore

    async def retrieve(self, query, *, top_k=None, scopes=None):
        return []

class FakeSosTool:
    def __init__(self, backend_client, w3w_tool=None, geocode_client=None):
        self.backend_client = backend_client

    async def get_payload(self, *, lat, lon):
        return {"numbers": {}, "services": []}


class FakeWeatherTool:
    def __init__(self, settings):
        self.settings = settings

    async def lookup(self, *, lat, lon):
        return None

    async def aclose(self):
        pass


class FakeChallanTool:
    def __init__(self, backend_client):
        self.backend_client = backend_client

    async def infer_and_calculate(self, message, client_ip=None):
        return None


class FakeLegalSearchTool:
    def __init__(self, retriever):
        self.retriever = retriever

    async def search(self, message):
        return []


class FakeFirstAidTool:
    def __init__(self, settings):
        self.settings = settings

    def lookup(self, message):
        return None


class FakeRoadInfrastructureTool:
    def __init__(self, backend_client):
        self.backend_client = backend_client

    async def lookup(self, *, lat, lon):
        return None


class FakeRoadIssuesTool:
    def __init__(self, backend_client):
        self.backend_client = backend_client

    async def lookup(self, *, lat, lon):
        return {"count": 0, "issues": []}


class FakeSubmitReportTool:
    def __init__(self, base_url=None):
        self.base_url = base_url

    def build_guidance(self, *, issue_type, lat, lon):
        return {"summary": ""}

    async def aclose(self):
        pass


class FakeSpeechService:
    def __init__(self, settings):
        self.settings = settings

    def status(self):
        return {"configured": True}


class FakeProviderRouter:
    def __init__(self, settings, cache=None):
        self.settings = settings

    async def generate(self, request):
        return ProviderResult(
            text=f"Response for: {request.message}",
            provider="mock",
            model="mock-model",
        )


class FakeIntentDetector:
    def __init__(self, **kwargs):
        pass

    def detect(self, message):
        return "general"

    def refine_intent(self, initial_intent, message, history):
        return initial_intent


class FakeSafetyChecker:
    def evaluate(self, message):
        from agent.safety_checker import SafetyDecision
        return SafetyDecision(blocked=False)


class FakeContextAssembler:
    def __init__(self, **kwargs):
        self.retriever = kwargs.get("retriever")

    async def assemble(self, *, session_id, message, intent, lat, lon, client_ip=None, history=None):
        from agent.state import ConversationContext, RetrievedContext
        context = ConversationContext(
            session_id=session_id,
            message=message,
            intent=intent,
            lat=lat,
            lon=lon,
            client_ip=client_ip,
            history=history or [],
        )
        context.retrieved.append(
            RetrievedContext(
                source="kb:general",
                title="Test",
                snippet="Test snippet",
                score=0.9,
                category="general",
            )
        )
        return context


@pytest.fixture
def admin_app(monkeypatch):
    main.get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_SECRET", "test-admin-secret-key")
    monkeypatch.setattr(main, "BackendToolClient", FakeBackendToolClient)
    monkeypatch.setattr(main, "ConversationMemoryStore", FakeConversationMemoryStore)
    monkeypatch.setattr(main, "LocalVectorStore", FakeVectorStore)
    monkeypatch.setattr(main, "Retriever", FakeRetriever)
    monkeypatch.setattr(main, "SosTool", FakeSosTool)
    monkeypatch.setattr(main, "WeatherTool", FakeWeatherTool)
    monkeypatch.setattr(main, "ChallanTool", FakeChallanTool)
    monkeypatch.setattr(main, "LegalSearchTool", FakeLegalSearchTool)
    monkeypatch.setattr(main, "FirstAidTool", FakeFirstAidTool)
    monkeypatch.setattr(main, "RoadInfrastructureTool", FakeRoadInfrastructureTool)
    monkeypatch.setattr(main, "RoadIssuesTool", FakeRoadIssuesTool)
    monkeypatch.setattr(main, "SubmitReportTool", FakeSubmitReportTool)
    monkeypatch.setattr(main, "IndicSeamlessService", FakeSpeechService)
    monkeypatch.setattr(main, "ProviderRouter", FakeProviderRouter)
    monkeypatch.setattr(main, "IntentDetector", FakeIntentDetector)
    monkeypatch.setattr(main, "SafetyChecker", FakeSafetyChecker)
    monkeypatch.setattr(main, "ContextAssembler", FakeContextAssembler)
    return main.create_app()


def test_admin_health_requires_valid_key(admin_app):
    with TestClient(admin_app) as client:
        response = client.get(
            "/admin/health",
            headers={"X-Admin-Key": "wrong-key"},
        )

    assert response.status_code == 403


def test_admin_health_accepts_valid_key(admin_app):
    with TestClient(admin_app) as client:
        response = client.get(
            "/admin/health",
            headers={"X-Admin-Key": "test-admin-secret-key"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "chunks" in payload
    assert "memory_backend" in payload


def test_admin_health_no_key(admin_app):
    with TestClient(admin_app) as client:
        response = client.get("/admin/health")

    assert response.status_code == 403


def test_rebuild_index_requires_valid_key(admin_app):
    with TestClient(admin_app) as client:
        response = client.post(
            "/admin/rebuild-index",
            headers={"X-Admin-Key": "wrong-key"},
        )

    assert response.status_code == 403


def test_rebuild_index_accepts_valid_key(admin_app):
    with TestClient(admin_app) as client:
        response = client.post(
            "/admin/rebuild-index",
            headers={"X-Admin-Key": "test-admin-secret-key"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "rebuilt"
    assert "index" in payload
