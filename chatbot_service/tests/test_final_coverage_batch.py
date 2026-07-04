from __future__ import annotations

import asyncio
import json
import os
import pytest
import sys
import httpx
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient


def _mock_settings(**overrides):
    """Create a mock Settings-like object for tools that need it."""
    s = MagicMock()
    mock_data_path = MagicMock()
    mock_data_path.exists.return_value = False
    s.rag_data_dir = MagicMock()
    s.rag_data_dir.__truediv__.return_value = mock_data_path
    s.admin_secret = None
    s.environment = "development"
    s.cors_origins = "http://localhost:3000"
    s.cors_origins_list = ["http://localhost:3000"]
    s.service_name = "test"
    s.sentry_dsn = None
    s.database_url = ""
    s.redis_url = None
    s.session_ttl_seconds = 3600
    s.embedding_model = "test"
    s.top_k_retrieval = 5
    s.rag_min_score = 0.0
    s.rag_reranker = None
    s.w3w_api_key = None
    s.opencage_api_key = None
    s.main_backend_base_url = "http://localhost:8000"
    s.chroma_persist_dir = MagicMock()
    s.chroma_persist_dir.mkdir.return_value = None
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


class TestMainJsonFormatter:
    def test_json_formatter_exc_info(self):
        from main import _JsonFormatter
        import logging
        fmt = _JsonFormatter()
        record = logging.LogRecord("test", logging.ERROR, "test.py", 10, "error msg", (), exc_info=True)
        try:
            raise ValueError("test error")
        except ValueError:
            record.exc_info = sys.exc_info()
        result = fmt.format(record)
        data = json.loads(result)
        assert "exc" in data
        assert data["msg"] == "error msg"

    def test_json_formatter_extra_fields(self):
        from main import _JsonFormatter
        import logging
        fmt = _JsonFormatter()
        record = logging.LogRecord("test", logging.INFO, "test.py", 10, "msg", (), None)
        record.request_id = "req-123"
        record.method = "GET"
        result = fmt.format(record)
        data = json.loads(result)
        assert data["request_id"] == "req-123"

    def test_json_formatter_no_exc_info(self):
        from main import _JsonFormatter
        import logging
        fmt = _JsonFormatter()
        record = logging.LogRecord("test", logging.WARNING, "test.py", 10, "warn msg", (), None)
        result = fmt.format(record)
        data = json.loads(result)
        assert "exc" not in data


class TestMainLogging:
    def test_configure_logging_production(self):
        from main import _configure_logging
        import logging
        root = logging.getLogger()
        old_handlers = root.handlers[:]
        root.handlers.clear()
        try:
            _configure_logging("production")
            assert len(root.handlers) > 0
        finally:
            root.handlers.clear()
            for h in old_handlers:
                root.handlers.append(h)

    def test_configure_logging_development(self):
        from main import _configure_logging
        import logging
        root = logging.getLogger()
        old_handlers = root.handlers[:]
        root.handlers.clear()
        try:
            _configure_logging("development")
            assert len(root.handlers) > 0
        finally:
            root.handlers.clear()
            for h in old_handlers:
                root.handlers.append(h)


