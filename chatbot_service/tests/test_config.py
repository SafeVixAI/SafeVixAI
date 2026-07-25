# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from agent.state import (
    ChatRequest,
    ChatResponse,
    ConversationContext,
    RetrievedContext,
    ToolContext,
)
from config import (
    ROOT_DIR,
    Settings,
    _as_optional_path,
    _as_path,
    _split_csv,
    get_settings,
)

# ═══════════════════════════════════════════════════════════════════════════════
# _split_csv
# ═══════════════════════════════════════════════════════════════════════════════

class TestSplitCSV:
    def test_none_returns_default(self):
        assert _split_csv(None, default=['a']) == ['a']

    def test_empty_string_returns_default(self):
        assert _split_csv('', default=['a']) == ['a']
        assert _split_csv('   ', default=['a']) == ['a']

    def test_comma_separated_values(self):
        result = _split_csv('a,b,c', default=[])
        assert result == ['a', 'b', 'c']

    def test_strips_whitespace(self):
        result = _split_csv(' a , b , c ', default=[])
        assert result == ['a', 'b', 'c']

    def test_removes_empty_entries(self):
        result = _split_csv('a,,b,,,c', default=[])
        assert result == ['a', 'b', 'c']

    def test_single_value(self):
        result = _split_csv('hello', default=[])
        assert result == ['hello']


# ═══════════════════════════════════════════════════════════════════════════════
# _as_path
# ═══════════════════════════════════════════════════════════════════════════════

class TestAsPath:
    def test_none_returns_default(self):
        default = Path('/default/path')
        assert _as_path(None, default=default) == default

    def test_empty_string_returns_default(self):
        default = Path('/default/path')
        assert _as_path('', default=default) == default

    def test_absolute_path_unchanged(self):
        result = _as_path(str(Path('/absolute/path')), default=Path('/default'))
        assert result.is_absolute()
        assert result.name == 'path'

    def test_relative_path_resolved(self):
        result = _as_path('relative/path', default=Path('/default'))
        assert result == ROOT_DIR / 'relative/path'

    def test_absolute_path_different_drive(self):
        result = _as_path(str(Path('/other/path')), default=Path('/default'))
        assert result.is_absolute()
        assert result.name == 'path'


# ═══════════════════════════════════════════════════════════════════════════════
# _as_optional_path
# ═══════════════════════════════════════════════════════════════════════════════

class TestAsOptionalPath:
    def test_none_returns_none(self):
        assert _as_optional_path(None) is None

    def test_empty_string_returns_none(self):
        assert _as_optional_path('') is None
        assert _as_optional_path('   ') is None

    def test_absolute_path_unchanged(self):
        result = _as_optional_path(str(Path('/some/path')))
        assert result.is_absolute()
        assert result.name == 'path'

    def test_relative_path_resolved(self):
        result = _as_optional_path('data/files')
        assert result == ROOT_DIR / 'data/files'

    def test_valid_path_returns_absolute(self):
        result = _as_optional_path(str(Path('/tmp/test')))
        assert result.is_absolute()
        assert str(result).endswith('test')


# ═══════════════════════════════════════════════════════════════════════════════
# Settings + get_settings
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def mock_env():
    """Provide a dict that mirrors changes to os.environ for pydantic-settings."""
    env: dict[str, str] = {}

    class _EnvProxy(dict):
        def __setitem__(self, key, value):
            super().__setitem__(key, value)
            os.environ[key] = value

    proxy = _EnvProxy()
    yield proxy

    for key in list(proxy.keys()):
        os.environ.pop(key, None)


@pytest.fixture(autouse=True)
def _clean_env():
    """Save and restore all env vars that Settings might read."""
    settings_env_keys = [
        'ENVIRONMENT', 'CHATBOT_SERVICE_NAME', 'CHATBOT_SERVICE_PORT',
        'CORS_ORIGINS', 'MAIN_BACKEND_BASE_URL', 'MAIN_BACKEND_TIMEOUT_SECONDS',
        'REDIS_URL', 'CHATBOT_INTERNAL_API_KEY', 'CHROMA_PERSIST_DIR',
        'RAG_DATA_DIR', 'EMBEDDING_MODEL', 'RAG_MIN_SCORE', 'TOP_K_RETRIEVAL',
        'DEFAULT_LLM_PROVIDER', 'DEFAULT_LLM_MODEL', 'SPEECH_MODEL_ID',
        'SPEECH_MODEL_DIR', 'SPEECH_DEVICE', 'SPEECH_DEFAULT_TARGET_LANG',
        'OPENWEATHER_API_KEY', 'OPENWEATHER_BASE_URL', 'OPENWEATHER_UNITS',
        'W3W_API_KEY', 'OPENCAGE_API_KEY', 'HTTP_TIMEOUT_SECONDS',
        'HTTP_USER_AGENT', 'SESSION_TTL_SECONDS', 'ADMIN_SECRET', 'SENTRY_DSN',
    ]
    saved = {k: os.environ.pop(k, None) for k in settings_env_keys if k in os.environ}
    yield
    os.environ.update({k: v for k, v in saved.items() if v is not None})


