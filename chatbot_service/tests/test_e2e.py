# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import main
from providers.base import ProviderResult


class FakeBackendToolClient:
    def __init__(self, settings) -> None:
        self.settings = settings

    async def aclose(self) -> None:
        return None


class FakeConversationMemoryStore:
    def __init__(self, redis_url: str | None, *, session_ttl_seconds: int = 86400) -> None:
        self.redis_url = redis_url
        self.session_ttl_seconds = session_ttl_seconds
        self._memory: dict[str, list[dict]] = {}

    @property
    def backend_name(self) -> str:
        return 'memory'

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        payload = {
            'role': role,
            'content': content,
            'metadata': metadata or {},
        }
        self._memory.setdefault(session_id, []).append(payload)
        return payload

    async def get_history(self, session_id: str, *, limit: int = 20) -> list[dict]:
        return self._memory.get(session_id, [])[-limit:]

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None


class FakeVectorStore:
    def __init__(self, database_url=None, data_dir=None, **kwargs):
        self.database_url = database_url
        self.data_dir = data_dir

    async def ensure_index(self):
        return []
        
    async def build_index(self, *, force=False):
        return []

    async def stats(self):
        return {"chunks": 1, "categories": 1, "database": "pgvector", "embedding_model": "test"}

class FakeRetriever:
    def __init__(self, vectorstore, *, default_top_k=5, min_score=0.0, **kwargs):
        self.vectorstore = vectorstore
        self.default_top_k = default_top_k
        self.min_score = min_score

    async def retrieve(self, query: str, *, top_k: int | None = None, scopes=None) -> list:
        return []
class FakeSosTool:
    def __init__(self, backend_client, w3w_tool=None, geocode_client=None) -> None:
        self.backend_client = backend_client

    async def get_payload(self, *, lat: float, lon: float) -> dict:
        return {
            'numbers': {
                '112': {'service': 'Emergency'},
                '108': {'service': 'Ambulance'},
            },
            'services': [
                {'name': 'Rajiv Gandhi Govt Hospital'},
                {'name': 'K4 Anna Nagar Police Station'},
            ],
        }


class FakeWeatherTool:
    def __init__(self, settings) -> None:
        self.settings = settings

    async def lookup(self, *, lat: float, lon: float) -> dict:
        return {'summary': 'clear skies', 'temperature': 29}

    async def aclose(self) -> None:
        return None


class FakeChallanTool:
    def __init__(self, backend_client) -> None:
        self.backend_client = backend_client

    async def infer_and_calculate(self, message: str, client_ip: str | None = None) -> dict:
        return {
            'section': '185',
            'base_fine': 10000,
            'repeat_fine': 15000,
            'amount_due': 10000,
        }


class FakeLegalSearchTool:
    def __init__(self, retriever) -> None:
        self.retriever = retriever

    async def search(self, message: str) -> list:
        return [
            SimpleNamespace(
                source='kb:legal',
                title='Motor Vehicles Act',
                category='legal',
                content=f'Legal reference for: {message}',
                score=0.96,
            )
        ]


class FakeFirstAidTool:
    def __init__(self, settings) -> None:
        self.settings = settings

    def lookup(self, message: str) -> dict:
        return {
            'title': 'Bleeding Control',
            'steps': ['Apply direct pressure.', 'Call emergency services if bleeding is severe.'],
        }


class FakeRoadInfrastructureTool:
    def __init__(self, backend_client) -> None:
        self.backend_client = backend_client

    async def lookup(self, *, lat: float, lon: float) -> dict:
        return {
            'exec_engineer': 'Highways Department',
            'contractor_name': 'City Works',
            'road_type': 'Urban road',
            'road_type_code': 'URB',
        }


class FakeRoadIssuesTool:
    def __init__(self, backend_client) -> None:
        self.backend_client = backend_client

    async def lookup(self, *, lat: float, lon: float) -> dict:
        return {'count': 1, 'issues': [{'id': 'issue-1'}]}


class FakeSubmitReportTool:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url

    def build_guidance(self, *, issue_type: str, lat: float | None, lon: float | None) -> dict:
        return {
            'summary': f'Report guidance for {issue_type} at {lat},{lon}.',
        }

    async def aclose(self) -> None:
        return None


class FakeSpeechService:
    def __init__(self, settings) -> None:
        self.settings = settings

    def status(self) -> dict:
        return {'configured': True}

    def translate_audio_bytes(self, audio_bytes: bytes, *, target_language: str | None = None):
        raise RuntimeError('Speech translation is not used in these tests')


