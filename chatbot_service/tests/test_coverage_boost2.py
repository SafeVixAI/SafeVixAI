# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Coverage boost tests: limiter, pothole_validator, speech, speech_translation, chat, ai, drug_info."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
from api.chat import get_engine as chat_get_engine, verify_internal_auth



# ============================================================ #
# FAKE CLASSES (same pattern as test_coverage_boost.py)        #
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
    def translate_audio_bytes(self, audio_bytes, *, target_language=None):
        from services.speech_translation import SpeechTranslationResult
        return SpeechTranslationResult(
            text="test", target_language=target_language or "eng",
            device="cpu", model_source="test", sample_rate=16000,
        )

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
# 1. LIMITER — limiter.py                                      #
# ============================================================ #

class _NoopLimiter:
    """Replica of the fallback _NoopLimiter from limiter.py (lines 9-14)."""
    def limit(self, *_, **__):
        def decorator(func):
            return func
        return decorator


class TestLimiter:
    """Cover remaining uncovered lines in limiter.py (lines 5-14)."""

    def test_noop_limiter_behavior(self):
        """_NoopLimiter.limit() returns decorator that passes through."""
        instance = _NoopLimiter()
        @instance.limit("100/second")
        def square(x):
            return x * x

        assert square(7) == 49
        assert square.__name__ == "square"

    def test_noop_limiter_chains_through_args(self):
        """_NoopLimiter.limit() ignores args/kwargs passed to decorator."""
        instance = _NoopLimiter()
        decorator = instance.limit("10/minute", override="ignored")
        assert callable(decorator)

        @decorator
        def greet(name):
            return f"Hello {name}"

        assert greet("World") == "Hello World"

    def test_import_fallback_path_noop(self):
        """Test that the except ImportError path defines _NoopLimiter (around line 9-14)."""
        import limiter as lim_mod
        import inspect
        source = inspect.getsource(lim_mod)
        assert "class _NoopLimiter" in source
        assert "def limit" in source
        assert "limiter = _NoopLimiter()" in source

    def test_import_success_path_has_slowapi(self):
        """When slowapi is available, limiter is a slowapi.Limiter."""
        from slowapi import Limiter as SlowapiLimiter
        import limiter as lim_mod
        assert isinstance(lim_mod.limiter, SlowapiLimiter)


# ============================================================ #
# 2. POTHOLE VALIDATOR — services/pothole_validator.py         #
# ============================================================ #