@pytest.fixture(autouse=True)
def _mock_mkdir():
    with patch('pathlib.Path.mkdir'):
        yield


class TestSettings:
    def test_creates_with_all_fields(self):
        s = Settings(
            environment='testing',
            service_name='Test',
            service_port=9999,
            cors_origins='http://localhost',
            main_backend_base_url='http://localhost:8000',
            main_backend_timeout_seconds=30.0,
            redis_url='redis://localhost',
            internal_api_key='key123',
            chroma_persist_dir=Path('/tmp/chroma'),
            rag_data_dir=Path('/tmp/data'),
            embedding_model='hash',
            rag_min_score=0.5,
            top_k_retrieval=10,
            default_llm_provider='groq',
            default_llm_model='llama3',
            speech_model_id='model/v1',
            speech_model_dir=None,
            speech_device='auto',
            speech_default_target_lang='eng',
            openweather_api_key='ow-key',
            openweather_base_url='https://api.openweathermap.org/data/2.5',
            openweather_units='metric',
            w3w_api_key='w3w-key',
            opencage_api_key='oc-key',
            http_timeout_seconds=15.0,
            http_user_agent='Test/1.0',
            session_ttl_seconds=3600,
            admin_secret='admin-secret',
            sentry_dsn='https://key@sentry.io/123',
        )
        assert s.environment == 'testing'
        assert s.service_port == 9999
        assert s.main_backend_base_url == 'http://localhost:8000'

    def test_default_values_from_environment(self, mock_env):
        s = get_settings()
        assert s.environment == 'development'
        assert s.service_name == 'SafeVixAI Chatbot Service'
        assert s.service_port == 8010
        assert s.cors_origins_list == ['http://localhost:3000', 'http://127.0.0.1:3000']
        assert s.main_backend_base_url == 'http://localhost:8000'
        assert s.redis_url is None
        assert s.chroma_persist_dir == ROOT_DIR / 'data' / 'chroma_db'
        assert s.rag_data_dir == ROOT_DIR / 'data'

    def test_reads_from_env_overrides(self, mock_env):
        mock_env['ENVIRONMENT'] = 'staging'
        mock_env['CHATBOT_SERVICE_PORT'] = '9090'
        mock_env['MAIN_BACKEND_BASE_URL'] = 'http://backend:8000/'
        mock_env['REDIS_URL'] = 'redis://upstash:6379'
        mock_env['CHROMA_PERSIST_DIR'] = '/custom/chroma'
        mock_env['RAG_DATA_DIR'] = '/custom/rag'
        mock_env['EMBEDDING_MODEL'] = 'sentence-transformers/all-MiniLM-L6-v2'
        mock_env['DEFAULT_LLM_PROVIDER'] = '  gemini  '
        mock_env['CORS_ORIGINS'] = 'https://app.example.com, https://api.example.com'

        s = get_settings()
        assert s.environment == 'staging'
        assert s.service_port == 9090
        assert s.main_backend_base_url == 'http://backend:8000'
        assert s.redis_url == 'redis://upstash:6379'
        assert str(s.chroma_persist_dir).replace('\\', '/').endswith('/custom/chroma')
        assert str(s.rag_data_dir).replace('\\', '/').endswith('/custom/rag')
        assert s.default_llm_provider == 'gemini'
        assert s.cors_origins_list == ['https://app.example.com', 'https://api.example.com']

    def test_cors_guard_production_wildcard_raises(self, mock_env):
        mock_env['ENVIRONMENT'] = 'production'
        mock_env['CORS_ORIGINS'] = '*'
        with pytest.raises(RuntimeError, match='CORS_ORIGINS must list explicit origins'):
            get_settings()

    def test_cors_guard_production_explicit_origins_ok(self, mock_env):
        mock_env['ENVIRONMENT'] = 'production'
        mock_env['CORS_ORIGINS'] = 'https://app.example.com'
        s = get_settings()
        assert s.cors_origins_list == ['https://app.example.com']
        assert s.environment == 'production'

    def test_cors_guard_development_wildcard_ok(self, mock_env):
        mock_env['ENVIRONMENT'] = 'development'
        mock_env['CORS_ORIGINS'] = '*'
        s = get_settings()
        assert '*' in s.cors_origins_list

    def test_creates_chroma_persist_dir_and_rag_data_dir(self, mock_env, _mock_mkdir):
        s = get_settings()
        assert s.chroma_persist_dir == ROOT_DIR / 'data' / 'chroma_db'
        assert s.rag_data_dir == ROOT_DIR / 'data'

    def test_main_backend_base_url_stripped_trailing_slash(self, mock_env):
        mock_env['MAIN_BACKEND_BASE_URL'] = 'http://localhost:8000/'
        s = get_settings()
        assert s.main_backend_base_url == 'http://localhost:8000'
        assert not s.main_backend_base_url.endswith('/')

    def test_openweather_base_url_stripped(self, mock_env):
        mock_env['OPENWEATHER_BASE_URL'] = 'https://api.example.com/'
        s = get_settings()
        assert s.openweather_base_url == 'https://api.example.com'

    def test_empty_env_vars_resolve_to_none(self, mock_env):
        mock_env['REDIS_URL'] = ''
        mock_env['CHATBOT_INTERNAL_API_KEY'] = ''
        s = get_settings()
        assert s.redis_url is None
        assert s.internal_api_key is None

    def test_speech_defaults(self, mock_env):
        s = get_settings()
        assert s.speech_model_id == 'ai4bharat/indic-seamless'
        assert s.speech_device == 'auto'
        assert s.speech_default_target_lang == 'eng'
        assert s.speech_model_dir is None

    def test_frozen_model(self, mock_env):
        s = get_settings()
        with pytest.raises((AttributeError, TypeError, ValidationError)):
            s.environment = 'changed'

    def test_all_optional_fields_none_by_default(self, mock_env):
        s = get_settings()
        assert s.internal_api_key is None
        assert s.openweather_api_key is None
        assert s.w3w_api_key is None
        assert s.opencage_api_key is None
        assert s.admin_secret is None
        assert s.sentry_dsn is None
        assert s.speech_model_dir is None

    def test_http_defaults(self, mock_env):
        s = get_settings()
        assert s.http_timeout_seconds == 20.0
        assert s.http_user_agent == 'SafeVixAIChatbot/1.0'
        assert s.session_ttl_seconds == 86400

    def test_rag_defaults(self, mock_env):
        s = get_settings()
        assert s.rag_min_score == 0.55
        assert s.top_k_retrieval == 5
        assert s.default_llm_model == 'deterministic-rag'