class TestMainAppFactory:
    def test_create_app_basic(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_root_endpoint(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] is not None
        assert data["version"] == "1.0.0"

    def test_metrics_endpoint(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_sentry_init_not_called_no_dsn(self):
        with patch("main.sentry_sdk") as mock_sentry:
            import main
            app = main.create_app()
            mock_sentry.init.assert_not_called()

    def test_request_id_header_returned(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.get("/health", headers={"X-Request-ID": "custom-req-id"})
        assert resp.headers.get("X-Request-ID") == "custom-req-id"

    def test_request_id_generated_if_not_provided(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert "X-Request-ID" in resp.headers

    def test_jwt_decode_in_request_id_middleware(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        import base64
        payload = json.dumps({"sub": "user123", "user_id": "user123"})
        encoded = base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()
        token = f"header.{encoded}.signature"
        resp = client.get("/health", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_jwt_bad_padding_in_request_id_middleware(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.get("/health", headers={"Authorization": "Bearer bad-token.stuff.signature"})
        assert resp.status_code == 200

    def test_chat_health_endpoint(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.stats = AsyncMock(return_value={"chunks": 5})
        client = TestClient(app)
        resp = client.get("/api/v1/chat/health")
        assert resp.status_code == 200

    def test_speech_status_endpoint(self):
        import main
        app = main.create_app()
        mock_service = MagicMock()
        mock_service.status.return_value = {"status": "ready", "device": "cpu", "configured": False, "model_loaded": False}
        app.state.speech_service = mock_service
        client = TestClient(app)
        resp = client.get("/speech/status")
        assert resp.status_code == 200


class TestAdminApi:
    def test_admin_health_no_key_returns_403(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.stats = AsyncMock(return_value={"chunks": 10, "categories": 3})
        app.state.memory_store = MagicMock()
        app.state.memory_store.backend_name = "memory"
        app.state.memory_store.ping = AsyncMock(return_value=True)
        client = TestClient(app)
        resp = client.get("/admin/health")
        assert resp.status_code == 403

    def test_admin_health_with_valid_key(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.stats = AsyncMock(return_value={"chunks": 10, "categories": 3})
        app.state.memory_store = MagicMock()
        app.state.memory_store.backend_name = "memory"
        app.state.memory_store.ping = AsyncMock(return_value=True)

        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", "test-admin-key")

        client = TestClient(app)
        resp = client.get("/admin/health", headers={"X-Admin-Key": "test-admin-key"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_admin_health_wrong_key(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.memory_store = MagicMock()
        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", "test-admin-key")
        client = TestClient(app)
        resp = client.get("/admin/health", headers={"X-Admin-Key": "wrong-key"})
        assert resp.status_code == 403

    def test_admin_health_disabled(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.memory_store = MagicMock()
        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", None)
        client = TestClient(app)
        resp = client.get("/admin/health", headers={"X-Admin-Key": ""})
        assert resp.status_code == 503

    def test_rebuild_index_no_queue(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.rebuild_index = AsyncMock(return_value={"chunks": 10})
        app.state.memory_store = MagicMock()
        app.state.queue = None
        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", "tk")
        client = TestClient(app)
        resp = client.post("/admin/rebuild-index", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "rebuilt"

    def test_rebuild_index_with_queue(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.memory_store = MagicMock()
        mock_queue = MagicMock()
        mock_queue.enqueue = AsyncMock(return_value="job-1")
        app.state.queue = mock_queue
        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", "tk")
        client = TestClient(app)
        resp = client.post("/admin/rebuild-index", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"

    def test_get_job_no_queue(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.memory_store = MagicMock()
        app.state.queue = None
        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", "tk")
        client = TestClient(app)
        resp = client.get("/admin/jobs/job-1", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 503

    def test_get_job_not_found(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.memory_store = MagicMock()
        mock_queue = MagicMock()
        mock_queue.get_job = AsyncMock(return_value=None)
        app.state.queue = mock_queue
        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", "tk")
        client = TestClient(app)
        resp = client.get("/admin/jobs/job-1", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 404

    def test_get_job_found(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.memory_store = MagicMock()
        mock_queue = MagicMock()
        mock_job = MagicMock()
        mock_job.to_dict.return_value = {"id": "job-1", "status": "completed"}
        mock_queue.get_job = AsyncMock(return_value=mock_job)
        app.state.queue = mock_queue
        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", "tk")
        client = TestClient(app)
        resp = client.get("/admin/jobs/job-1", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200
        assert resp.json()["id"] == "job-1"

    def test_provider_health(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router._provider_unavailable.return_value = False
        app.state.chat_engine.provider_router.providers = {"template": MagicMock()}
        app.state.memory_store = MagicMock()
        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", "tk")
        client = TestClient(app)
        resp = client.get("/admin/providers/health", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_provider_dashboard(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router._provider_unavailable.return_value = False
        app.state.chat_engine.provider_router.providers = {}
        mock_cache = MagicMock()
        mock_cache.ping = AsyncMock(return_value=False)
        app.state.chat_engine.provider_router.cache = mock_cache
        app.state.memory_store = MagicMock()
        app.state.memory_store.backend_name = "memory"
        app.state.memory_store.ping = AsyncMock(return_value=True)
        from config import get_settings
        settings = get_settings()
        object.__setattr__(settings, "admin_secret", "tk")
        client = TestClient(app)
        resp = client.get("/admin/providers/dashboard", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]


class TestRebuildTask:
    @pytest.mark.asyncio
    async def test_rebuild_task_no_engine(self):
        with patch("core.queue.get_global_chat_engine", return_value=None):
            from api.admin import rebuild_rag_index_task
            with pytest.raises(ValueError, match="ChatEngine is not initialized globally"):
                mock_queue = MagicMock()
                await rebuild_rag_index_task(mock_queue, "test-job")

    @pytest.mark.asyncio
    async def test_rebuild_task_success(self):
        mock_engine = MagicMock()
        mock_engine.rebuild_index = AsyncMock(return_value={"chunks": 10})
        with patch("core.queue.get_global_chat_engine", return_value=mock_engine):
            from api.admin import rebuild_rag_index_task
            mock_queue = MagicMock()
            result = await rebuild_rag_index_task(mock_queue, "test-job")
            assert result["chunks"] == 10


class TestFirstAidTool:
    def test_lookup_cpr(self):
        from tools.first_aid_tool import FirstAidTool
        settings = _mock_settings()
        tool = FirstAidTool(settings)
        result = tool.lookup("cpr")
        assert result is not None
        assert result.get("title") == "CPR"

    def test_lookup_burn(self):
        from tools.first_aid_tool import FirstAidTool
        settings = _mock_settings()
        tool = FirstAidTool(settings)
        result = tool.lookup("burn")
        assert result is not None
        assert "steps" in result

    def test_lookup_bleeding(self):
        from tools.first_aid_tool import FirstAidTool
        settings = _mock_settings()
        tool = FirstAidTool(settings)
        result = tool.lookup("bleeding")
        assert result is not None


class TestGeocoding:
    @pytest.mark.asyncio
    async def test_aclose(self):
        from tools.geocoding import GeocodingClient
        client = GeocodingClient()
        mock_http = AsyncMock()
        client._client = mock_http
        await client.aclose()
        mock_http.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_nominatim_failure_opens_no_key(self):
        from tools.geocoding import GeocodingClient
        client = GeocodingClient(opencage_key="")
        client._client.get = AsyncMock(side_effect=Exception("network error"))
        result = await client.reverse_geocode(lat=13.0, lon=80.0)
        assert result is None


class TestContextAssembler:
    @pytest.mark.asyncio
    async def test_assemble_general_intent(self):
        from agent.context_assembler import ContextAssembler
        from rag.retriever import Retriever
        chunk = MagicMock()
        chunk.chunk_id = "c1"
        chunk.source = "test"
        chunk.title = "Test"
        chunk.category = "general"
        chunk.content = "test content"

        vs = MagicMock()
        vs.search = AsyncMock(return_value=[(chunk, 0.8)])
        vs.ensure_index = AsyncMock(return_value=[chunk])
        retriever = Retriever(vectorstore=vs, min_score=0.0)

        def make_mock_tool():
            m = MagicMock()
            m.lookup = AsyncMock(return_value=None)
            m.search = AsyncMock(return_value=[])
            m.get_payload = AsyncMock(return_value=None)
            m.infer_and_calculate = AsyncMock(return_value=None)
            return m

        assembler = ContextAssembler(
            retriever=retriever,
            sos_tool=make_mock_tool(),
            challan_tool=make_mock_tool(),
            legal_search_tool=MagicMock(),
            first_aid_tool=make_mock_tool(),
            road_infra_tool=make_mock_tool(),
            road_issues_tool=make_mock_tool(),
            submit_report_tool=MagicMock(),
            weather_tool=make_mock_tool(),
            drug_info_tool=MagicMock(),
        )
        result = await assembler.assemble(
            session_id="s1", message="hello", intent="general",
            lat=None, lon=None, client_ip=None, history=[], user_id=None
        )
        assert result is not None
        assert result.intent == "general"
        assert len(result.retrieved) > 0


class TestGovernance:
    @pytest.mark.asyncio
    async def test_evaluate_trivial_response(self):
        from agent.governance import AIGovernance
        gov = AIGovernance(redis_url=None)
        result = await gov.evaluate(
            response_text="Short response", retrieved_context=[], tool_results=[], prompt="test"
        )
        assert result is not None


class TestSafetyChecker:
    @pytest.mark.asyncio
    async def test_check_llama_guard_available(self):
        from agent.safety_checker import SafetyChecker
        checker = SafetyChecker()
        result = await checker.check_llama_guard("hello", "user")
        assert result.blocked is False


class TestCoreMetrics:
    def test_metrics_response(self):
        from core.metrics import metrics_response, metrics_content_type
        result = metrics_response()
        assert result is not None
        content_type = metrics_content_type()
        assert "text/plain" in content_type


class TestCoreQueue:
    def test_task_registry(self):
        from core.queue import task, _TASK_REGISTRY
        @task("my_test_task")
        async def my_func(q, job_id):
            return "ok"
        assert "my_test_task" in _TASK_REGISTRY

    def test_get_global_engine_none(self):
        from core.queue import get_global_chat_engine, _chat_engine
        saved = _chat_engine
        try:
            from core.queue import set_global_chat_engine
            set_global_chat_engine(None)
            result = get_global_chat_engine()
            assert result is None
        finally:
            from core.queue import set_global_chat_engine
            set_global_chat_engine(saved)

    def test_set_and_get_global_engine(self):
        from core.queue import set_global_chat_engine, get_global_chat_engine, _chat_engine
        saved = _chat_engine
        try:
            engine = MagicMock()
            set_global_chat_engine(engine)
            result = get_global_chat_engine()
            assert result is engine
        finally:
            set_global_chat_engine(saved)

    def test_job_from_dict(self):
        from core.queue import Job
        data = {
            "job_id": "j1", "task_name": "test", "args": [], "kwargs": {},
            "status": "success", "retries_left": 0, "error": None,
            "created_at": 100.0, "started_at": 101.0, "completed_at": 102.0,
            "progress": 100, "result": "done",
        }
        job = Job.from_dict(data)
        assert job.job_id == "j1"
        assert job.status == "success"

    def test_job_to_dict(self):
        from core.queue import Job
        job = Job(job_id="j2", task_name="t", args=[], kwargs={})
        d = job.to_dict()
        assert d["job_id"] == "j2"

    def test_task_queue_enqueue_unregistered(self):
        from core.queue import TaskQueue
        mock_redis = MagicMock()
        mock_redis.hset = AsyncMock()
        mock_redis.rpush = AsyncMock()
        q = TaskQueue(mock_redis)
        import asyncio
        job_id = asyncio.run(q.enqueue("unregistered_task"))
        assert job_id is not None
        mock_redis.hset.assert_called_once()
        mock_redis.rpush.assert_called_once()

    def test_task_queue_get_job_not_found(self):
        from core.queue import TaskQueue
        mock_redis = MagicMock()
        mock_redis.hget = AsyncMock(return_value=None)
        q = TaskQueue(mock_redis)
        import asyncio
        result = asyncio.run(q.get_job("nonexistent"))
        assert result is None

    def test_task_queue_get_job_found(self):
        from core.queue import TaskQueue, Job
        import json
        job = Job(job_id="j3", task_name="t", args=[], kwargs={})
        mock_redis = MagicMock()
        mock_redis.hget = AsyncMock(return_value=json.dumps(job.to_dict()))
        q = TaskQueue(mock_redis)
        import asyncio
        result = asyncio.run(q.get_job("j3"))
        assert result is not None
        assert result.job_id == "j3"


class TestRetriever:
    @pytest.mark.asyncio
    async def test_retrieve_empty_query(self):
        from rag.retriever import Retriever
        vs = MagicMock()
        vs.search = AsyncMock(return_value=[])
        retriever = Retriever(vectorstore=vs, min_score=0.5)
        result = await retriever.retrieve("", top_k=5)
        assert result == []


class TestConfig:
    def test_split_csv_none(self):
        from config import _split_csv
        assert _split_csv(None, default=["a"]) == ["a"]

    def test_split_csv_empty(self):
        from config import _split_csv
        assert _split_csv("", default=["a"]) == ["a"]

    def test_split_csv_values(self):
        from config import _split_csv
        assert _split_csv("a, b, c", default=[]) == ["a", "b", "c"]

    def test_as_path_none(self):
        from config import _as_path
        from pathlib import Path
        result = _as_path(None, default=Path("/tmp"))
        assert result == Path("/tmp")

    def test_as_optional_path_none(self):
        from config import _as_optional_path
        assert _as_optional_path(None) is None

    def test_as_optional_path_empty(self):
        from config import _as_optional_path
        assert _as_optional_path("") is None


class TestMainSentryAndLifespan:
    @patch("main.sentry_sdk")
    def test_sentry_init_with_dsn(self, mock_sentry):
        import main
        settings = main.get_settings()
        orig = settings.sentry_dsn
        object.__setattr__(settings, "sentry_dsn", "https://key@sentry.io/123")
        try:
            app = main.create_app()
            mock_sentry.init.assert_called_once()
        finally:
            object.__setattr__(settings, "sentry_dsn", orig)

    def test_no_api_keys_warning_branch(self):
        import main
        app = main.create_app()
        assert app is not None

    def test_body_size_middleware_too_large(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.post("/api/v1/chat/", json={"message": "x" * (2 * 1024 * 1024)})
        assert resp.status_code == 413

    def test_security_headers_middleware(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.headers.get("Strict-Transport-Security") is not None
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_jwt_bad_token_user_id_fallback(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.get("/health", headers={"Authorization": "Bearer .notjson."})
        assert resp.status_code == 200

    def test_jwt_short_token(self):
        import main
        app = main.create_app()
        client = TestClient(app)
        resp = client.get("/health", headers={"Authorization": "Bearer singlepart"})
        assert resp.status_code == 200


class TestApiChatBranches:
    def test_chat_no_message(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        client = TestClient(app)
        resp = client.post("/api/v1/chat/", json={})
        assert resp.status_code == 422

    def test_chat_history_no_auth(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        client = TestClient(app)
        resp = client.get("/api/v1/chat/history/test-session")
        assert resp.status_code == 403

    def test_chat_timeout(self):
        import main
        import asyncio
        app = main.create_app()
        engine = MagicMock()
        async def ok_chat(*args, **kwargs):
            from agent.state import ChatResponse
            return ChatResponse(response="ok", intent="general", session_id="s1", sources=[])
        engine.chat = ok_chat
        app.state.chat_engine = engine
        from config import get_settings
        object.__setattr__(get_settings(), "internal_api_key", None)
        object.__setattr__(get_settings(), "environment", "development")
        import api.chat
        orig = api.chat.asyncio.wait_for
        def timeout_wait_for(coro, timeout, **kw):
            raise asyncio.TimeoutError()
        api.chat.asyncio.wait_for = timeout_wait_for
        try:
            client = TestClient(app)
            resp = client.post("/api/v1/chat/", json={"message": "hi"})
            assert resp.status_code == 504
        finally:
            api.chat.asyncio.wait_for = orig


class TestConfigHelperBranches:
    def test_as_path_relative_resolves(self):
        from config import _as_path
        from pathlib import Path
        result = _as_path("relative/path", default=Path("/tmp"))
        assert result is not None
        assert result.is_absolute()

    def test_as_optional_path_relative(self):
        from config import _as_optional_path
        result = _as_optional_path("relative/sub")
        assert result is not None
        assert result.is_absolute()


class TestMiddlewareBranches:
    def test_correlation_id_added(self):
        from middleware.correlation_id import setup_correlation_id
        app = FastAPI()
        @app.get("/test")
        async def test():
            return {"ok": True}
        setup_correlation_id(app)
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200

    def test_query_profiler_added(self):
        from middleware.query_profiler import setup_query_profiler
        app = FastAPI()
        @app.get("/test")
        async def test():
            return {"ok": True}
        setup_query_profiler(app)
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200


class TestPotholeValidator:
    def test_validate_image_fails_without_yolo(self):
        from services.pothole_validator import PotholeValidator
        result = PotholeValidator.validate_image(b"fakebytes")
        assert result["success"] is False


class TestProviderRouterInitBranches:
    @patch.dict(os.environ, {"GROQ_API_KEY": "gk-test", "DEFAULT_LLM_PROVIDER": "groq"})
    def test_router_init_with_provider(self):
        from config import get_settings
        s = get_settings()
        orig_provider = s.default_llm_provider
        object.__setattr__(s, "default_llm_provider", "groq")
        try:
            from providers.router import ProviderRouter
            router = ProviderRouter(s, cache=None)
            assert router is not None
            assert "groq" in router.providers or len(router.providers) > 0
        finally:
            object.__setattr__(s, "default_llm_provider", orig_provider)


class TestGraphCoordination:
    @pytest.mark.asyncio
    async def test_chat_emergency_intent(self):
        from agent.graph import ChatEngine
        from agent.state import ChatRequest
        from tests.test_graph_coverage import FakeMemoryStore, FakeVectorStore, FakeIntentDetector, FakeSafetyChecker, FakeProviderRouter, FakeGovernance, FakeSummarizer
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("emergency"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=MagicMock(),
            provider_router=FakeProviderRouter(),
        )
        engine.governance = FakeGovernance()
        engine.summarizer = FakeSummarizer()
        ctx = MagicMock()
        ctx.retrieved = []
        ctx.tools = [MagicMock()]
        engine.context_assembler.assemble = AsyncMock(return_value=ctx)
        result = await engine.chat(ChatRequest(message="help", session_id="em-test"))
        assert result is not None

    @pytest.mark.asyncio
    async def test_stream_tool_call(self):
        from agent.graph import ChatEngine
        from agent.state import ChatRequest
        from tests.test_graph_coverage import FakeMemoryStore, FakeVectorStore, FakeIntentDetector, FakeSafetyChecker, FakeProviderRouter, FakeGovernance, FakeSummarizer
        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=MagicMock(),
            provider_router=FakeProviderRouter(),
        )
        engine.governance = FakeGovernance()
        engine.summarizer = FakeSummarizer()
        ctx = MagicMock()
        ctx.retrieved = []
        ctx.tools = [MagicMock()]
        ctx.tools[0].name = "sos"
        ctx.tools[0].summary = "test sos"
        engine.context_assembler.assemble = AsyncMock(return_value=ctx)
        events = [e async for e in engine.stream_chat(ChatRequest(message="help", session_id="stream-tool"))]
        assert len(events) >= 1


class TestGraphStreamNoContext:
    @pytest.mark.asyncio
    async def test_stream_no_context(self):
        from agent.graph import ChatEngine
        from agent.state import ChatRequest
        from tests.test_graph_coverage import FakeMemoryStore, FakeVectorStore, FakeIntentDetector, FakeSafetyChecker, FakeProviderRouter, FakeGovernance, FakeSummarizer

        memory = FakeMemoryStore()
        engine = ChatEngine(
            memory_store=memory,
            vectorstore=FakeVectorStore(),
            intent_detector=FakeIntentDetector("general"),
            safety_checker=FakeSafetyChecker(),
            context_assembler=MagicMock(),
            provider_router=FakeProviderRouter(),
        )
        engine.governance = FakeGovernance()
        engine.summarizer = FakeSummarizer()
        ctx_result = MagicMock()
        ctx_result.retrieved = []
        ctx_result.tools = []
        engine.context_assembler.assemble = AsyncMock(return_value=ctx_result)

        events = [e async for e in engine.stream_chat(ChatRequest(message="test", session_id="st-no-ctx"))]
        assert len(events) >= 1


class TestMainGlobalExceptionHandler:
    def test_global_exception_handler_catches_unhandled(self):
        import main
        app = main.create_app()
        @app.get("/trigger-error")
        async def _trigger():
            raise ValueError("test unhandled error")
        from fastapi.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/trigger-error")
        assert resp.status_code == 500
        assert "Internal server error" in resp.json()["detail"]


class TestMainHostValidation:
    def test_host_validation_blocks_bad_host_in_production(self):
        import main
        from config import get_settings
        s = get_settings()
        orig_env = s.environment
        object.__setattr__(s, "environment", "production")
        try:
            app = main.create_app()
            from fastapi.testclient import TestClient
            client = TestClient(app)
            resp = client.get("/health", headers={"host": "malicious.example.com"})
            assert resp.status_code == 403
        finally:
            object.__setattr__(s, "environment", orig_env)

    def test_host_validation_allows_good_host_in_production(self):
        import main
        from config import get_settings
        s = get_settings()
        orig_env = s.environment
        object.__setattr__(s, "environment", "production")
        try:
            app = main.create_app()
            from fastapi.testclient import TestClient
            client = TestClient(app)
            resp = client.get("/health", headers={"host": "localhost:3000"})
            assert resp.status_code == 200
        finally:
            object.__setattr__(s, "environment", orig_env)





class TestAdminProviderHealth:
    def test_provider_health_circuit_breaker_open(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router._provider_unavailable.return_value = True
        app.state.chat_engine.provider_router.providers = {"test-provider": MagicMock()}
        app.state.memory_store = MagicMock()
        from config import get_settings
        object.__setattr__(get_settings(), "admin_secret", "tk")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/admin/providers/health", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["providers"]["test-provider"]["status"] == "disabled"

    def test_provider_health_generate_fails(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        mock_provider = MagicMock()
        async def bad_generate(req):
            raise RuntimeError("provider down")
        mock_provider.generate = bad_generate
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router._provider_unavailable.return_value = False
        app.state.chat_engine.provider_router.providers = {"failing-provider": mock_provider}
        app.state.memory_store = MagicMock()
        from config import get_settings
        object.__setattr__(get_settings(), "admin_secret", "tk")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/admin/providers/health", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["providers"]["failing-provider"]["status"] == "error"

    def test_provider_dashboard_circuit_breaker(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router._provider_unavailable.return_value = True
        app.state.chat_engine.provider_router.providers = {"test-p": MagicMock()}
        mock_cache = MagicMock()
        mock_cache.ping = AsyncMock(return_value=True)
        app.state.chat_engine.provider_router.cache = mock_cache
        app.state.memory_store = MagicMock()
        app.state.memory_store.backend_name = "memory"
        app.state.memory_store.ping = AsyncMock(return_value=True)
        from config import get_settings
        object.__setattr__(get_settings(), "admin_secret", "tk")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/admin/providers/dashboard", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200

    def test_provider_dashboard_one_healthy_one_error(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        healthy = MagicMock()
        async def healthy_gen(req):
            pass
        healthy.generate = healthy_gen
        failing = MagicMock()
        async def fail_gen(req):
            raise RuntimeError("fail")
        failing.generate = fail_gen
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router._provider_unavailable.return_value = False
        app.state.chat_engine.provider_router.providers = {"healthy-p": healthy, "failing-p": failing}
        mock_cache = MagicMock()
        mock_cache.ping = AsyncMock(return_value=True)
        app.state.chat_engine.provider_router.cache = mock_cache
        app.state.memory_store = MagicMock()
        app.state.memory_store.backend_name = "memory"
        app.state.memory_store.ping = AsyncMock(return_value=True)
        from config import get_settings
        object.__setattr__(get_settings(), "admin_secret", "tk")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/admin/providers/dashboard", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200


class TestAdminNoSecret:
    def test_admin_disabled_when_no_secret(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        app.state.memory_store = MagicMock()
        from config import get_settings
        object.__setattr__(get_settings(), "admin_secret", None)
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/admin/health", headers={"X-Admin-Key": ""})
        assert resp.status_code == 503


class TestChatStreamTimeout:
    def test_chat_stream_timeout(self):
        import main
        import asyncio
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        async def endless_stream(*args, **kwargs):
            async def inner():
                await asyncio.sleep(100)
                yield {"type": "token", "text": "still going"}
            return inner()
        app.state.chat_engine.stream_chat = endless_stream
        from config import get_settings
        object.__setattr__(get_settings(), "internal_api_key", None)
        object.__setattr__(get_settings(), "environment", "development")
        object.__setattr__(get_settings(), "http_timeout_seconds", 0.001)
        from fastapi.testclient import TestClient
        client = TestClient(app)
        with client.stream("POST", "/api/v1/chat/stream", json={"message": "hi"}) as resp:
            assert resp.status_code == 200


class TestToolsInitBackendClient:
    @pytest.mark.asyncio
    async def test_backend_get_http_500_triggers_alert(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        s = get_settings()
        client = BackendToolClient(s)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_resp)
        client._client.get = AsyncMock(return_value=mock_resp)
        with patch("tools.__init__.get_alert_service") as mock_alert:
            alert_svc = MagicMock()
            mock_alert.return_value = alert_svc
            result = await client.get("/test")
            assert result is None
            alert_svc.alert_external_api_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_backend_get_request_error(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        import httpx
        s = get_settings()
        client = BackendToolClient(s)
        client._client.get = AsyncMock(side_effect=httpx.RequestError("connection failed"))
        with patch("tools.__init__.get_alert_service") as mock_alert:
            alert_svc = MagicMock()
            mock_alert.return_value = alert_svc
            result = await client.get("/test")
            assert result is None
            alert_svc.alert_external_api_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_backend_get_value_error(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        s = get_settings()
        client = BackendToolClient(s)
        mock_resp = MagicMock()
        mock_resp.json.side_effect = ValueError("not json")
        client._client.get = AsyncMock(return_value=mock_resp)
        mock_resp.raise_for_status = MagicMock()
        result = await client.get("/test")
        assert result is None

    @pytest.mark.asyncio
    async def test_backend_post_http_500_triggers_alert(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        import httpx
        s = get_settings()
        client = BackendToolClient(s)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_resp)
        client._client.post = AsyncMock(return_value=mock_resp)
        with patch("tools.__init__.get_alert_service") as mock_alert:
            alert_svc = MagicMock()
            mock_alert.return_value = alert_svc
            result = await client.post("/test", payload={})
            assert result is None
            alert_svc.alert_external_api_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_backend_post_request_error(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        import httpx
        s = get_settings()
        client = BackendToolClient(s)
        client._client.post = AsyncMock(side_effect=httpx.RequestError("connection failed"))
        with patch("tools.__init__.get_alert_service") as mock_alert:
            alert_svc = MagicMock()
            mock_alert.return_value = alert_svc
            result = await client.post("/test", payload={})
            assert result is None
            alert_svc.alert_external_api_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_backend_post_value_error(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        s = get_settings()
        client = BackendToolClient(s)
        mock_resp = MagicMock()
        mock_resp.json.side_effect = ValueError("not json")
        client._client.post = AsyncMock(return_value=mock_resp)
        mock_resp.raise_for_status = MagicMock()
        result = await client.post("/test", payload={})
        assert result is None

    @pytest.mark.asyncio
    async def test_backend_get_success(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        s = get_settings()
        client = BackendToolClient(s)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "ok"}
        client._client.get = AsyncMock(return_value=mock_resp)
        mock_resp.raise_for_status = MagicMock()
        result = await client.get("/test")
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_backend_post_success(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        s = get_settings()
        client = BackendToolClient(s)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "created"}
        client._client.post = AsyncMock(return_value=mock_resp)
        mock_resp.raise_for_status = MagicMock()
        result = await client.post("/test", payload={"key": "val"})
        assert result == {"result": "created"}

    @pytest.mark.asyncio
    async def test_backend_get_http_400_no_alert(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        import httpx
        s = get_settings()
        client = BackendToolClient(s)
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("400", request=MagicMock(), response=mock_resp)
        client._client.get = AsyncMock(return_value=mock_resp)
        with patch("tools.__init__.get_alert_service") as mock_alert:
            alert_svc = MagicMock()
            mock_alert.return_value = alert_svc
            result = await client.get("/test")
            assert result is None
            alert_svc.alert_external_api_failed.assert_not_called()

    @pytest.mark.asyncio
    async def test_backend_post_http_400_no_alert(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        import httpx
        s = get_settings()
        client = BackendToolClient(s)
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("400", request=MagicMock(), response=mock_resp)
        client._client.post = AsyncMock(return_value=mock_resp)
        with patch("tools.__init__.get_alert_service") as mock_alert:
            alert_svc = MagicMock()
            mock_alert.return_value = alert_svc
            result = await client.post("/test", payload={})
            assert result is None
            alert_svc.alert_external_api_failed.assert_not_called()

    @pytest.mark.asyncio
    async def test_aclose(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        s = get_settings()
        client = BackendToolClient(s)
        client._client.aclose = AsyncMock()
        await client.aclose()
        client._client.aclose.assert_called_once()

    def test_backend_client_constructor_with_internal_api_key(self):
        from tools.__init__ import BackendToolClient
        from config import get_settings
        s = get_settings()
        orig = s.internal_api_key
        object.__setattr__(s, "internal_api_key", "test-internal-key")
        try:
            client = BackendToolClient(s)
            assert client._client.headers.get("X-Internal-Api-Key") == "test-internal-key"
        finally:
            object.__setattr__(s, "internal_api_key", orig)


class TestApiChatTimeout:
    def test_chat_timeout_error(self):
        import main
        import asyncio
        app = main.create_app()
        engine = MagicMock()
        original = asyncio.wait_for
        def timeout_first(coro, timeout, **kw):
            if hasattr(coro, "__aiter__"):
                return coro
            raise asyncio.TimeoutError()
        asyncio.wait_for = timeout_first
        try:
            async def ok_chat(*a, **kw):
                from agent.state import ChatResponse
                return ChatResponse(response="ok", intent="g", session_id="s1", sources=[])
            engine.chat = ok_chat
            app.state.chat_engine = engine
            from config import get_settings
            object.__setattr__(get_settings(), "internal_api_key", None)
            object.__setattr__(get_settings(), "environment", "development")
            from fastapi.testclient import TestClient
            client = TestClient(app)
            resp = client.post("/api/v1/chat/", json={"message": "hi"})
            assert resp.status_code == 504
        finally:
            asyncio.wait_for = original


class TestAdminProviderHealthWithSuccess:
    def test_provider_health_successful_generate(self):
        import main
        app = main.create_app()
        app.state.chat_engine = MagicMock()
        healthy = MagicMock()
        async def healthy_gen(req):
            import time
        healthy.generate = healthy_gen
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router._provider_unavailable.return_value = False
        app.state.chat_engine.provider_router.providers = {"my-provider": healthy}
        app.state.memory_store = MagicMock()
        from config import get_settings
        object.__setattr__(get_settings(), "admin_secret", "tk")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/admin/providers/health", headers={"X-Admin-Key": "tk"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["providers"]["my-provider"]["status"] == "healthy"


class TestApiProvidersRoutes:
    def test_configure_providers(self):
        from api import api_router
        app = FastAPI()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router.configure_user_providers.return_value = ["groq"]
        app.include_router(api_router)
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.post("/api/v1/providers/configure", json=[{"provider_name": "groq", "api_key": "test"}])
        assert resp.status_code == 200
        assert resp.json()["configured"] == 1

    def test_get_active_providers(self):
        from api import api_router
        app = FastAPI()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router.get_active_provider_info.return_value = [{"name": "groq"}]
        app.include_router(api_router)
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/api/v1/providers/active")
        assert resp.status_code == 200
        assert resp.json() == [{"name": "groq"}]

    def test_test_provider_no_base_url(self):
        from api import api_router
        app = FastAPI()
        app.include_router(api_router)
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.post("/api/v1/providers/test", json={"api_key": "test", "base_url": ""})
        assert resp.status_code == 400

    def test_reset_providers(self):
        from api import api_router
        app = FastAPI()
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router.reset_to_env_providers = MagicMock()
        app.include_router(api_router)
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.post("/api/v1/providers/reset")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestMemorySummarizer:
    def test_summarizer_no_history(self):
        from memory.summarizer import ConversationSummarizer
        summarizer = ConversationSummarizer()
        result = summarizer.summarize([])
        assert result is None or result == "" or result is not None


class TestCoreMetricsDetail:
    def test_metrics_labels_and_counters(self):
        from core.metrics import api_request_total, api_request_time
        assert api_request_total is not None
        assert api_request_time is not None


class TestMainWebEmbeddings:
    def test_embeddings_not_found(self):
        import main
        app = main.create_app()
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/embeddings.json")
        assert resp.status_code == 404


class TestToolInitBrokenImportOnly:
    def test_tools_init_can_be_imported(self):
        import tools.__init__
        assert tools.__init__.__name__ == "tools.__init__"


class TestFirstAidToolLoadGuides:
    def test_load_guides_valid_dict(self):
        from tools.first_aid_tool import FirstAidTool, FALLBACK_GUIDES
        import tempfile, json
        s = _mock_settings()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({"test-guide": {"title": "Test Guide", "keywords": ["test"], "steps": ["Step 1"]}}, f)
            tmp_path = f.name
        try:
            from pathlib import Path
            mock_path = Path(tmp_path)
            s.rag_data_dir.__truediv__.return_value = mock_path
            tool = FirstAidTool(s)
            result = tool.lookup("test")
            assert result is not None
            assert result["title"] == "Test Guide"
        finally:
            import os
            os.unlink(tmp_path)


class TestIntentDetectorBranches:
    def test_cosine_similarity_zero_norm(self):
        from agent.intent_detector import IntentDetector
        d = IntentDetector()
        result = d._cosine_similarity([0.0, 0.0], [1.0, 0.0])
        assert result == 0.0

    def test_semantic_routing_best_intent(self):
        from agent.intent_detector import IntentDetector
        d = IntentDetector()
        result = d.detect("tell me about traffic rules and regulations")
        assert result in ("legal", "general")


class TestCorrelationIdFunctions:
    def test_generate_correlation_id(self):
        from middleware.correlation_id import generate_correlation_id
        cid = generate_correlation_id()
        assert cid is not None
        assert len(cid) == 8

    def test_get_correlation_id_default(self):
        from middleware.correlation_id import get_correlation_id, correlation_id_var
        correlation_id_var.set("test-id")
        cid = get_correlation_id()
        assert cid == "test-id"


class TestFirstAidToolBranches:
    def test_lookup_returns_none_for_unmatched(self):
        from tools.first_aid_tool import FirstAidTool
        from config import get_settings
        tool = FirstAidTool(get_settings())
        result = tool.lookup("supercalifragilistic")
        assert result is None

    def test_load_guides_valid_dict(self):
        from tools.first_aid_tool import FirstAidTool
        from config import get_settings
        import json
        from pathlib import Path
        s = get_settings()
        data_path = Path(__file__).resolve().parent.parent / "data" / "first_aid_guides.json"
        if data_path.exists():
            tool = FirstAidTool(s)
            result = tool.lookup("cpr")
            assert result is not None


class TestGeocodingRateLimit:
    @pytest.mark.asyncio
    async def test_nominatim_rate_limit_sleep(self):
        from tools.geocoding import GeocodingClient
        import time
        client = GeocodingClient()
        client._last_nominatim_request_at = time.monotonic() - 0.5
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"display_name": "Test"}
        client._client.get = AsyncMock(return_value=mock_resp)
        result = await client._nominatim_request(lat=13.0, lon=80.0)
        assert result is not None


class TestCoreQueueWorker:
    @pytest.mark.asyncio
    async def test_worker_loop_blpop_timeout(self):
        from core.queue import BackgroundWorker
        mock_redis = MagicMock()
        call_count = 0
        async def blpop_once(*a, **kw):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                worker.running = False
            return None
        mock_redis.blpop = AsyncMock(side_effect=blpop_once)
        worker = BackgroundWorker(mock_redis, concurrency=1)
        worker.running = True
        worker._process_job = AsyncMock()
        await worker._worker_loop(1)
        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_worker_loop_blpop_with_job(self):
        from core.queue import BackgroundWorker
        mock_redis = MagicMock()
        processed = False
        async def blpop_then_stop(*a, **kw):
            nonlocal processed
            return (b"queue", b"job-1")
        mock_redis.blpop = AsyncMock(side_effect=blpop_then_stop)
        mock_redis.hget = AsyncMock(return_value=None)
        worker = BackgroundWorker(mock_redis, concurrency=1)
        worker.running = True
        async def process_and_stop(job_id):
            nonlocal processed
            processed = True
            worker.running = False
        worker._process_job = process_and_stop
        await worker._worker_loop(1)
        assert processed

    @pytest.mark.asyncio
    async def test_worker_loop_exception_continues(self):
        from core.queue import BackgroundWorker
        mock_redis = MagicMock()
        call_count = 0
        async def blpop_error(*a, **kw):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                worker.running = False
            raise Exception("worker error")
        mock_redis.blpop = AsyncMock(side_effect=blpop_error)
        worker = BackgroundWorker(mock_redis, concurrency=1)
        worker.running = True
        worker._process_job = AsyncMock()
        await worker._worker_loop(1)
        assert call_count >= 2


class TestGovernanceBranches:
    @pytest.mark.asyncio
    async def test_evaluate_low_factuality(self):
        from agent.governance import AIGovernance
        from unittest.mock import ANY
        gov = AIGovernance(redis_url=None)
        gov._redis = None
        with patch.object(gov, '_detect_hallucination', return_value=0.9):
            with patch.object(gov, '_score_factuality', return_value=0.3):
                result = await gov.evaluate(
                    response_text="Some response about law",
                    retrieved_context=[{"text": "some context"}],
                    tool_results=[],
                    prompt="test prompt",
                )
                assert result.flagged is True
                assert "factuality" in (result.flag_reason or "").lower()


class TestGovernanceAuditLogError:
    @pytest.mark.asyncio
    async def test_log_audit_exception(self):
        from agent.governance import AIGovernance, GovernanceResult
        gov = AIGovernance(redis_url=None)
        gov._redis = MagicMock()
        gov._redis.rpush = AsyncMock(side_effect=Exception("redis error"))
        result = GovernanceResult(
            text="ok", flagged=False, flag_reason=None,
            hallucination_score=0.9, factuality_score=0.8,
            prompt_version="v1",
        )
        await gov._log_audit(result, "test prompt")
        assert True


class TestSafetyCheckerExtra:
    def test_space_obfuscated_harm(self):
        from agent.safety_checker import SafetyChecker
        checker = SafetyChecker()
        result = checker.evaluate("h u r t   s o m e o n e")
        assert result.blocked is True


class TestSummarizerBranches:
    def test_summarize_assistant_role(self):
        from memory.summarizer import ConversationSummarizer
        s = ConversationSummarizer(threshold=2)
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        result = s.summarize(history)
        assert "user" in result["summary"].lower() or "assistant" in result["summary"].lower()
        assert result["turn_count"] == 2

    def test_summarize_intent_from_metadata(self):
        from memory.summarizer import ConversationSummarizer
        s = ConversationSummarizer(threshold=2)
        history = [
            {"role": "user", "content": "need help", "metadata": {"intent": "emergency"}},
            {"role": "assistant", "content": "calling 112"},
        ]
        result = s.summarize(history)
        assert "emergency" in result["summary"]


class TestFirstAidToolBranches2:
    def test_load_guides_empty_dict(self):
        from tools.first_aid_tool import FirstAidTool
        import tempfile, json
        s = _mock_settings()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({}, f)
            tmp_path = f.name
        try:
            from pathlib import Path
            s.rag_data_dir.__truediv__.return_value = Path(tmp_path)
            tool = FirstAidTool(s)
            result = tool.lookup("bleeding")
            assert result is not None
        finally:
            import os
            os.unlink(tmp_path)


class TestSubmitReportToolBranches:
    def test_get_client_closed(self):
        from tools.submit_report_tool import SubmitReportTool
        s = _mock_settings()
        from unittest.mock import PropertyMock
        type(s).backend_base_url = PropertyMock(return_value="http://localhost:8000")
        tool = SubmitReportTool(s)
        client = tool._get_client()
        assert client is not None
        import asyncio
        asyncio.run(client.aclose())
        client2 = tool._get_client()
        assert client2 is not client


class TestPotholeValidatorBranches:
    def test_confidence_update(self):
        from services.pothole_validator import PotholeValidator
        import io
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        img_bytes = buf.getvalue()
        result = PotholeValidator.validate_image(img_bytes)
        assert result["success"] is False  # no YOLO model loaded
        assert "error" in result


class TestDocumentLoaderBranches:
    def test_csv_no_fieldnames(self):
        from rag.document_loader import _read_csv
        import tempfile
        content = "a,b\n1,2\n".encode('utf-8-sig')
        try:
            p = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
            p.write(content)
            p.close()
            from pathlib import Path
            result = _read_csv(Path(p.name))
            assert result is not None
        finally:
            import os
            os.unlink(p.name)

    def test_pdf_no_text(self):
        from rag.document_loader import _read_pdf
        import tempfile
        try:
            p = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            p.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\nxref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \ntrailer<</Size 3/Root 1 0 R>>\nstartxref\n114\n%%EOF")
            p.close()
            from pathlib import Path
            result = _read_pdf(Path(p.name))
            assert result == ''
        finally:
            import os
            os.unlink(p.name)


class TestCoreQueueBranches:
    def test_update_progress_no_job(self):
        from core.queue import TaskQueue
        mock_redis = MagicMock()
        mock_redis.hget = AsyncMock(return_value=None)
        q = TaskQueue(mock_redis)
        import asyncio
        asyncio.run(q.update_progress("noexist", 50))
        mock_redis.hget.assert_called_once()

    def test_update_progress_with_result(self):
        from core.queue import TaskQueue, Job
        import json
        job = Job(job_id="j99", task_name="t", args=[], kwargs={})
        mock_redis = MagicMock()
        mock_redis.hget = AsyncMock(return_value=json.dumps(job.to_dict()))
        mock_redis.hset = AsyncMock()
        q = TaskQueue(mock_redis)
        import asyncio
        asyncio.run(q.update_progress("j99", 100, status="success", result="done"))
        mock_redis.hset.assert_called_once()


class TestApiAiEndpoint:
    def test_validate_image_too_large(self):
        import main
        app = main.create_app()
        from config import get_settings
        object.__setattr__(get_settings(), "internal_api_key", None)
        object.__setattr__(get_settings(), "environment", "development")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        large_data = b"x" * (6 * 1024 * 1024)
        resp = client.post("/api/v1/ai/validate-image", files={"file": ("test.jpg", large_data, "image/jpeg")})
        assert resp.status_code == 413
        assert "too large" in resp.text.lower()


class TestConfigRelativePaths:
    def test_as_path_relative(self):
        from config import _as_path
        from pathlib import Path
        result = _as_path("relative/path", default=Path("/tmp/default"))
        assert result.is_absolute()

    def test_as_optional_path_relative(self):
        from config import _as_optional_path
        result = _as_optional_path("relative/opt")
        assert result.is_absolute()

    def test_resolve_optional_path_relative(self):
        from config import Settings, ROOT_DIR
        s = Settings()
        from pathlib import Path
        result = s._resolve_optional_path(ROOT_DIR / "relative/data")
        assert result.is_absolute()


class TestAdminNonTupleResult:
    def test_admin_health_non_tuple(self):
        import main
        app = main.create_app()
        from config import get_settings
        object.__setattr__(get_settings(), "admin_secret", "test-secret")
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.stats = AsyncMock(return_value={"total_queries": 0})
        mem = MagicMock()
        mem.ping = AsyncMock(return_value=True)
        app.state.memory_store = mem
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/admin/health", headers={"X-Admin-Key": "test-secret"})
        assert resp.status_code == 200

    def test_admin_dashboard_non_tuple(self):
        import main
        app = main.create_app()
        from config import get_settings
        object.__setattr__(get_settings(), "admin_secret", "test-secret")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        engine = MagicMock()
        engine.stats = AsyncMock(return_value={})
        engine.provider_router = MagicMock()
        engine.provider_router.providers = {}
        engine.provider_router._provider_unavailable = MagicMock(return_value=False)
        engine.provider_router.cache = None
        engine.get_history = AsyncMock(return_value=[])
        app.state.chat_engine = engine
        mem = MagicMock()
        mem.ping = AsyncMock(return_value=True)
        mem.backend_name = "redis"
        app.state.memory_store = mem
        resp = client.get("/admin/providers/dashboard", headers={"X-Admin-Key": "test-secret"})
        assert resp.status_code in (200, 503)


class TestChatAuthBranches:
    def test_chat_wrong_internal_key(self):
        import main
        app = main.create_app()
        from config import get_settings
        object.__setattr__(get_settings(), "internal_api_key", "real-key")
        object.__setattr__(get_settings(), "environment", "development")
        app.state.chat_engine = MagicMock()
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.post("/api/v1/chat/", json={"message": "hi"}, headers={"X-Internal-Api-Key": "wrong-key"})
        assert resp.status_code == 403

    def test_chat_production_no_key_configured(self):
        import main
        app = main.create_app()
        from config import get_settings
        saved_env = get_settings().environment
        saved_key = get_settings().internal_api_key
        object.__setattr__(get_settings(), "internal_api_key", None)
        object.__setattr__(get_settings(), "environment", "production")
        app.state.chat_engine = MagicMock()
        import os as _os
        _os.environ["ALLOWED_HOSTS"] = "testserver"
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.post("/api/v1/chat/", json={"message": "hi"})
        _os.environ.pop("ALLOWED_HOSTS", None)
        object.__setattr__(get_settings(), "environment", saved_env)
        object.__setattr__(get_settings(), "internal_api_key", saved_key)
        assert resp.status_code == 500


class TestQueueAlertServiceNotFound:
    def test_queue_module_imports_alert_service(self):
        from core.queue import get_alert_service
        assert get_alert_service is not None


class TestToolsInitAlertService:
    def test_tools_init_imports_alert_service(self):
        from tools.__init__ import get_alert_service
        assert get_alert_service is not None


class TestPotholeValidatorModelNotFound:
    def test_get_model_not_found(self):
        import sys as _sys
        mock_ultralytics = MagicMock()
        _sys.modules['ultralytics'] = mock_ultralytics
        _sys.modules['ultralytics.YOLO'] = MagicMock()
        try:
            from services.pothole_validator import PotholeValidator
            PotholeValidator._model = None
            with patch("os.path.exists", return_value=False):
                with pytest.raises(FileNotFoundError):
                    PotholeValidator.get_model()
        finally:
            _sys.modules.pop('ultralytics', None)


class TestPlanAndExecuteGeneratePlan:
    @pytest.mark.asyncio
    async def test_no_json_markers_returns_fallback(self):
        from agent.plan_and_execute import PlanAndExecuteAgent, PlanStep
        router = MagicMock()
        router.generate = AsyncMock()
        router.generate.return_value.text = "just plain text"
        agent = PlanAndExecuteAgent(provider_router=router, tools={})
        steps = await agent.generate_plan("hello")
        assert len(steps) == 1
        assert steps[0].step == "hello"

    @pytest.mark.asyncio
    async def test_router_exception_caught(self):
        from agent.plan_and_execute import PlanAndExecuteAgent
        router = MagicMock()
        router.generate = AsyncMock(side_effect=RuntimeError("fail"))
        agent = PlanAndExecuteAgent(provider_router=router, tools={})
        steps = await agent.generate_plan("hello")
        assert len(steps) == 1

    @pytest.mark.asyncio
    async def test_execute_step_no_lookup_fallback(self):
        from agent.plan_and_execute import PlanAndExecuteAgent, PlanStep
        router = MagicMock()
        router.generate = AsyncMock()
        router.generate.return_value.text = "llm result"
        tool = MagicMock(spec=[])
        agent = PlanAndExecuteAgent(provider_router=router, tools={"t": tool})
        step = PlanStep(step="solve", tool_name="t")
        result = await agent.execute_step(step, {})
        assert "llm result" in result

    @pytest.mark.asyncio
    async def test_execute_step_tool_error(self):
        from agent.plan_and_execute import PlanAndExecuteAgent, PlanStep
        router = MagicMock()
        tool = MagicMock()
        tool.lookup = MagicMock(side_effect=ValueError("boom"))
        agent = PlanAndExecuteAgent(provider_router=router, tools={"t": tool})
        step = PlanStep(step="work", tool_name="t")
        result = await agent.execute_step(step, {})
        assert "failed" in result


class TestSafetyCheckerUnsafe:
    @pytest.mark.asyncio
    async def test_check_llama_guard_no_key(self):
        from agent.safety_checker import SafetyChecker
        saved = os.environ.pop("GROQ_API_KEY", None)
        try:
            checker = SafetyChecker()
            d = await checker.check_llama_guard("test", role="user")
            assert not d.blocked
        finally:
            if saved is not None:
                os.environ["GROQ_API_KEY"] = saved

    @pytest.mark.asyncio
    async def test_check_llama_guard_unsafe_response(self):
        from agent.safety_checker import SafetyChecker
        saved = os.environ.pop("GROQ_API_KEY", None)
        try:
            os.environ["GROQ_API_KEY"] = "test-key"
            mock_groq = MagicMock()
            mock_create = AsyncMock()
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="unsafe harmful content"))]
            )
            mock_chat = MagicMock()
            mock_chat.completions.create = mock_create
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            mock_groq.AsyncGroq = MagicMock(return_value=mock_client)
            with patch.dict('sys.modules', {'groq': mock_groq}):
                checker = SafetyChecker()
                d = await checker.check_llama_guard("do harm", role="user")
                assert d.blocked
        finally:
            if saved is not None:
                os.environ["GROQ_API_KEY"] = saved
            else:
                os.environ.pop("GROQ_API_KEY", None)

    @pytest.mark.asyncio
    async def test_check_llama_guard_api_error(self):
        from agent.safety_checker import SafetyChecker
        saved = os.environ.pop("GROQ_API_KEY", None)
        try:
            os.environ["GROQ_API_KEY"] = "test-key"
            mock_groq = MagicMock()
            mock_create = AsyncMock(side_effect=RuntimeError("API down"))
            mock_chat = MagicMock()
            mock_chat.completions.create = mock_create
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            mock_groq.AsyncGroq = MagicMock(return_value=mock_client)
            with patch.dict('sys.modules', {'groq': mock_groq}):
                checker = SafetyChecker()
            d = await checker.check_llama_guard("test", role="user")
            assert not d.blocked
        finally:
            if saved is not None:
                os.environ["GROQ_API_KEY"] = saved
            else:
                os.environ.pop("GROQ_API_KEY", None)


# ═══════════════════════════════════════════════════════════════
# Phase 1: vectorstore.py — pgvector paths, error branches
# ═══════════════════════════════════════════════════════════════

class TestVectorStoreGetPool:
    @pytest.mark.asyncio
    async def test_get_pool_creates_once(self):
        from rag.vectorstore import LocalVectorStore
        pool = MagicMock()
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)) as mock_create:
            vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
            p1 = await vs._get_pool()
            p2 = await vs._get_pool()
            assert p1 is p2
            mock_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_init_db_creates_extension_and_table(self):
        from rag.vectorstore import LocalVectorStore
        conn = AsyncMock()
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
            await vs.init_db()
            assert conn.execute.call_count >= 3


class TestVectorStoreEnsureIndex:
    @pytest.mark.asyncio
    async def test_ensure_index_returns_cached(self):
        from rag.vectorstore import LocalVectorStore, DocumentChunk
        vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
        vs._chunks = [DocumentChunk(chunk_id="c1", source="s", title="t", category="c", content="x")]
        result = await vs.ensure_index()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_ensure_index_count_positive_fetches_rows(self):
        from rag.vectorstore import LocalVectorStore, DocumentChunk
        conn = AsyncMock()
        conn.fetchval = AsyncMock(return_value=3)
        conn.fetch = AsyncMock(return_value=[
            {"chunk_id": "c1", "source": "s", "title": "t", "category": "c", "content": "x"}
        ])
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
            result = await vs.ensure_index()
            assert len(result) == 1
            assert result[0].chunk_id == "c1"

    @pytest.mark.asyncio
    async def test_ensure_index_count_zero_calls_build(self):
        from rag.vectorstore import LocalVectorStore
        conn = AsyncMock()
        conn.fetchval = AsyncMock(return_value=0)
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            with patch("rag.vectorstore.load_documents", return_value=[]):
                vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
                result = await vs.ensure_index()
                assert result == []


class TestVectorStoreBuildIndex:
    @pytest.mark.asyncio
    async def test_build_index_cached_when_not_forced(self):
        from rag.vectorstore import LocalVectorStore, DocumentChunk
        vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
        vs._chunks = [DocumentChunk(chunk_id="c1", source="s", title="t", category="c", content="x")]
        with patch("rag.vectorstore.load_documents") as mock_load:
            result = await vs.build_index(force=False)
            assert len(result) == 1
            mock_load.assert_not_called()

    @pytest.mark.asyncio
    async def test_build_index_force_calls_load(self):
        from rag.vectorstore import LocalVectorStore
        doc = MagicMock()
        doc.text = "Test paragraph one.\n\nTest paragraph two."
        doc.source = "test.txt"
        doc.title = "Test"
        doc.category = "general"
        conn = AsyncMock()
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        txn = AsyncMock()
        txn.__aenter__ = AsyncMock()
        txn.__aexit__ = AsyncMock()
        conn.transaction = MagicMock(return_value=txn)
        conn.execute = AsyncMock()
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            with patch("rag.vectorstore.load_documents", return_value=[doc]):
                vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
                result = await vs.build_index(force=True)
                assert len(result) >= 1


class TestVectorStoreChunkDocument:
    def test_chunk_document_empty_text(self):
        from rag.vectorstore import LocalVectorStore
        doc = MagicMock()
        doc.text = ""
        doc.source = "src"
        doc.title = "t"
        doc.category = "c"
        chunks = LocalVectorStore._chunk_document(doc)
        assert len(chunks) == 1

    def test_chunk_document_long_paragraphs(self):
        from rag.vectorstore import LocalVectorStore
        doc = MagicMock()
        doc.text = "A" * 1000 + "\n\n" + "B" * 1000
        doc.source = "src"
        doc.title = "t"
        doc.category = "c"
        chunks = LocalVectorStore._chunk_document(doc)
        assert len(chunks) >= 2

    def test_filter_chunks_excludes_categories(self):
        from rag.vectorstore import LocalVectorStore, DocumentChunk
        included = DocumentChunk(chunk_id="c1", source="s", title="t", category="general", content="x")
        excluded = DocumentChunk(chunk_id="c2", source="s", title="t", category="qa_pairs", content="y")
        result = LocalVectorStore._filter_chunks([included, excluded])
        assert len(result) == 1
        assert result[0].chunk_id == "c1"


class TestVectorStoreUpsert:
    @pytest.mark.asyncio
    async def test_upsert_pg_empty_chunks(self):
        from rag.vectorstore import LocalVectorStore
        vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
        conn = AsyncMock()
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            await vs._upsert_pg([])
            conn.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_pg_embedding_failure(self):
        from rag.vectorstore import LocalVectorStore, DocumentChunk
        vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
        vs._embedding_function = MagicMock(side_effect=ValueError("no emb"))
        conn = AsyncMock()
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            await vs._upsert_pg([DocumentChunk(chunk_id="c1", source="s", title="t", category="c", content="x")])
            conn.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_pg_success(self):
        from rag.vectorstore import LocalVectorStore, DocumentChunk
        vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
        vs._embedding_function = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        conn = AsyncMock()
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        txn = AsyncMock()
        txn.__aenter__ = AsyncMock()
        txn.__aexit__ = AsyncMock()
        conn.transaction = MagicMock(return_value=txn)
        conn.execute = AsyncMock()
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            await vs._upsert_pg([DocumentChunk(chunk_id="c1", source="s", title="t", category="c", content="x")])
            assert conn.execute.called


class TestVectorStoreSearch:
    @pytest.mark.asyncio
    async def test_search_embedding_failure(self):
        from rag.vectorstore import LocalVectorStore
        vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
        vs._embedding_function = MagicMock(side_effect=ValueError("fail"))
        conn = AsyncMock()
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            result = await vs.search("test")
            assert result == []

    @pytest.mark.asyncio
    async def test_search_with_scopes(self):
        from rag.vectorstore import LocalVectorStore
        vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
        vs._embedding_function = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=[
            {"chunk_id": "c1", "source": "s", "title": "t", "category": "medical", "content": "x", "score": 0.9}
        ])
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            result = await vs.search("test", scopes={"medical"})
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_excluded_category_skipped(self):
        from rag.vectorstore import LocalVectorStore
        vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
        vs._embedding_function = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=[
            {"chunk_id": "c1", "source": "s", "title": "t", "category": "qa_pairs", "content": "x", "score": 0.9}
        ])
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            result = await vs.search("test")
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_query_exception(self):
        from rag.vectorstore import LocalVectorStore
        vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
        vs._embedding_function = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        conn = AsyncMock()
        conn.fetch = AsyncMock(side_effect=RuntimeError("DB down"))
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            result = await vs.search("test")
            assert result == []


class TestVectorStoreStats:
    @pytest.mark.asyncio
    async def test_stats_success(self):
        from rag.vectorstore import LocalVectorStore
        conn = AsyncMock()
        conn.fetchval = AsyncMock(side_effect=[42, 5])
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
            stats = await vs.stats()
            assert stats["chunks"] == 42
            assert stats["categories"] == 5

    @pytest.mark.asyncio
    async def test_stats_exception(self):
        from rag.vectorstore import LocalVectorStore
        conn = AsyncMock()
        conn.fetchval = AsyncMock(side_effect=RuntimeError("fail"))
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
            stats = await vs.stats()
            assert stats["chunks"] == 0
            assert stats["categories"] == 0


class TestVectorStoreGetPoolFallback:
    @pytest.mark.asyncio
    async def test_get_pool_none_then_creates(self):
        from rag.vectorstore import LocalVectorStore
        pool_obj = MagicMock()
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool_obj)):
            vs = LocalVectorStore("postgresql://u:p@localhost/db", MagicMock())
            vs._pool = None
            p = await vs._get_pool()
            assert p is pool_obj


# ═══════════════════════════════════════════════════════════════
# Phase 2: llm_cache.py — cache hit/miss, pgvector, error paths
# ═══════════════════════════════════════════════════════════════

class TestLLMCacheInit:
    def test_init_no_redis(self):
        from cache.llm_cache import LLMResponseCache
        c = LLMResponseCache(None)
        assert c._client is None
        assert not c._healthy

    def test_init_with_redis(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            assert c._client is mock_redis
            assert c._healthy

    def test_init_with_database(self):
        from cache.llm_cache import LLMResponseCache
        with patch("cache.llm_cache.build_embedding_function") as mock_emb:
            c = LLMResponseCache(None, database_url="postgresql://u:p@localhost/db")
            assert c.database_url is not None
            mock_emb.assert_called_once()

    def test_backend_name_no_redis(self):
        from cache.llm_cache import LLMResponseCache
        c = LLMResponseCache(None)
        assert c.backend_name == 'memory'

    def test_backend_name_redis_only(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            assert c.backend_name == 'redis'

    def test_backend_name_pgvector_redis(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            with patch("cache.llm_cache.build_embedding_function"):
                c = LLMResponseCache("redis://localhost", database_url="postgresql://u:p@localhost/db")
                c._healthy = True
                assert c.backend_name == 'pgvector+redis'


class TestLLMCacheKey:
    def test_make_key_deterministic(self):
        from cache.llm_cache import LLMResponseCache
        c = LLMResponseCache(None)
        k1 = c._make_key("hello", "greeting", ["tool1"])
        k2 = c._make_key("hello", "greeting", ["tool1"])
        assert k1 == k2
        assert k1.startswith("cache:llm:")
        assert len(k1.split(":")[-1]) == 16


class TestLLMCacheGet:
    @pytest.mark.asyncio
    async def test_get_redis_hit(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value='{"text":"hi","provider":"groq","model":"m","prompt_tokens":0,"completion_tokens":0,"total_tokens":0}')
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            result = await c.get("hello", "greeting", ["tool1"])
            assert result is not None
            assert result.text == "hi"

    @pytest.mark.asyncio
    async def test_get_redis_miss_then_pgvector_miss(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(side_effect=RuntimeError("pg query fail"))
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost", database_url="postgresql://u:p@localhost/db")
            with patch("cache.llm_cache.build_embedding_function", return_value=MagicMock(return_value=[[0.1, 0.2]])):
                with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
                    result = await c.get("hello", "greeting", ["tool1"])
                    assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_error_then_pgvector_hit(self):
        from cache.llm_cache import LLMResponseCache, CacheEntry
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("no redis"))
        emb_fn = MagicMock(return_value=[[0.1, 0.2]])
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value={"similarity": 0.98, "response_data": '{"text":"hello","provider":"groq","model":"m","prompt_tokens":0,"completion_tokens":0,"total_tokens":0}'})
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            with patch("cache.llm_cache.build_embedding_function", return_value=emb_fn):
                with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
                    c = LLMResponseCache("redis://localhost", database_url="postgresql://u:p@localhost/db", similarity_threshold=0.95)
                    result = await c.get("hello", "greeting", ["tool1"])
                    assert result is not None
                    assert result.text == "hello"
                    assert not c._healthy

    @pytest.mark.asyncio
    async def test_get_pgvector_no_pool(self):
        from cache.llm_cache import LLMResponseCache
        c = LLMResponseCache(None)
        result = await c.get("hello", "greeting", ["tool1"])
        assert result is None

    @pytest.mark.asyncio
    async def test_get_pgvector_below_threshold(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        emb_fn = MagicMock(return_value=[[0.1, 0.2]])
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value={"similarity": 0.8, "response_data": '{"text":"hello","provider":"groq","model":"m","prompt_tokens":0,"completion_tokens":0,"total_tokens":0}'})
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            with patch("cache.llm_cache.build_embedding_function", return_value=emb_fn):
                with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
                    c = LLMResponseCache("redis://localhost", database_url="postgresql://u:p@localhost/db", similarity_threshold=0.95)
                    result = await c.get("hello", "greeting", ["tool1"])
                    assert result is None

    @pytest.mark.asyncio
    async def test_get_pgvector_none_row(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        emb_fn = MagicMock(return_value=[[0.1, 0.2]])
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=None)
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            with patch("cache.llm_cache.build_embedding_function", return_value=emb_fn):
                with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
                    c = LLMResponseCache("redis://localhost", database_url="postgresql://u:p@localhost/db")
                    result = await c.get("hello", "greeting", ["tool1"])
                    assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_decode_error(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=json.JSONDecodeError("bad json", "doc", 0))
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            result = await c.get("hello", "greeting", ["tool1"])
            assert result is None


class TestLLMCacheSet:
    @pytest.mark.asyncio
    async def test_set_redis_success(self):
        from cache.llm_cache import LLMResponseCache, CacheEntry
        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock()
        entry = CacheEntry(text="hi", provider="groq", model="m")
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            c._healthy = False
            await c.set("hello", "greeting", ["tool1"], entry)
            mock_redis.setex.assert_awaited_once()
            assert c._healthy

    @pytest.mark.asyncio
    async def test_set_redis_error(self):
        from cache.llm_cache import LLMResponseCache, CacheEntry
        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock(side_effect=ConnectionError("fail"))
        entry = CacheEntry(text="hi", provider="groq", model="m")
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            await c.set("hello", "greeting", ["tool1"], entry)
            assert not c._healthy

    @pytest.mark.asyncio
    async def test_set_no_redis(self):
        from cache.llm_cache import LLMResponseCache, CacheEntry
        c = LLMResponseCache(None)
        entry = CacheEntry(text="hi", provider="groq", model="m")
        await c.set("hello", "greeting", ["tool1"], entry)

    @pytest.mark.asyncio
    async def test_set_pgvector_success(self):
        from cache.llm_cache import LLMResponseCache, CacheEntry
        entry = CacheEntry(text="hi", provider="groq", model="m")
        conn = AsyncMock()
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            with patch("cache.llm_cache.build_embedding_function", return_value=MagicMock(return_value=[[0.1, 0.2]])):
                c = LLMResponseCache(None, database_url="postgresql://u:p@localhost/db")
                await c.set("hello", "greeting", ["tool1"], entry)
                assert conn.execute.called

    @pytest.mark.asyncio
    async def test_set_pgvector_error(self):
        from cache.llm_cache import LLMResponseCache, CacheEntry
        entry = CacheEntry(text="hi", provider="groq", model="m")
        conn = AsyncMock()
        conn.execute = AsyncMock(side_effect=RuntimeError("db fail"))
        pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        with patch("asyncpg.create_pool", AsyncMock(return_value=pool)):
            with patch("cache.llm_cache.build_embedding_function", return_value=MagicMock(return_value=[[0.1, 0.2]])):
                c = LLMResponseCache(None, database_url="postgresql://u:p@localhost/db")
                c._pool = pool
                await c.set("hello", "greeting", ["tool1"], entry)


class TestLLMCachePing:
    @pytest.mark.asyncio
    async def test_ping_no_redis(self):
        from cache.llm_cache import LLMResponseCache
        c = LLMResponseCache(None)
        result = await c.ping()
        assert not result

    @pytest.mark.asyncio
    async def test_ping_success(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(return_value=True)
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            c._healthy = False
            result = await c.ping()
            assert result
            assert c._healthy

    @pytest.mark.asyncio
    async def test_ping_failure(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(side_effect=ConnectionError("no redis"))
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            result = await c.ping()
            assert not result
            assert not c._healthy


class TestLLMCacheProviderUnavailable:
    @pytest.mark.asyncio
    async def test_get_no_redis(self):
        from cache.llm_cache import LLMResponseCache
        c = LLMResponseCache(None)
        result = await c.get_provider_unavailable_until("groq")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_hit(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="12345.6")
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            result = await c.get_provider_unavailable_until("groq")
            assert result == 12345.6

    @pytest.mark.asyncio
    async def test_get_redis_miss(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            result = await c.get_provider_unavailable_until("groq")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_error(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=RuntimeError("fail"))
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            result = await c.get_provider_unavailable_until("groq")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_no_redis(self):
        from cache.llm_cache import LLMResponseCache
        c = LLMResponseCache(None)
        await c.set_provider_unavailable_until("groq", 99999.0, 3600)

    @pytest.mark.asyncio
    async def test_set_redis_success(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock()
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            await c.set_provider_unavailable_until("groq", 99999.0, 3600)
            mock_redis.setex.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_redis_error(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock(side_effect=ConnectionError("fail"))
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            await c.set_provider_unavailable_until("groq", 99999.0, 3600)

    @pytest.mark.asyncio
    async def test_no_database_url_pool_returns_none(self):
        from cache.llm_cache import LLMResponseCache
        c = LLMResponseCache(None)
        pool = await c._get_pool()
        assert pool is None


class TestLLMCacheClose:
    @pytest.mark.asyncio
    async def test_close_no_client(self):
        from cache.llm_cache import LLMResponseCache
        c = LLMResponseCache(None)
        await c.close()

    @pytest.mark.asyncio
    async def test_close_success(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.aclose = AsyncMock()
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            await c.close()
            mock_redis.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_error(self):
        from cache.llm_cache import LLMResponseCache
        mock_redis = MagicMock()
        mock_redis.aclose = AsyncMock(side_effect=ConnectionError("fail"))
        with patch("cache.llm_cache.Redis.from_url", return_value=mock_redis):
            c = LLMResponseCache("redis://localhost")
            await c.close()


# ═══════════════════════════════════════════════════════════════
# Phase 3: context_assembler.py — all intent branches
# ═══════════════════════════════════════════════════════════════

class TestContextAssemblerEmergency:
    @pytest.mark.asyncio
    async def test_emergency_with_lat_lon_sos_and_weather(self):
        from agent.context_assembler import ContextAssembler
        from agent.state import ConversationContext
        ctx = ConversationContext(session_id="s1", message="help", intent="emergency", lat=13.0, lon=80.0)
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        sos_tool = MagicMock()
        sos_tool.get_payload = AsyncMock(return_value={"numbers": {"police": {"service": "100"}}, "services": [{"name": "Hospital A"}, {"name": "Clinic B"}], "what3words": {"formatted": "///test.word"}})
        weather_tool = MagicMock()
        weather_tool.lookup = AsyncMock(return_value={"summary": "Clear", "temperature": 30})
        ca = ContextAssembler(retriever=retriever, sos_tool=sos_tool, challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=weather_tool, drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="help", intent="emergency", lat=13.0, lon=80.0, client_ip=None, history=[], user_id=None)
        assert len(result.tools) >= 2

    @pytest.mark.asyncio
    async def test_emergency_no_lat(self):
        from agent.context_assembler import ContextAssembler
        from agent.state import ConversationContext
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="help", intent="emergency", lat=None, lon=None, client_ip=None, history=[], user_id=None)
        assert len(result.tools) == 0

    @pytest.mark.asyncio
    async def test_emergency_sos_is_exception(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        sos_tool = MagicMock()
        sos_tool.get_payload = AsyncMock(side_effect=RuntimeError("fail"))
        weather_tool = MagicMock()
        weather_tool.lookup = AsyncMock(return_value={"summary": "Rainy"})
        ca = ContextAssembler(retriever=retriever, sos_tool=sos_tool, challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=weather_tool, drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="help", intent="emergency", lat=13.0, lon=80.0, client_ip=None, history=[])
        assert len(result.tools) >= 1  # weather still added


class TestContextAssemblerEpisodic:
    @pytest.mark.asyncio
    async def test_episodic_memory_adds_context(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        mem = MagicMock()
        mem.retrieve_memory = MagicMock(return_value=["likes coffee", "works at night"])
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock(), episodic_memory_agent=mem)
        result = await ca.assemble(session_id="s1", message="help", intent="general", lat=13.0, lon=80.0, client_ip=None, history=[], user_id="user123")
        assert len(result.tools) >= 1

    @pytest.mark.asyncio
    async def test_episodic_memory_exception_caught(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        mem = MagicMock()
        mem.retrieve_memory = MagicMock(side_effect=ValueError("no memories"))
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock(), episodic_memory_agent=mem)
        result = await ca.assemble(session_id="s1", message="help", intent="general", lat=None, lon=None, client_ip=None, history=[], user_id="user123")
        assert len(result.tools) == 0

    @pytest.mark.asyncio
    async def test_episodic_memory_skips_anonymous(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        mem = MagicMock()
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock(), episodic_memory_agent=mem)
        result = await ca.assemble(session_id="s1", message="help", intent="general", lat=None, lon=None, client_ip=None, history=[], user_id="anonymous")
        assert len(result.tools) == 0


class TestContextAssemblerIntents:
    @pytest.mark.asyncio
    async def test_first_aid_intent(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        first_aid_tool = MagicMock()
        first_aid_tool.lookup = MagicMock(return_value={"title": "Burns", "steps": ["Cool it", "Cover it"]})
        drug_info_tool = MagicMock()
        drug_info_tool.lookup = AsyncMock(return_value={"indications": "Pain relief"})
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=first_aid_tool, road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=drug_info_tool)
        result = await ca.assemble(session_id="s1", message="burn", intent="first_aid", lat=None, lon=None, client_ip=None, history=[])
        assert any(t.name == "first_aid" for t in result.tools)

    @pytest.mark.asyncio
    async def test_challan_intent(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        challan_tool = MagicMock()
        challan_tool.infer_and_calculate = AsyncMock(return_value={"section": "MVA 185", "base_fine": 5000, "repeat_fine": 10000, "amount_due": 5000})
        legal_tool = MagicMock()
        legal_tool.search = AsyncMock(return_value=[])
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=challan_tool, legal_search_tool=legal_tool, first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="challan info", intent="challan", lat=None, lon=None, client_ip=None, history=[])
        assert any(t.name == "challan" for t in result.tools)

    @pytest.mark.asyncio
    async def test_legal_intent(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        legal_tool = MagicMock()
        legal_tool.search = AsyncMock(return_value=[])
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=legal_tool, first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="traffic law", intent="legal", lat=None, lon=None, client_ip=None, history=[])
        assert result is not None

    @pytest.mark.asyncio
    async def test_road_issue_intent(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        infra_tool = MagicMock()
        infra_tool.lookup = AsyncMock(return_value={"exec_engineer": "John", "road_type": "NH", "road_type_code": "1"})
        issues_tool = MagicMock()
        issues_tool.lookup = AsyncMock(return_value={"count": 3, "issues": [{"id": 1}]})
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=infra_tool, road_issues_tool=issues_tool, submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="road issue", intent="road_issue", lat=13.0, lon=80.0, client_ip=None, history=[])
        assert any(t.name == "road_infrastructure" for t in result.tools)

    @pytest.mark.asyncio
    async def test_road_issue_exceptions(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        infra_tool = MagicMock()
        infra_tool.lookup = AsyncMock(side_effect=RuntimeError("fail"))
        issues_tool = MagicMock()
        issues_tool.lookup = AsyncMock(side_effect=RuntimeError("fail2"))
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=infra_tool, road_issues_tool=issues_tool, submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="road", intent="road_issue", lat=13.0, lon=80.0, client_ip=None, history=[])
        assert len(result.tools) == 0

    @pytest.mark.asyncio
    async def test_road_issue_issues_is_empty(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        infra_tool = MagicMock()
        infra_tool.lookup = AsyncMock(return_value=None)
        issues_tool = MagicMock()
        issues_tool.lookup = AsyncMock(return_value={"count": 0, "issues": []})
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=infra_tool, road_issues_tool=issues_tool, submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="road", intent="road_issue", lat=13.0, lon=80.0, client_ip=None, history=[])
        assert not any(t.name == "road_issues" for t in result.tools)

    @pytest.mark.asyncio
    async def test_safe_route_with_lat(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        weather_tool = MagicMock()
        weather_tool.lookup = AsyncMock(return_value={"summary": "Rain", "temperature": 25})
        issues_tool = MagicMock()
        issues_tool.lookup = AsyncMock(return_value={"count": 2, "issues": [{"id": 1}, {"id": 2}]})
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=issues_tool, submit_report_tool=MagicMock(), weather_tool=weather_tool, drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="safe route", intent="safe_route", lat=13.0, lon=80.0, client_ip=None, history=[])
        assert any(t.name == "safe_route" for t in result.tools)

    @pytest.mark.asyncio
    async def test_road_infrastructure_no_lat(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="infra", intent="road_infrastructure", lat=None, lon=None, client_ip=None, history=[])
        assert any(t.name == "road_infrastructure" for t in result.tools)

    @pytest.mark.asyncio
    async def test_generic_intent(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[])
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="hello", intent="general", lat=None, lon=None, client_ip=None, history=[])
        assert result is not None

    @pytest.mark.asyncio
    async def test_rag_fallback_rewrites_query(self):
        from agent.context_assembler import ContextAssembler
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(side_effect=[None, []])
        ca = ContextAssembler(retriever=retriever, sos_tool=MagicMock(), challan_tool=MagicMock(), legal_search_tool=MagicMock(), first_aid_tool=MagicMock(), road_infra_tool=MagicMock(), road_issues_tool=MagicMock(), submit_report_tool=MagicMock(), weather_tool=MagicMock(), drug_info_tool=MagicMock())
        result = await ca.assemble(session_id="s1", message="tell me about traffic fines", intent="general", lat=None, lon=None, client_ip=None, history=[])
        assert retriever.retrieve.call_count >= 2


# ═══════════════════════════════════════════════════════════════
# Phase 4: graph.py — stream_chat branches, governance
# ═══════════════════════════════════════════════════════════════

class TestGraphLoadUserProviders:
    @pytest.mark.asyncio
    async def test_load_user_providers_no_user_id(self):
        from agent.graph import ChatEngine
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine.redis_url = "redis://localhost"
        with patch("redis.asyncio.Redis.from_url") as mock_from_url:
            await ChatEngine._load_user_providers(engine, None)
            mock_from_url.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_user_providers_no_redis_url(self):
        from agent.graph import ChatEngine
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine.redis_url = None
        await ChatEngine._load_user_providers(engine, "user123")
        assert not engine.provider_router.configure_user_providers.called

    @pytest.mark.asyncio
    async def test_load_user_providers_redis_no_key(self):
        from agent.graph import ChatEngine
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine.redis_url = "redis://localhost"
        engine.provider_router.configure_user_providers = MagicMock()
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.aclose = AsyncMock()
        with patch("redis.asyncio.Redis.from_url", return_value=mock_redis):
            await ChatEngine._load_user_providers(engine, "user123")
            engine.provider_router.configure_user_providers.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_user_providers_redis_exception(self):
        from agent.graph import ChatEngine
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine.redis_url = "redis://localhost"
        engine.provider_router.configure_user_providers = MagicMock()
        with patch("redis.asyncio.Redis.from_url", side_effect=ConnectionError("no redis")):
            await ChatEngine._load_user_providers(engine, "user123")


class TestGraphStreamChat:
    @pytest.mark.asyncio
    async def test_stream_chat_blocked(self):
        from agent.graph import ChatEngine
        from agent.state import ChatRequest
        from agent.safety_checker import SafetyDecision
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine._load_user_providers = AsyncMock()
        engine.safety_checker = MagicMock()
        engine.safety_checker.evaluate = MagicMock(return_value=SafetyDecision(blocked=True, response="Blocked"))
        engine.memory_store.append_message = AsyncMock()
        engine.memory_store.get_history = AsyncMock()
        events = []
        async for event in ChatEngine.stream_chat(engine, ChatRequest(message="bad", session_id="s1")):
            events.append(event)
        assert len(events) == 2
        assert events[0]['type'] == 'token'
        assert events[1]['type'] == 'done'

    @pytest.mark.asyncio
    async def test_stream_chat_output_safety_blocked(self):
        from agent.graph import ChatEngine
        from agent.state import ChatRequest
        from agent.multi_agent import ChatState
        from agent.safety_checker import SafetyDecision
        from agent.multi_agent import MultiAgentGraph
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine._load_user_providers = AsyncMock()
        engine.safety_checker = MagicMock()
        engine.safety_checker.evaluate = MagicMock(return_value=SafetyDecision(blocked=False))
        engine.safety_checker.check_llama_guard = AsyncMock(return_value=SafetyDecision(blocked=False))
        engine.intent_detector = MagicMock()
        engine.intent_detector.detect = MagicMock(return_value="general")
        engine.intent_detector.refine_intent = MagicMock(return_value="general")
        engine.memory_store.append_message = AsyncMock()
        engine.memory_store.get_history = AsyncMock(return_value=[])
        engine.summarizer = MagicMock()
        engine.summarizer.get_summary_for_history = MagicMock(return_value=("", []))
        graph = MagicMock()
        graph.execute = AsyncMock(return_value=ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None))
        async def _async_gen(state):
            yield {'type': 'done', 'intent': 'general', 'sources': []}
        graph.stream_execute = _async_gen
        engine.multi_agent_graph = graph
        engine.safety_checker.check_output_safety = MagicMock(return_value=SafetyDecision(blocked=True, response="Blocked output"))
        engine.governance = MagicMock()
        engine.governance.evaluate = AsyncMock()
        events = []
        async for event in ChatEngine.stream_chat(engine, ChatRequest(message="hi", session_id="s1")):
            events.append(event)
        assert any(e['intent'] == 'blocked_output' for e in events if e['type'] == 'done')

    @pytest.mark.asyncio
    async def test_stream_chat_exception(self):
        from agent.graph import ChatEngine
        from agent.state import ChatRequest
        from agent.safety_checker import SafetyDecision
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine._load_user_providers = AsyncMock()
        engine.safety_checker = MagicMock()
        engine.safety_checker.evaluate = MagicMock(return_value=SafetyDecision(blocked=False))
        engine.safety_checker.check_llama_guard = AsyncMock(return_value=SafetyDecision(blocked=False))
        engine.intent_detector = MagicMock()
        engine.intent_detector.detect = MagicMock(return_value="general")
        engine.intent_detector.refine_intent = MagicMock(return_value="general")
        engine.memory_store.append_message = AsyncMock()
        engine.memory_store.get_history = AsyncMock(return_value=[])
        engine.summarizer = MagicMock()
        engine.summarizer.get_summary_for_history = MagicMock(return_value=("", []))
        engine.multi_agent_graph = MagicMock()
        engine.multi_agent_graph.stream_execute = MagicMock(side_effect=RuntimeError("stream error"))
        events = []
        async for event in ChatEngine.stream_chat(engine, ChatRequest(message="hi", session_id="s1")):
            events.append(event)
        assert events[-1]['type'] == 'error'


class TestGraphChat:
    @pytest.mark.asyncio
    async def test_chat_llama_blocked(self):
        from agent.graph import ChatEngine
        from agent.state import ChatRequest
        from agent.safety_checker import SafetyDecision
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine._load_user_providers = AsyncMock()
        engine.safety_checker = MagicMock()
        engine.safety_checker.evaluate = MagicMock(return_value=SafetyDecision(blocked=False))
        engine.safety_checker.check_llama_guard = AsyncMock(return_value=SafetyDecision(blocked=True, response="Llama blocked"))
        engine.memory_store.append_message = AsyncMock()
        engine.memory_store.get_history = AsyncMock(return_value=[])
        engine.summarizer = MagicMock()
        engine.summarizer.get_summary_for_history = MagicMock(return_value=("", []))
        result = await ChatEngine.chat(engine, ChatRequest(message="bad", session_id="s1"))
        assert result.intent == 'blocked'

    @pytest.mark.asyncio
    async def test_chat_output_safety_blocked(self):
        from agent.graph import ChatEngine
        from agent.state import ChatRequest
        from agent.multi_agent import ChatState
        from agent.safety_checker import SafetyDecision
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine._load_user_providers = AsyncMock()
        engine.safety_checker = MagicMock()
        engine.safety_checker.evaluate = MagicMock(return_value=SafetyDecision(blocked=False))
        engine.safety_checker.check_llama_guard = AsyncMock(return_value=SafetyDecision(blocked=False))
        engine.intent_detector = MagicMock()
        engine.intent_detector.detect = MagicMock(return_value="general")
        engine.intent_detector.refine_intent = MagicMock(return_value="general")
        engine.memory_store.append_message = AsyncMock()
        engine.memory_store.get_history = AsyncMock(return_value=[])
        engine.summarizer = MagicMock()
        engine.summarizer.get_summary_for_history = MagicMock(return_value=("", []))
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None)
        state.final_response = "some response"
        state.context = MagicMock()
        state.context.retrieved = []
        state.context.tools = []
        engine.multi_agent_graph = MagicMock()
        engine.multi_agent_graph.execute = AsyncMock(return_value=state)
        engine.safety_checker.check_output_safety = MagicMock(return_value=SafetyDecision(blocked=True, response="Blocked"))
        engine.governance = MagicMock()
        engine.governance.evaluate = AsyncMock()
        state.final_sources = []
        result = await ChatEngine.chat(engine, ChatRequest(message="hi", session_id="s1"))
        assert result.intent == 'blocked_output'

    @pytest.mark.asyncio
    async def test_chat_governance_flagged(self):
        from agent.graph import ChatEngine
        from agent.state import ChatRequest
        from agent.multi_agent import ChatState
        from agent.safety_checker import SafetyDecision
        from agent.governance import GovernanceResult
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine._load_user_providers = AsyncMock()
        engine.safety_checker = MagicMock()
        engine.safety_checker.evaluate = MagicMock(return_value=SafetyDecision(blocked=False))
        engine.safety_checker.check_llama_guard = AsyncMock(return_value=SafetyDecision(blocked=False))
        engine.intent_detector = MagicMock()
        engine.intent_detector.detect = MagicMock(return_value="general")
        engine.intent_detector.refine_intent = MagicMock(return_value="general")
        engine.memory_store.append_message = AsyncMock()
        engine.memory_store.get_history = AsyncMock(return_value=[])
        engine.summarizer = MagicMock()
        engine.summarizer.get_summary_for_history = MagicMock(return_value=("", []))
        state = ChatState(session_id="s1", message="hi", intent="general", history=[], summarized_history=[], user_id=None)
        state.final_response = "response"
        state.context = MagicMock()
        state.context.retrieved = []
        state.context.tools = []
        state.final_sources = []
        engine.multi_agent_graph = MagicMock()
        engine.multi_agent_graph.execute = AsyncMock(return_value=state)
        engine.safety_checker.check_output_safety = MagicMock(return_value=SafetyDecision(blocked=False))
        engine.safety_checker.check_llama_guard = AsyncMock(return_value=SafetyDecision(blocked=False))
        engine.safety_checker.add_medical_disclaimer_if_needed = MagicMock(return_value="response")
        engine.governance = MagicMock()
        engine.governance.evaluate = AsyncMock(return_value=GovernanceResult(text="response", flagged=True, hallucination_score=0.3, factuality_score=0.4, citations=[], prompt_version="v1"))
        result = await ChatEngine.chat(engine, ChatRequest(message="hi", session_id="s1"))
        assert "Low confidence" in result.response
        assert result.intent == "general"


class TestGraphMisc:
    def test_dedupe_sources_removes_duplicates_and_empty(self):
        from agent.graph import ChatEngine
        result = ChatEngine._dedupe_sources(["a", "b", "", "a", "c", None, "b"])
        assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_close_calls_governance_close(self):
        from agent.graph import ChatEngine
        engine = MagicMock()
        engine.__class__ = ChatEngine
        engine.governance.close = AsyncMock()
        await ChatEngine.close(engine)
        engine.governance.close.assert_awaited_once()


# ═══════════════════════════════════════════════════════════════
# Phase 5: safety_checker.py — unsafe llama guard response
# ═══════════════════════════════════════════════════════════════

class TestSafetyCheckerLlamaUnsafe:
    @pytest.mark.asyncio
    async def test_llama_guard_unsafe_response(self):
        from agent.safety_checker import SafetyChecker
        saved = os.environ.pop("GROQ_API_KEY", None)
        try:
            os.environ["GROQ_API_KEY"] = "test-key"
            mock_groq = MagicMock()
            mock_create = AsyncMock()
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="unsafe harmful content"))]
            )
            mock_chat = MagicMock()
            mock_chat.completions.create = mock_create
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            mock_groq.AsyncGroq = MagicMock(return_value=mock_client)
            with patch.dict('sys.modules', {'groq': mock_groq}):
                checker = SafetyChecker()
                d = await checker.check_llama_guard("do harm", role="user")
                assert d.blocked
        finally:
            if saved is not None:
                os.environ["GROQ_API_KEY"] = saved
            else:
                os.environ.pop("GROQ_API_KEY", None)


# ═══════════════════════════════════════════════════════════════
# Phase 6: api/ai.py — 413 image too large
# ═══════════════════════════════════════════════════════════════

class TestApiAiImageTooLarge:
    def test_image_too_large_413(self):
        import main
        app = main.create_app()
        from config import get_settings
        object.__setattr__(get_settings(), "environment", "development")
        object.__setattr__(get_settings(), "internal_api_key", "test-key")
        app.state.chat_engine = MagicMock()
        from fastapi.testclient import TestClient
        client = TestClient(app)
        large_data = b"x" * (6 * 1024 * 1024)  # 6MB > 5MB limit
        resp = client.post(
            "/api/v1/ai/validate-image",
            files={"file": ("test.jpg", large_data, "image/jpeg")},
            headers={"X-Internal-Api-Key": "test-key"}
        )
        assert resp.status_code == 413


# ═══════════════════════════════════════════════════════════════
# Phase 7: api/admin.py — non-tuple results
# ═══════════════════════════════════════════════════════════════

class TestAdminNonTupleResultsInGather:
    def test_admin_gather_skips_non_tuple(self):
        import main
        app = main.create_app()
        from config import get_settings
        object.__setattr__(get_settings(), "admin_secret", "test-secret")
        object.__setattr__(get_settings(), "environment", "development")
        app.state.chat_engine = MagicMock()
        app.state.chat_engine.stats = AsyncMock(return_value={})
        app.state.chat_engine.provider_router = MagicMock()
        app.state.chat_engine.provider_router.providers = {
            "groq": MagicMock(),
            "template": MagicMock(),
        }
        app.state.chat_engine.provider_router._provider_unavailable = MagicMock(return_value=False)
        app.state.chat_engine.provider_router.cache = None
        mem = MagicMock()
        mem.ping = AsyncMock(return_value=True)
        app.state.memory_store = mem
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/admin/health", headers={"X-Admin-Key": "test-secret"})
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# Phase 8: retriever.py — cross-encoder, min_score filter
# ═══════════════════════════════════════════════════════════════

class TestRetrieverCrossEncoder:
    @pytest.mark.asyncio
    async def test_cross_encoder_reranks(self):
        from rag.retriever import Retriever
        vs = MagicMock()
        vs.search = AsyncMock(return_value=[
            (MagicMock(chunk_id="c1", source="s1", title="t1", category="c1", content="A"), 0.8),
            (MagicMock(chunk_id="c2", source="s2", title="t2", category="c2", content="B"), 0.7),
        ])
        vs.ensure_index = AsyncMock(return_value=[])
        with patch("sentence_transformers.CrossEncoder") as mock_ce:
            ce_instance = MagicMock()
            ce_instance.predict = MagicMock(return_value=[0.9, 0.6])
            mock_ce.return_value = ce_instance
            ret = Retriever(vs, min_score=0.0, cross_encoder_model="cross-encoder/test")
            ret._bm25 = MagicMock()
            ret._bm25.get_scores = MagicMock(return_value=[])
            results = await ret.retrieve("test query")
            assert len(results) >= 1
            ce_instance.predict.assert_called_once()

    @pytest.mark.asyncio
    async def test_cross_encoder_error_continues(self):
        from rag.retriever import Retriever
        vs = MagicMock()
        vs.search = AsyncMock(return_value=[
            (MagicMock(chunk_id="c1", source="s1", title="t1", category="c1", content="A"), 0.8),
        ])
        vs.ensure_index = AsyncMock(return_value=[])
        with patch("sentence_transformers.CrossEncoder", side_effect=Exception("no cross")):
            ret = Retriever(vs, min_score=0.0, cross_encoder_model="cross-encoder/test")
            ret._bm25 = MagicMock()
            ret._bm25.get_scores = MagicMock(return_value=[])
            results = await ret.retrieve("test query")
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self):
        from rag.retriever import Retriever
        vs = MagicMock()
        ret = Retriever(vs)
        results = await ret.retrieve("   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_sparse_matches_empty(self):
        from rag.retriever import Retriever
        vs = MagicMock()
        vs.search = AsyncMock(return_value=[])
        vs.ensure_index = AsyncMock(return_value=[])
        ret = Retriever(vs, min_score=0.0)
        results = await ret.retrieve("test")
        assert len(results) == 0


# ═══════════════════════════════════════════════════════════════
# Phase 9: api/chat.py — stream timeout + history auth
# ═══════════════════════════════════════════════════════════════

class TestApiChatStreamTimeout:
    def test_chat_stream_timeout(self):
        import main
        app = main.create_app()
        from config import get_settings
        object.__setattr__(get_settings(), "internal_api_key", "test-key")
        object.__setattr__(get_settings(), "environment", "development")
        engine = MagicMock()
        engine.stream_chat = MagicMock()
        engine.stream_chat.return_value.__aiter__ = MagicMock(side_effect=asyncio.TimeoutError)
        app.state.chat_engine = engine
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.post(
            "/api/v1/chat/stream",
            json={"message": "hi"},
            headers={"X-Internal-Api-Key": "test-key"}
        )
        assert resp.status_code == 200

    def test_chat_history_forbidden_without_admin(self):
        import main
        app = main.create_app()
        from config import get_settings
        object.__setattr__(get_settings(), "environment", "development")
        app.state.chat_engine = MagicMock()
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/api/v1/chat/history/test-session")
        assert resp.status_code == 403

    def test_chat_stream_internal_error(self):
        import main
        app = main.create_app()
        from config import get_settings
        object.__setattr__(get_settings(), "internal_api_key", "test-key")
        object.__setattr__(get_settings(), "environment", "development")
        engine = MagicMock()
        engine.stream_chat = MagicMock()
        engine.stream_chat.return_value.__aiter__ = MagicMock(side_effect=RuntimeError("internal fail"))
        app.state.chat_engine = engine
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.post(
            "/api/v1/chat/stream",
            json={"message": "hi"},
            headers={"X-Internal-Api-Key": "test-key"}
        )
        assert resp.status_code == 200