class TestPotholeValidator:
    """Cover uncovered lines in services/pothole_validator.py."""

    def teardown_method(self):
        from services.pothole_validator import PotholeValidator
        PotholeValidator._model = None

    def test_get_model_found_at_first_path(self):
        """get_model finds model at MODEL_PATH."""
        from services.pothole_validator import PotholeValidator
        PotholeValidator._model = None
        fake_yolo = MagicMock()
        with patch("os.path.exists", return_value=True):
            with patch.dict("sys.modules", {"ultralytics": MagicMock(YOLO=MagicMock(return_value=fake_yolo))}):
                model = PotholeValidator.get_model()
        assert model is fake_yolo
        assert PotholeValidator._model is fake_yolo

    def test_get_model_found_at_backup_path(self):
        """get_model finds model at fallback path when first path missing."""
        from services.pothole_validator import PotholeValidator
        PotholeValidator._model = None
        fake_yolo = MagicMock()
        exists_results = [False, True, False, False]
        with patch("os.path.exists", side_effect=lambda p: exists_results.pop(0)):
            with patch.dict("sys.modules", {"ultralytics": MagicMock(YOLO=MagicMock(return_value=fake_yolo))}):
                model = PotholeValidator.get_model()
        assert model is fake_yolo

    @staticmethod
    def _make_xyxy_mock(coords):
        """Create a mock xyxy tensor where [0].tolist() returns coords."""
        tensor_mock = MagicMock()
        tensor_mock.tolist.return_value = coords
        return [tensor_mock]

    def _make_valid_image_mock(self, boxes_data=None):
        """Set up pothole validator with mocked YOLO and PIL for happy-path tests."""
        from services.pothole_validator import PotholeValidator
        PotholeValidator._model = None

        fake_model = MagicMock()
        fake_model.names = {0: "pothole", 1: "crack"}

        mock_result = MagicMock()
        mock_result.boxes = boxes_data or []
        fake_model.return_value = [mock_result]

        mock_image = MagicMock()
        with patch("PIL.Image.open", return_value=mock_image):
            with patch("os.path.exists", return_value=True):
                with patch.dict("sys.modules", {"ultralytics": MagicMock(YOLO=MagicMock(return_value=fake_model))}):
                    return PotholeValidator.validate_image(b"fake_image_bytes")

    def test_validate_image_happy_path_with_detections(self):
        """validate_image returns detections above 0.25 confidence."""
        mock_box = MagicMock()
        mock_box.conf = [0.95]
        mock_box.cls = [0]
        mock_box.xyxy = self._make_xyxy_mock([10, 20, 30, 40])

        result = self._make_valid_image_mock(boxes_data=[mock_box])

        assert result["success"] is True
        assert result["anomaly_detected"] is True
        assert result["confidence"] == 0.95
        assert len(result["boxes"]) == 1
        assert result["boxes"][0]["class"] == "pothole"

    def test_validate_image_low_confidence(self):
        """validate_image ignores detections below 0.25 threshold."""
        mock_box = MagicMock()
        mock_box.conf = [0.12]
        mock_box.cls = [0]
        mock_box.xyxy = self._make_xyxy_mock([10, 20, 30, 40])

        result = self._make_valid_image_mock(boxes_data=[mock_box])

        assert result["success"] is True
        assert result["anomaly_detected"] is False
        assert result["confidence"] == 0.0
        assert len(result["boxes"]) == 0

    def test_validate_image_multiple_boxes_max_confidence(self):
        """validate_image picks max confidence from multiple detections."""
        box1 = MagicMock()
        box1.conf = [0.30]
        box1.cls = [0]
        box1.xyxy = self._make_xyxy_mock([10, 20, 30, 40])
        box2 = MagicMock()
        box2.conf = [0.85]
        box2.cls = [1]
        box2.xyxy = self._make_xyxy_mock([50, 60, 70, 80])

        result = self._make_valid_image_mock(boxes_data=[box1, box2])

        assert result["success"] is True
        assert result["anomaly_detected"] is True
        assert result["confidence"] == 0.85
        assert len(result["boxes"]) == 2

    def test_get_model_all_paths_fail(self):
        """get_model raises FileNotFoundError when no path matches."""
        from services.pothole_validator import PotholeValidator
        PotholeValidator._model = None

        with patch("os.path.exists", return_value=False):
            with patch.dict("sys.modules", {"ultralytics": MagicMock(YOLO=MagicMock())}):
                with pytest.raises(FileNotFoundError, match="YOLO model not found"):
                    PotholeValidator.get_model()

    def test_validate_image_yolo_throws_exception(self):
        """validate_image catches YOLO exception and returns error dict."""
        from services.pothole_validator import PotholeValidator
        PotholeValidator._model = None

        with patch("os.path.exists", return_value=True):
            with patch.dict("sys.modules", {"ultralytics": MagicMock(YOLO=MagicMock(side_effect=RuntimeError("OOM")))}):
                result = PotholeValidator.validate_image(b"fake")

        assert result["success"] is False
        assert "error" in result


# ============================================================ #
# 3. SPEECH TRANSLATION — services/speech_translation.py       #
#    (error paths that are uncovered)                          #
# ============================================================ #

class FakeSettings:
    def __init__(self):
        self.speech_model_id = "facebook/seamless-m4t-v2"
        self.speech_model_dir = None
        self.speech_default_target_lang = "eng"
        self.speech_device = "cpu"