# ═══════════════════════════════════════════════════════════════════════════════
# ChatRequest
# ═══════════════════════════════════════════════════════════════════════════════

class TestChatRequest:
    def test_valid_message(self):
        req = ChatRequest(message='Hello')
        assert req.message == 'Hello'
        assert req.session_id is None
        assert req.lat is None
        assert req.lon is None

    def test_empty_message_raises(self):
        with pytest.raises(ValidationError):
            ChatRequest(message='')

    def test_long_message_raises(self):
        with pytest.raises(ValidationError):
            ChatRequest(message='x' * 4001)

    def test_lat_lon_validation_valid(self):
        req = ChatRequest(message='test', lat=13.08, lon=80.27)
        assert req.lat == 13.08
        assert req.lon == 80.27

    def test_lat_out_of_bounds_raises(self):
        with pytest.raises(ValidationError):
            ChatRequest(message='test', lat=100.0, lon=0.0)
        with pytest.raises(ValidationError):
            ChatRequest(message='test', lat=-91.0, lon=0.0)

    def test_lon_out_of_bounds_raises(self):
        with pytest.raises(ValidationError):
            ChatRequest(message='test', lat=0.0, lon=200.0)
        with pytest.raises(ValidationError):
            ChatRequest(message='test', lat=0.0, lon=-181.0)

    def test_session_id_bounds(self):
        req = ChatRequest(message='test', session_id='abc-123')
        assert req.session_id == 'abc-123'
        with pytest.raises(ValidationError):
            ChatRequest(message='test', session_id='')
        with pytest.raises(ValidationError):
            ChatRequest(message='test', session_id='x' * 129)

    def test_client_ip_optional(self):
        req = ChatRequest(message='test', client_ip='192.168.1.1')
        assert req.client_ip == '192.168.1.1'


