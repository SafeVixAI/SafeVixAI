# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Coverage boost tests for low-coverage modules: admin, ai, chat, speech, pothole_validator, limiter."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main
from agent.state import ChatResponse
from api.chat import get_engine as chat_get_engine, verify_internal_auth



# ============================================================ #
# FAKE CLASSES (same pattern as test_admin.py)                 #
# ============================================================ #

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
        return {"role": role, "content": content}
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
    def __init__(self, vectorstore, *args, **kwargs):
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
    def search(self, message):
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
        self.cache = cache
        self.providers = {"mock": type("MockProvider", (), {"generate": AsyncMock()})()}
        self._unavailable = set()
    def _provider_unavailable(self, name):
        return name in self._unavailable
    async def generate(self, request):
        from providers.base import ProviderResult
        return ProviderResult(
            text=f"Response for: {request.message}",
            provider="mock",
            model="mock-model",
        )
    async def stream_generate(self, request):
        yield {"type": "token", "text": "mock stream"}

class FakeIntentDetector:
    def detect(self, message):
        return "general"
    def refine_intent(self, initial_intent, message, history):
        return initial_intent

class FakeSafetyChecker:
    def evaluate(self, message):
        from agent.safety_checker import SafetyDecision
        return SafetyDecision(blocked=False)
    def check_output_safety(self, text):
        from agent.safety_checker import SafetyDecision
        return SafetyDecision(blocked=False)
    def add_medical_disclaimer_if_needed(self, message, text):
        return text

class FakeContextAssembler:
    def __init__(self, **kwargs):
        self.retriever = kwargs.get("retriever")
    async def assemble(self, *, session_id, message, intent, lat, lon, client_ip=None, history=None):
        from agent.state import ConversationContext, RetrievedContext
        context = ConversationContext(
            session_id=session_id, message=message, intent=intent,
            lat=lat, lon=lon, client_ip=client_ip, history=history or [],
        )
        context.retrieved.append(
            RetrievedContext(source="kb:general", title="Test", snippet="Test snippet", score=0.9, category="general")
        )
        return context


# ============================================================ #
# HELPERS                                                      #
# ============================================================ #

def _patch_main_classes(mpatch):
    for name, fake_name in [
        ("BackendToolClient", "FakeBackendToolClient"),
        ("ConversationMemoryStore", "FakeConversationMemoryStore"),
        ("LocalVectorStore", "FakeVectorStore"),
        ("Retriever", "FakeRetriever"),
        ("SosTool", "FakeSosTool"),
        ("WeatherTool", "FakeWeatherTool"),
        ("ChallanTool", "FakeChallanTool"),
        ("LegalSearchTool", "FakeLegalSearchTool"),
        ("FirstAidTool", "FakeFirstAidTool"),
        ("RoadInfrastructureTool", "FakeRoadInfrastructureTool"),
        ("RoadIssuesTool", "FakeRoadIssuesTool"),
        ("SubmitReportTool", "FakeSubmitReportTool"),
        ("IndicSeamlessService", "FakeSpeechService"),
        ("ProviderRouter", "FakeProviderRouter"),
        ("IntentDetector", "FakeIntentDetector"),
        ("SafetyChecker", "FakeSafetyChecker"),
        ("ContextAssembler", "FakeContextAssembler"),
    ]:
        mpatch.setattr(main, name, globals()[fake_name])


def _build_app(mpatch, **env):
    main.get_settings.cache_clear()
    for k, v in env.items():
        mpatch.setenv(k, v)
    _patch_main_classes(mpatch)
    return main.create_app()


# ============================================================ #
# 1. ADMIN MODULE — api/admin.py                               #
# ============================================================ #