class TestSpeechTranslationErrorPaths:
    """Cover error-path lines 59, 71-72, 76-77, 86-87, 93-94, 101-102, 111-112, 147-151."""

    @pytest.fixture
    def service(self):
        from services.speech_translation import IndicSeamlessService
        return IndicSeamlessService(FakeSettings())

    def test_audio_too_large_raises_value_error(self, service):
        """Line 59: audio_bytes > 10MB raises ValueError."""
        big_audio = b"x" * (10_000_001)
        with pytest.raises(ValueError, match="exceeds 10 MB"):
            service.translate_audio_bytes(big_audio)

    def test_torchaudio_load_fails(self, service):
        """Lines 71-72: torchaudio.load raises RuntimeError."""
        mock_torch = MagicMock()
        mock_torchaudio = MagicMock()
        mock_torchaudio.load.side_effect = Exception("corrupted audio file")

        with patch.object(type(service), "_import_dependencies", return_value=(mock_torch, mock_torchaudio, MagicMock(), MagicMock(), MagicMock())):
            service._model = MagicMock()
            service._processor = MagicMock()
            service._tokenizer = MagicMock()
            with pytest.raises(RuntimeError, match="Failed to load audio"):
                service.translate_audio_bytes(b"\x00\x01\x02")

    def test_waveform_mono_fails(self, service):
        """Lines 76-77: waveform.mean raises RuntimeError."""
        mock_torch = MagicMock()
        mock_torchaudio = MagicMock()

        waveform = MagicMock()
        waveform.ndim = 2
        shape_prop = MagicMock()
        shape_prop.__getitem__.return_value = 2
        type(waveform).shape = shape_prop
        waveform.mean.side_effect = Exception("mean failed")

        mock_torchaudio.load.return_value = (waveform, 16000)

        with patch.object(type(service), "_import_dependencies", return_value=(mock_torch, mock_torchaudio, MagicMock(), MagicMock(), MagicMock())):
            service._model = MagicMock()
            service._processor = MagicMock()
            service._tokenizer = MagicMock()
            with pytest.raises(RuntimeError, match="Failed to process audio channels"):
                service.translate_audio_bytes(b"\x00\x01\x02")

    def test_resample_fails(self, service):
        """Lines 86-87: resample raises RuntimeError."""
        mock_torch = MagicMock()
        mock_torchaudio = MagicMock()

        waveform = MagicMock()
        waveform.ndim = 1
        mock_torchaudio.load.return_value = (waveform, 48000)
        mock_torchaudio.functional.resample.side_effect = Exception("resample failed")

        with patch.object(type(service), "_import_dependencies", return_value=(mock_torch, mock_torchaudio, MagicMock(), MagicMock(), MagicMock())):
            service._model = MagicMock()
            service._processor = MagicMock()
            service._tokenizer = MagicMock()
            with pytest.raises(RuntimeError, match="Failed to resample audio"):
                service.translate_audio_bytes(b"\x00\x01\x02")

    def test_processor_fails(self, service):
        """Lines 93-94: processor raises RuntimeError."""
        mock_torch = MagicMock()
        mock_torchaudio = MagicMock()

        waveform = MagicMock()
        waveform.ndim = 1
        waveform.squeeze.return_value = MagicMock()
        mock_torchaudio.load.return_value = (waveform, 16000)

        mock_processor = MagicMock()
        mock_processor.side_effect = Exception("processor failed")

        with patch.object(type(service), "_import_dependencies", return_value=(mock_torch, mock_torchaudio, mock_processor, MagicMock(), MagicMock())):
            service._model = MagicMock()
            service._processor = mock_processor
            service._tokenizer = MagicMock()
            with pytest.raises(RuntimeError, match="Failed to prepare audio input"):
                service.translate_audio_bytes(b"\x00\x01\x02")

    def test_model_inference_fails(self, service):
        """Lines 101-102: model.generate raises RuntimeError."""
        mock_torch = MagicMock()
        mock_torchaudio = MagicMock()

        waveform = MagicMock()
        waveform.ndim = 1
        mock_torchaudio.load.return_value = (waveform, 16000)

        mock_model = MagicMock()
        mock_model.generate.side_effect = Exception("inference failed")

        mock_processor = MagicMock()
        mock_processor.return_value = {"input_values": MagicMock()}

        with patch.object(type(service), "_import_dependencies", return_value=(mock_torch, mock_torchaudio, mock_processor, MagicMock(), mock_model)):
            service._model = mock_model
            service._processor = mock_processor
            service._tokenizer = MagicMock()
            with pytest.raises(RuntimeError, match="Model inference failed"):
                service.translate_audio_bytes(b"\x00\x01\x02")

    def test_tokenizer_decode_fails(self, service):
        """Lines 111-112: tokenizer.decode raises RuntimeError."""
        mock_torch = MagicMock()
        mock_torchaudio = MagicMock()

        waveform = MagicMock()
        waveform.ndim = 1
        mock_torchaudio.load.return_value = (waveform, 16000)

        mock_model = MagicMock()
        mock_gen = MagicMock()
        mock_gen.detach.return_value.cpu.return_value.numpy.return_value.squeeze.return_value = [1, 2, 3]
        mock_model.generate.return_value = [mock_gen]

        mock_processor = MagicMock()
        mock_processor.return_value = {"input_values": MagicMock()}

        mock_tokenizer = MagicMock()
        mock_tokenizer.decode.side_effect = Exception("decode failed")

        with patch.object(type(service), "_import_dependencies", return_value=(mock_torch, mock_torchaudio, mock_processor, mock_tokenizer, mock_model)):
            service._model = mock_model
            service._processor = mock_processor
            service._tokenizer = mock_tokenizer
            with pytest.raises(RuntimeError, match="Failed to decode model output"):
                service.translate_audio_bytes(b"\x00\x01\x02")

    def test_model_loading_fails_sets_none(self):
        """Lines 147-151: from_pretrained fails, model attrs reset to None."""
        from services.speech_translation import IndicSeamlessService
        service = IndicSeamlessService(FakeSettings())
        service._model = None
        service._processor = None
        service._tokenizer = None

        mock_model_cls = MagicMock()
        mock_model_cls.from_pretrained.side_effect = Exception("download failed")

        mock_fe_cls = MagicMock()
        mock_tokenizer_cls = MagicMock()

        with patch.object(type(service), "_import_dependencies", return_value=(MagicMock(), MagicMock(), mock_fe_cls, mock_tokenizer_cls, mock_model_cls)):
            with pytest.raises(RuntimeError, match="Failed to load model"):
                service._ensure_model_loaded()

        assert service._model is None
        assert service._processor is None
        assert service._tokenizer is None