# ═══════════════════════════════════════════════════════════════════════════════
# ChatResponse
# ═══════════════════════════════════════════════════════════════════════════════

class TestChatResponse:
    def test_all_fields(self):
        resp = ChatResponse(
            response='Fine is Rs 5000',
            intent='challan',
            sources=['doc1.txt', 'doc2.txt'],
            session_id='sess-001',
        )
        assert resp.response == 'Fine is Rs 5000'
        assert resp.intent == 'challan'
        assert resp.sources == ['doc1.txt', 'doc2.txt']
        assert resp.session_id == 'sess-001'

    def test_session_id_required(self):
        with pytest.raises(ValidationError):
            ChatResponse(response='Hello')

    def test_default_sources_empty(self):
        resp = ChatResponse(response='Hello', session_id='s1')
        assert resp.sources == []

    def test_intent_optional(self):
        resp = ChatResponse(response='Hi', session_id='s1')
        assert resp.intent is None


# ═══════════════════════════════════════════════════════════════════════════════
# ConversationContext
# ═══════════════════════════════════════════════════════════════════════════════

class TestConversationContext:
    def test_creates_with_all_fields(self):
        ctx = ConversationContext(
            session_id='sess-1',
            message='What is fine?',
            intent='challan',
            lat=12.34,
            lon=56.78,
            client_ip='10.0.0.1',
            history=[{'role': 'user', 'content': 'hi'}],
            retrieved=[RetrievedContext('src', 'title', 'snippet', 0.9)],
            tools=[ToolContext('SosTool', 'Called SOS')],
        )
        assert ctx.session_id == 'sess-1'
        assert ctx.message == 'What is fine?'
        assert ctx.intent == 'challan'
        assert ctx.lat == 12.34
        assert ctx.lon == 56.78
        assert ctx.client_ip == '10.0.0.1'
        assert len(ctx.history) == 1
        assert len(ctx.retrieved) == 1
        assert len(ctx.tools) == 1

    def test_optional_fields_default(self):
        ctx = ConversationContext(session_id='s1', message='Hi', intent='general')
        assert ctx.lat is None
        assert ctx.lon is None
        assert ctx.client_ip is None
        assert ctx.history == []
        assert ctx.retrieved == []
        assert ctx.tools == []

    def test_dataclass_slots(self):
        ctx = ConversationContext('s1', 'Hi', 'general')
        with pytest.raises(AttributeError):
            ctx.__dict__


# ═══════════════════════════════════════════════════════════════════════════════
# RetrievedContext
# ═══════════════════════════════════════════════════════════════════════════════

class TestRetrievedContext:
    def test_creates_with_all_fields(self):
        rc = RetrievedContext(source='doc.txt', title='Doc', snippet='text', score=0.95, category='legal')
        assert rc.source == 'doc.txt'
        assert rc.title == 'Doc'
        assert rc.snippet == 'text'
        assert rc.score == 0.95
        assert rc.category == 'legal'

    def test_category_defaults_to_none(self):
        rc = RetrievedContext(source='doc.txt', title='Doc', snippet='text', score=0.8)
        assert rc.category is None

    def test_dataclass_slots(self):
        rc = RetrievedContext('s', 't', 'sn', 0.5)
        with pytest.raises(AttributeError):
            rc.__dict__


# ═══════════════════════════════════════════════════════════════════════════════
# ToolContext
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolContext:
    def test_creates_with_all_fields(self):
        tc = ToolContext(name='SosTool', summary='Dispatched SOS', payload={'id': 1}, sources=['api'])
        assert tc.name == 'SosTool'
        assert tc.summary == 'Dispatched SOS'
        assert tc.payload == {'id': 1}
        assert tc.sources == ['api']

    def test_optional_fields_default(self):
        tc = ToolContext(name='Tool', summary='Done')
        assert tc.payload is None
        assert tc.sources == []

    def test_dataclass_slots(self):
        tc = ToolContext('n', 's')
        with pytest.raises(AttributeError):
            tc.__dict__