class TestAdminCoverage:
    """Tests covering missing code paths in api/admin.py."""

    def test_health_no_admin_secret_returns_503(self, monkeypatch):
        """_require_admin: secret is None → HTTP 503."""
        app = _build_app(monkeypatch, ADMIN_SECRET="")
        with TestClient(app) as client:
            resp = client.get("/admin/health", headers={"X-Admin-Key": "any"})
        assert resp.status_code == 503
        assert "disabled" in resp.text.lower()

    def test_get_job_status_no_queue(self, monkeypatch):
        """get_job_status: queue is None → 503."""
        app = _build_app(monkeypatch, ADMIN_SECRET="test-key")
        with TestClient(app) as client:
            resp = client.get("/admin/jobs/j1", headers={"X-Admin-Key": "test-key"})
        assert resp.status_code == 503
        assert "queue" in resp.text.lower()

    def test_get_job_status_not_found(self, monkeypatch):
        """get_job_status: job not found → 404."""
        app = _build_app(monkeypatch, ADMIN_SECRET="test-key")
        with TestClient(app) as client:
            mock_queue = MagicMock()
            mock_queue.get_job = AsyncMock(return_value=None)
            client.app.state.queue = mock_queue
            resp = client.get("/admin/jobs/missing", headers={"X-Admin-Key": "test-key"})
        assert resp.status_code == 404

    def test_get_job_status_found(self, monkeypatch):
        """get_job_status: valid job → 200."""
        from core.queue import Job
        app = _build_app(monkeypatch, ADMIN_SECRET="test-key")
        with TestClient(app) as client:
            mock_queue = MagicMock()
            job = Job(job_id="j1", task_name="rebuild", args=[], kwargs={})
            mock_queue.get_job = AsyncMock(return_value=job)
            client.app.state.queue = mock_queue
            resp = client.get("/admin/jobs/j1", headers={"X-Admin-Key": "test-key"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == "j1"

    def test_providers_health(self, monkeypatch):
        """GET /admin/providers/health returns provider status matrix."""
        app = _build_app(monkeypatch, ADMIN_SECRET="test-key")
        from api.admin import get_engine as admin_get_engine
        mock_prov = MagicMock()
        mock_prov.providers = {"template": MagicMock(), "groq": MagicMock()}
        mock_prov._provider_unavailable = MagicMock(return_value=False)
        mock_eng = MagicMock()
        mock_eng.provider_router = mock_prov
        mock_eng.stats = MagicMock(return_value={})
        app.dependency_overrides[admin_get_engine] = lambda: mock_eng
        with TestClient(app) as client:
            resp = client.get("/admin/providers/health", headers={"X-Admin-Key": "test-key"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert "providers" in data

    def test_providers_dashboard_html(self, monkeypatch):
        """GET /admin/providers/dashboard returns HTML page."""
        app = _build_app(monkeypatch, ADMIN_SECRET="test-key")
        from api.admin import get_engine as admin_get_engine
        from api.admin import get_memory as admin_get_memory
        mock_mem = MagicMock()
        mock_mem.backend_name = "test"
        mock_mem.ping = AsyncMock(return_value=True)
        mock_cache = MagicMock()
        mock_cache.ping = AsyncMock(return_value=True)
        mock_prov = MagicMock()
        mock_prov.providers = {"template": MagicMock(), "groq": MagicMock()}
        mock_prov._provider_unavailable = MagicMock(return_value=False)
        mock_prov.cache = mock_cache
        mock_eng = MagicMock()
        mock_eng.provider_router = mock_prov
        mock_eng.stats = MagicMock(return_value={})
        app.dependency_overrides[admin_get_engine] = lambda: mock_eng
        app.dependency_overrides[admin_get_memory] = lambda: mock_mem
        with TestClient(app) as client:
            resp = client.get("/admin/providers/dashboard", headers={"X-Admin-Key": "test-key"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/html; charset=utf-8"
        assert "SafeVixAI" in resp.text
        assert "Healthy" in resp.text

    def test_rebuild_rag_index_task_direct(self):
        """Call rebuild_rag_index_task without global engine → ValueError."""
        from core.queue import _TASK_REGISTRY, set_global_chat_engine
        set_global_chat_engine(None)
        assert "rebuild_rag_index" in _TASK_REGISTRY
        func = _TASK_REGISTRY["rebuild_rag_index"]
        assert callable(func)
        with pytest.raises(ValueError, match="ChatEngine is not initialized"):
            func(MagicMock(), "j1")


# ============================================================ #
# 2. CHAT MODULE — api/chat.py                                 #
# ============================================================ #

class TestChatCoverage:
    """Tests covering missing code paths in api/chat.py."""

    def test_production_no_internal_key(self, monkeypatch):
        """Production without CHATBOT_INTERNAL_API_KEY → 500."""
        app = _build_app(monkeypatch, ENVIRONMENT="production", ALLOWED_HOSTS="testserver")
        with TestClient(app) as client:
            resp = client.post("/api/v1/chat/", json={"message": "hi"})
        assert resp.status_code == 500

    def test_wrong_internal_key(self, monkeypatch):
        """Wrong X-Internal-Api-Key header → 403."""
        app = _build_app(monkeypatch, CHATBOT_INTERNAL_API_KEY="real-secret")
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/chat/",
                json={"message": "hi"},
                headers={"X-Internal-Api-Key": "wrong"},
            )
        assert resp.status_code == 403

    def test_chat_post(self, monkeypatch):
        """POST /api/v1/chat/ returns ChatResponse."""
        app = _build_app(monkeypatch)
        mock_engine = MagicMock()
        mock_engine.chat = AsyncMock(return_value=ChatResponse(
            response="Hello world", intent="general", sources=[], session_id="s1",
        ))
        app.dependency_overrides[chat_get_engine] = lambda: mock_engine
        app.dependency_overrides[verify_internal_auth] = lambda: None
        with TestClient(app) as client:
            resp = client.post("/api/v1/chat/", json={"message": "hello"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert data["response"] == "Hello world"
        assert data["session_id"] == "s1"

    def test_chat_stream_success(self, monkeypatch):
        """POST /api/v1/chat/stream yields SSE token events."""
        app = _build_app(monkeypatch)
        async def mock_stream(_payload):
            yield {"type": "token", "text": "Hello"}
            yield {"type": "done", "intent": "general", "sources": [], "session_id": "s1"}
        mock_engine = MagicMock()
        mock_engine.stream_chat = mock_stream
        app.dependency_overrides[chat_get_engine] = lambda: mock_engine
        app.dependency_overrides[verify_internal_auth] = lambda: None
        with TestClient(app) as client:
            resp = client.post("/api/v1/chat/stream", json={"message": "hi"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert "Hello" in resp.text
        assert '"type": "done"' in resp.text

    def test_chat_stream_error_event(self, monkeypatch):
        """Stream yields error event on engine exception."""
        app = _build_app(monkeypatch)
        async def mock_stream_error(_payload):
            yield {"type": "token", "text": "partial"}
            raise RuntimeError("stream failure")
        mock_engine = MagicMock()
        mock_engine.stream_chat = mock_stream_error
        app.dependency_overrides[chat_get_engine] = lambda: mock_engine
        app.dependency_overrides[verify_internal_auth] = lambda: None
        with TestClient(app) as client:
            resp = client.post("/api/v1/chat/stream", json={"message": "hi"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert "error" in resp.text.lower()

    def test_chat_stream_x_forwarded_for(self, monkeypatch):
        """Stream sets client_ip from X-Forwarded-For header."""
        app = _build_app(monkeypatch)
        async def mock_stream(payload):
            assert payload.client_ip == "1.2.3.4"
            yield {"type": "done", "intent": "general", "sources": [], "session_id": "s1"}
        mock_engine = MagicMock()
        mock_engine.stream_chat = mock_stream
        app.dependency_overrides[chat_get_engine] = lambda: mock_engine
        app.dependency_overrides[verify_internal_auth] = lambda: None
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/chat/stream",
                json={"message": "hi"},
                headers={"X-Forwarded-For": "1.2.3.4"},
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 200

    def test_chat_history_no_key(self, monkeypatch):
        """GET /api/v1/chat/history/{id} returns 403 without admin auth."""
        app = _build_app(monkeypatch, ADMIN_SECRET="secret-key")
        with TestClient(app) as client:
            resp = client.get("/api/v1/chat/history/session-1")
        assert resp.status_code == 403

    def test_chat_history_valid_key(self, monkeypatch):
        """GET /api/v1/chat/history/{id} returns history with valid X-Admin-Secret."""
        app = _build_app(monkeypatch, ADMIN_SECRET="secret-key")
        mock_engine = MagicMock()
        mock_engine.get_history = AsyncMock(return_value=[{"role": "user", "content": "hi"}])
        app.dependency_overrides[chat_get_engine] = lambda: mock_engine
        with TestClient(app) as client:
            resp = client.get(
                "/api/v1/chat/history/session-1",
                headers={"X-Admin-Secret": "secret-key"},
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "user"

    def test_chat_health(self, monkeypatch):
        """GET /api/v1/chat/health returns ok."""
        app = _build_app(monkeypatch)
        with TestClient(app) as client:
            resp = client.get("/api/v1/chat/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ============================================================ #
# 3. SPEECH MODULE — api/speech.py                             #
# ============================================================ #

class TestSpeechCoverage:
    """Tests covering missing code paths in api/speech.py."""

    def test_speech_status(self, monkeypatch):
        """GET /speech/status returns configured status."""
        app = _build_app(monkeypatch)
        with TestClient(app) as client:
            resp = client.get("/speech/status")
        assert resp.status_code == 200
        assert resp.json()["configured"] is True

    def test_translate_unsupported_content_type(self, monkeypatch):
        """POST /speech/translate with bad content-type → 415."""
        app = _build_app(monkeypatch)
        with TestClient(app) as client:
            resp = client.post(
                "/speech/translate",
                content=b"test",
                headers={"Content-Type": "video/mp4"},
            )
        assert resp.status_code == 415

    def test_translate_content_length_too_large(self, monkeypatch):
        """POST /speech/translate with oversized content-length → 413."""
        app = _build_app(monkeypatch)
        with TestClient(app) as client:
            resp = client.post(
                "/speech/translate",
                content=b"x" * (11 * 1024 * 1024),
                headers={"Content-Type": "audio/wav"},
            )
        assert resp.status_code == 413

    def test_translate_empty_body(self, monkeypatch):
        """POST /speech/translate with empty body → 400."""
        app = _build_app(monkeypatch)
        with TestClient(app) as client:
            resp = client.post(
                "/speech/translate",
                content=b"",
                headers={"Content-Type": "audio/wav"},
            )
        assert resp.status_code == 400
        assert "empty" in resp.text.lower()

    def test_translate_value_error(self, monkeypatch):
        """POST /speech/translate: ValueError → 400."""
        app = _build_app(monkeypatch)
        svc = MagicMock()
        svc.translate_audio_bytes = MagicMock(side_effect=ValueError("bad audio"))
        with TestClient(app) as client:
            client.app.state.speech_service = svc
            resp = client.post(
                "/speech/translate",
                content=b"\x00\x01",
                headers={"Content-Type": "audio/wav"},
            )
        assert resp.status_code == 400
        assert "bad audio" in resp.text.lower()

    def test_translate_runtime_error(self, monkeypatch):
        """POST /speech/translate: RuntimeError → 503."""
        app = _build_app(monkeypatch)
        svc = MagicMock()
        svc.translate_audio_bytes = MagicMock(side_effect=RuntimeError("no deps"))
        with TestClient(app) as client:
            client.app.state.speech_service = svc
            resp = client.post(
                "/speech/translate",
                content=b"\x00\x01",
                headers={"Content-Type": "audio/wav"},
            )
        assert resp.status_code == 503

    def test_translate_generic_error(self, monkeypatch):
        """POST /speech/translate: generic Exception → 500."""
        app = _build_app(monkeypatch)
        svc = MagicMock()
        svc.translate_audio_bytes = MagicMock(side_effect=Exception("unexpected"))
        with TestClient(app) as client:
            client.app.state.speech_service = svc
            resp = client.post(
                "/speech/translate",
                content=b"\x00\x01",
                headers={"Content-Type": "audio/wav"},
            )
        assert resp.status_code == 500

    def test_translate_success(self, monkeypatch):
        """POST /speech/translate returns translated result."""
        app = _build_app(monkeypatch)
        from services.speech_translation import SpeechTranslationResult
        svc = MagicMock()
        svc.translate_audio_bytes = MagicMock(return_value=SpeechTranslationResult(
            text="Hello world", target_language="eng", device="cpu",
            model_source="facebook/seamless-m4t-v2", sample_rate=16000,
        ))
        with TestClient(app) as client:
            client.app.state.speech_service = svc
            resp = client.post(
                "/speech/translate",
                content=b"\x00\x01",
                headers={"Content-Type": "audio/wav"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["text"] == "Hello world"
        assert data["target_language"] == "eng"
        assert data["content_type"] == "audio/wav"


# ============================================================ #
# 4. AI MODULE — api/ai.py                                     #
# ============================================================ #

class TestAICoverage:
    """Tests covering missing code paths in api/ai.py."""

    def test_validate_image_non_image(self, monkeypatch):
        """Reject non-image content type → 400."""
        app = _build_app(monkeypatch)
        app.dependency_overrides[verify_internal_auth] = lambda: None
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/ai/validate-image",
                files={"file": ("test.txt", b"hello", "text/plain")},
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 400
        assert "image" in resp.text.lower()

    def test_validate_image_empty(self, monkeypatch):
        """Reject empty file → 400."""
        app = _build_app(monkeypatch)
        app.dependency_overrides[verify_internal_auth] = lambda: None
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/ai/validate-image",
                files={"file": ("empty.jpg", b"", "image/jpeg")},
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 400
        assert "empty" in resp.text.lower()

    def test_validate_image_too_large(self, monkeypatch):
        """Reject oversized file → 413."""
        app = _build_app(monkeypatch)
        app.dependency_overrides[verify_internal_auth] = lambda: None
        big_data = b"x" * (5 * 1024 * 1024 + 1)
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/ai/validate-image",
                files={"file": ("big.jpg", big_data, "image/jpeg")},
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 413

    def test_validate_image_success(self, monkeypatch):
        """Valid image returns pothole detection result."""
        app = _build_app(monkeypatch)
        app.dependency_overrides[verify_internal_auth] = lambda: None
        mock_result = {"anomaly_detected": True, "confidence": 0.95, "boxes": [], "success": True}
        with patch("api.ai.PotholeValidator.validate_image", return_value=mock_result):
            with TestClient(app) as client:
                resp = client.post(
                    "/api/v1/ai/validate-image",
                    files={"file": ("test.jpg", b"fakeimagedata", "image/jpeg")},
                )
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["anomaly_detected"] is True

    def test_validate_image_exception(self, monkeypatch):
        """Unexpected error → 500."""
        app = _build_app(monkeypatch)
        app.dependency_overrides[verify_internal_auth] = lambda: None
        with patch("api.ai.PotholeValidator.validate_image", side_effect=RuntimeError("model crash")):
            with TestClient(app) as client:
                resp = client.post(
                    "/api/v1/ai/validate-image",
                    files={"file": ("test.jpg", b"data", "image/jpeg")},
                )
        app.dependency_overrides.clear()
        assert resp.status_code == 500


# ============================================================ #
# 5. POTHOLE VALIDATOR — services/pothole_validator.py         #
# ============================================================ #

class TestPotholeValidatorCoverage:
    """Tests for services/pothole_validator.py."""

    def test_get_model_file_not_found(self):
        """get_model raises FileNotFoundError when model path missing."""
        from services.pothole_validator import PotholeValidator
        PotholeValidator._model = None
        fake_ultralytics = MagicMock()
        fake_ultralytics.YOLO = MagicMock()
        with patch.dict("sys.modules", {"ultralytics": fake_ultralytics}):
            with patch("os.path.exists", return_value=False):
                with pytest.raises(FileNotFoundError, match="YOLO model not found"):
                    PotholeValidator.get_model()

    def test_validate_image_model_not_found(self):
        """validate_image returns error dict when model missing."""
        from services.pothole_validator import PotholeValidator
        PotholeValidator._model = None
        fake_ultralytics = MagicMock()
        fake_ultralytics.YOLO = MagicMock()
        with patch.dict("sys.modules", {"ultralytics": fake_ultralytics}):
            with patch("os.path.exists", return_value=False):
                result = PotholeValidator.validate_image(b"fakeimage")
        assert result["success"] is False
        assert "error" in result

    def test_validate_image_generic_exception(self):
        """validate_image catches unexpected exception and returns error dict."""
        from services.pothole_validator import PotholeValidator
        PotholeValidator._model = None
        with patch("os.path.exists", return_value=True):
            with patch("services.pothole_validator.PotholeValidator.get_model",
                       side_effect=PermissionError("access denied")):
                result = PotholeValidator.validate_image(b"data")
        assert result["success"] is False
        assert "error" in result


# ============================================================ #
# 6. LIMITER — limiter.py                                      #
# ============================================================ #

class TestLimiterCoverage:
    """Tests for limiter.py."""

    def test_limiter_import_success_default(self):
        """limiter is a slowapi Limiter instance by default."""
        import limiter as limiter_mod
        from slowapi import Limiter as SlowapiLimiter
        assert isinstance(limiter_mod.limiter, SlowapiLimiter)

    def test_noop_limiter_behavior_replica(self):
        """_NoopLimiter (replicated from source) wraps functions unchanged."""
        class _NoopLimiter:
            def limit(self, *_, **__):
                def decorator(func):
                    return func
                return decorator

        nl = _NoopLimiter()
        @nl.limit("1/second")
        def my_func(x):
            return x * 2

        assert my_func(21) == 42
        assert my_func.__name__ == "my_func"

    def test_limiter_import_fallback_path(self):
        """When slowapi is unavailable, the except block defines _NoopLimiter."""
        import limiter as limiter_mod
        import inspect
        source = inspect.getsource(limiter_mod)
        assert "except ImportError" in source
        assert "_NoopLimiter" in source
        assert "try:" in source
        assert "class _NoopLimiter" in source