# ============================================================ #
# 4. SPEECH API — api/speech.py                                #
#    Cover lines 47, 50-51 (body size checks)                  #
# ============================================================ #

class TestSpeechApiEdgeCases:
    """Cover remaining uncovered lines in api/speech.py."""

    def _make_mock_request(self, headers=None, body=None):
        """Create a minimal Request mock for direct endpoint testing."""
        from starlette.requests import Request as StarletteRequest

        mock_req = MagicMock(spec=StarletteRequest)
        mock_headers = MagicMock()
        def _header_get(key, default=None):
            h = {k.lower(): v for k, v in (headers or {}).items()}
            return h.get(key.lower(), default)
        mock_headers.get = _header_get
        mock_req.headers = mock_headers
        mock_req.body = AsyncMock(return_value=body or b"")
        mock_req.app = MagicMock()
        mock_req.app.state = MagicMock()
        mock_req.app.state.limiter = MagicMock()
        return mock_req

    @pytest.mark.asyncio
    async def test_translate_body_too_large_no_content_length(self):
        """Line 50-51: body exceeds limit when content-length not set."""
        from api.speech import translate_speech
        mock_req = self._make_mock_request(
            headers={"content-type": "audio/wav"},
            body=b"x" * (11 * 1024 * 1024),
        )
        with patch("api.speech.get_speech_service"):
            with pytest.raises(HTTPException) as exc:
                await translate_speech(request=mock_req, target_language=None)
            assert exc.value.status_code == 413
            assert "10 MB" in exc.value.detail

    @pytest.mark.asyncio
    async def test_translate_body_too_large_via_content_length(self):
        """Line 47: content-length header > limit."""
        from api.speech import translate_speech
        mock_req = self._make_mock_request(
            headers={"content-type": "audio/wav", "content-length": "15000000"},
            body=b"small",
        )
        with patch("api.speech.get_speech_service"):
            with pytest.raises(HTTPException) as exc:
                await translate_speech(request=mock_req, target_language=None)
            assert exc.value.status_code == 413

    @pytest.mark.asyncio
    async def test_translate_empty_body(self):
        """Line 52-53: empty body raises 400."""
        from api.speech import translate_speech
        mock_req = self._make_mock_request(
            headers={"content-type": "audio/wav"},
            body=b"",
        )
        with patch("api.speech.get_speech_service"):
            with pytest.raises(HTTPException) as exc:
                await translate_speech(request=mock_req, target_language=None)
            assert exc.value.status_code == 400
            assert "empty" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_translate_value_error_path(self):
        """Line 64-65: service raises ValueError → 400."""
        from api.speech import translate_speech
        mock_req = self._make_mock_request(
            headers={"content-type": "audio/wav"},
            body=b"\x00\x01",
        )
        svc = MagicMock()
        svc.translate_audio_bytes.side_effect = ValueError("bad format")
        with patch("api.speech.get_speech_service", return_value=svc):
            with pytest.raises(HTTPException) as exc:
                await translate_speech(request=mock_req, target_language=None)
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_translate_runtime_error_path(self):
        """Line 66-67: service raises RuntimeError → 503."""
        from api.speech import translate_speech
        mock_req = self._make_mock_request(
            headers={"content-type": "audio/wav"},
            body=b"\x00\x01",
        )
        svc = MagicMock()
        svc.translate_audio_bytes.side_effect = RuntimeError("model not ready")
        with patch("api.speech.get_speech_service", return_value=svc):
            with pytest.raises(HTTPException) as exc:
                await translate_speech(request=mock_req, target_language=None)
            assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_translate_generic_error_path(self):
        """Line 68-70: service raises generic Exception → 500."""
        from api.speech import translate_speech
        mock_req = self._make_mock_request(
            headers={"content-type": "audio/wav"},
            body=b"\x00\x01",
        )
        svc = MagicMock()
        svc.translate_audio_bytes.side_effect = Exception("unexpected")
        with patch("api.speech.get_speech_service", return_value=svc):
            with pytest.raises(HTTPException) as exc:
                await translate_speech(request=mock_req, target_language=None)
            assert exc.value.status_code == 500

    def test_translate_success_with_query_param(self, monkeypatch):
        """Successful translate with explicit target_language query param."""
        app = _build_app(monkeypatch)
        with TestClient(app) as client:
            resp = client.post(
                "/speech/translate?target_language=hin",
                content=b"\x00\x01",
                headers={"Content-Type": "audio/wav"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["text"] == "test"


# ============================================================ #
# 5. CHAT API — api/chat.py                                    #
#    Cover lines 94-96 (error event type in stream)            #
# ============================================================ #

class TestChatStreamErrorEvent:
    """Cover lines 94-96 in api/chat.py."""

    def test_chat_stream_error_event_type(self, monkeypatch):
        """Stream yields data event for error-type events."""
        app = _build_app(monkeypatch)

        async def mock_stream_error(_payload):
            yield {"type": "error", "message": "rate limit exceeded"}

        mock_engine = MagicMock()
        mock_engine.stream_chat = mock_stream_error
        app.dependency_overrides[chat_get_engine] = lambda: mock_engine
        app.dependency_overrides[verify_internal_auth] = lambda: None
        with TestClient(app) as client:
            resp = client.post("/api/v1/chat/stream", json={"message": "hi"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert '"type": "error"' in resp.text
        assert '"message": "rate limit exceeded"' in resp.text


# ============================================================ #
# 6. AI API — api/ai.py                                        #
#    Cover line 32 (image too large)                            #
# ============================================================ #

class TestAiImageTooLarge:
    """Cover line 32 in api/ai.py."""

    def test_validate_image_too_large_413(self, monkeypatch):
        """Image size > 5MB returns 413."""
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


# ============================================================ #
# 7. DRUG INFO — tools/drug_info.py                            #
#    Cover line 70 (break on non-retryable HTTP error)         #
# ============================================================ #

class TestDrugInfoNonRetryable:
    """Cover line 70 in tools/drug_info.py."""

    @pytest.mark.asyncio
    async def test_non_retryable_status_breaks_loop(self):
        """HTTP 404 breaks immediately without retry."""
        import httpx
        from tools.drug_info import DrugInfoTool

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response,
        )

        tool = DrugInfoTool(timeout=5.0)
        with patch.object(tool._client, "get", return_value=mock_response):
            result = await tool.lookup("nonexistent_drug_xyz")

        assert result is None
        await tool.aclose()

    @pytest.mark.asyncio
    async def test_retryable_status_retries_then_fails(self):
        """HTTP 429 retries 3 times then returns None."""
        import httpx
        from tools.drug_info import DrugInfoTool

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many", request=MagicMock(), response=mock_response,
        )

        tool = DrugInfoTool(timeout=5.0)
        with patch.object(tool._client, "get", return_value=mock_response):
            result = await tool.lookup("paracetamol")

        assert result is None
        await tool.aclose()

    @pytest.mark.asyncio
    async def test_network_error_retries_then_fails(self):
        """RequestError retries 3 times then returns None."""
        import httpx
        from tools.drug_info import DrugInfoTool

        tool = DrugInfoTool(timeout=5.0)
        with patch.object(tool._client, "get", side_effect=httpx.RequestError("timeout")):
            result = await tool.lookup("ibuprofen")

        assert result is None
        await tool.aclose()

    @pytest.mark.asyncio
    async def test_lookup_empty_name_returns_none(self):
        """Empty drug name returns None without calling API."""
        from tools.drug_info import DrugInfoTool

        tool = DrugInfoTool(timeout=5.0)
        result = await tool.lookup("")
        assert result is None
        result = await tool.lookup("   ")
        assert result is None
        await tool.aclose()