class FakeAIGovernance:
    def __init__(self, redis_url=None) -> None:
        pass

    async def evaluate(self, response_text, retrieved_context, tool_results, prompt):
        from agent.governance import GovernanceResult
        return GovernanceResult(
            text=response_text,
            hallucination_score=1.0,
            factuality_score=1.0,
            citations=[],
            flagged=False,
            prompt_version="v1",
        )

    async def close(self) -> None:
        pass


class FakeProviderRouter:
    def __init__(self, settings, *args, **kwargs) -> None:
        self.settings = settings

    async def generate(self, request) -> ProviderResult:
        if request.intent == 'emergency':
            tool_summary = ' | '.join(request.tool_summaries)
            return ProviderResult(
                text=f'MOCK_EMERGENCY_RESPONSE: {tool_summary}',
                provider='mock',
                model='mock-model',
            )
        if any('\u0b80' <= char <= '\u0bff' for char in request.message):
            return ProviderResult(
                text=f'MOCK_TAMIL_RESPONSE: {request.message}',
                provider='mock',
                model='mock-model',
            )
        return ProviderResult(
            text=f'MOCK_ENGLISH_RESPONSE: {request.message}',
            provider='mock',
            model='mock-model',
        )


@pytest.fixture
def app(monkeypatch):
    main.get_settings.cache_clear()
    monkeypatch.setattr(main, 'BackendToolClient', FakeBackendToolClient)
    monkeypatch.setattr(main, 'ConversationMemoryStore', FakeConversationMemoryStore)
    monkeypatch.setattr(main, 'LocalVectorStore', FakeVectorStore)
    monkeypatch.setattr(main, 'Retriever', FakeRetriever)
    monkeypatch.setattr(main, 'SosTool', FakeSosTool)
    monkeypatch.setattr(main, 'WeatherTool', FakeWeatherTool)
    monkeypatch.setattr(main, 'ChallanTool', FakeChallanTool)
    monkeypatch.setattr(main, 'LegalSearchTool', FakeLegalSearchTool)
    monkeypatch.setattr(main, 'FirstAidTool', FakeFirstAidTool)
    monkeypatch.setattr(main, 'RoadInfrastructureTool', FakeRoadInfrastructureTool)
    monkeypatch.setattr(main, 'RoadIssuesTool', FakeRoadIssuesTool)
    monkeypatch.setattr(main, 'SubmitReportTool', FakeSubmitReportTool)
    monkeypatch.setattr(main, 'IndicSeamlessService', FakeSpeechService)
    monkeypatch.setattr(main, 'ProviderRouter', FakeProviderRouter)
    import agent.graph
    monkeypatch.setattr(agent.graph, 'AIGovernance', FakeAIGovernance)
    return main.create_app()


@pytest_asyncio.fixture
async def client(app):
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://testserver') as async_client:
            yield async_client


@pytest.mark.asyncio
async def test_chat_endpoint_handles_basic_english_query(client: AsyncClient):
    response = await client.post(
        '/api/v1/chat/',
        json={
            'message': 'What traffic safety checks should I do before a road trip?',
            'session_id': 'english-session',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['response'] == 'MOCK_ENGLISH_RESPONSE: What traffic safety checks should I do before a road trip?'
    assert payload['intent'] == 'general'
    assert payload['sources'] == ['kb:general']
    assert payload['session_id'] == 'english-session'


@pytest.mark.asyncio
async def test_chat_endpoint_handles_tamil_query(client: AsyncClient):
    tamil_message = 'சாலையில் விபத்து நடந்தால் என்ன செய்ய வேண்டும்?'
    response = await client.post(
        '/api/v1/chat/',
        json={
            'message': tamil_message,
            'session_id': 'tamil-session',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['response'] == f'MOCK_TAMIL_RESPONSE: {tamil_message}'
    assert payload['intent'] == 'general'
    assert payload['sources'] == ['kb:general']
    assert payload['session_id'] == 'tamil-session'


@pytest.mark.asyncio
async def test_chat_endpoint_handles_emergency_query_with_coordinates(client: AsyncClient):
    response = await client.post(
        '/api/v1/chat/',
        json={
            'message': 'Emergency, I need an ambulance after an accident near Anna Nagar.',
            'session_id': 'emergency-session',
            'lat': 13.0878,
            'lon': 80.2087,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['response'].startswith('MOCK_EMERGENCY_RESPONSE:')
    assert 'Nearby emergency services: Rajiv Gandhi Govt Hospital, K4 Anna Nagar Police Station.' in payload['response']
    assert 'Local weather: clear skies at 29 degrees.' in payload['response']
    assert payload['intent'] == 'emergency'
    assert payload['sources'] == [
        'tool:sos',
        'backend:/api/v1/emergency/sos',
        'tool:weather',
        'kb:emergency',
    ]
    assert payload['session_id'] == 'emergency-session'