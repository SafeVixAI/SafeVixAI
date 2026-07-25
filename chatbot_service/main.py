# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
# CI trigger: verify notify-failure fix
from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from agent.context_assembler import ContextAssembler
from agent.graph import ChatEngine
from agent.intent_detector import IntentDetector
from agent.safety_checker import SafetyChecker
from api import api_router
from cache.llm_cache import LLMResponseCache
from config import get_settings

# P2-02: Structured JSON logging (audit H35) — mirrors backend/core/logging.py
from core.logging import configure_logging
from limiter import limiter
from memory.redis_memory import ConversationMemoryStore
from memory.tiered_memory import TieredMemory
from memory.user_memory import UserPreferenceStore
from middleware.correlation_id import setup_correlation_id
from middleware.query_profiler import setup_query_profiler
from providers.router import ProviderRouter
from rag.retriever import Retriever
from rag.vectorstore import LocalVectorStore
from services import IndicSeamlessService
from tools import (
    BackendToolClient,
    ChallanTool,
    DrugInfoTool,
    FirstAidTool,
    GeocodingClient,
    LegalSearchTool,
    RoadInfrastructureTool,
    RoadIssuesTool,
    SosTool,
    SubmitReportTool,
    WeatherTool,
    What3WordsTool,
)

logger = configure_logging(get_settings().environment, "safevixai.chatbot")


def create_app() -> FastAPI:
    settings = get_settings()

    # OBSERVABILITY#1: Sentry error tracking (free tier: 5K errors/month)
    if settings.sentry_dsn and sentry_sdk is not None:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        import asyncio
        import signal
        _shutdown_requested = False
        def _handle_signal():
            nonlocal _shutdown_requested
            _shutdown_requested = True  # pragma: no cover
            logger.info("Chatbot received shutdown signal — draining connections")  # pragma: no cover
        try:
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):  # pragma: no branch
                loop.add_signal_handler(sig, _handle_signal)
        except (NotImplementedError, ValueError, RuntimeError):
            logger.warning("Signal handlers not supported on this platform")

        backend_client = BackendToolClient(settings)
        memory_store = ConversationMemoryStore(
            settings.redis_url,
            session_ttl_seconds=settings.session_ttl_seconds,
        )
        vectorstore = LocalVectorStore(
            database_url=settings.database_url,
            data_dir=settings.rag_data_dir,
            embedding_model=settings.embedding_model,
        )
        # User preference store and tiered memory
        user_pref_store = UserPreferenceStore(redis_url=settings.redis_url)
        tiered_memory = TieredMemory(pref_store=user_pref_store, episodic_agent=None)

        retriever = Retriever(
            vectorstore,
            default_top_k=settings.top_k_retrieval,
            min_score=settings.rag_min_score,
            cross_encoder_model=settings.rag_reranker,
            redis_url=settings.redis_url,
        )
        weather_tool = WeatherTool(settings)
        speech_service = IndicSeamlessService(settings)
        w3w_tool = What3WordsTool(api_key=settings.w3w_api_key)
        geocode_client = GeocodingClient(opencage_key=settings.opencage_api_key)
        drug_info_tool = DrugInfoTool()

        submit_report_tool = SubmitReportTool(settings.main_backend_base_url)

        # C9: Initialize LLM response cache
        llm_cache = LLMResponseCache(settings.redis_url, database_url=settings.database_url)
        provider_router = ProviderRouter(settings, cache=llm_cache)

        from memory.episodic_memory import EpisodicMemoryAgent
        episodic_memory_agent = EpisodicMemoryAgent(provider_router, settings.database_url, settings.chroma_persist_dir)

        # Wire episodic agent into tiered memory now that both exist
        tiered_memory.episodic_agent = episodic_memory_agent

        context_assembler = ContextAssembler(
            retriever=retriever,
            sos_tool=SosTool(backend_client, w3w_tool, geocode_client),
            challan_tool=ChallanTool(backend_client),
            legal_search_tool=LegalSearchTool(retriever),
            first_aid_tool=FirstAidTool(settings),
            road_infra_tool=RoadInfrastructureTool(backend_client),
            road_issues_tool=RoadIssuesTool(backend_client),
            submit_report_tool=submit_report_tool,
            weather_tool=weather_tool,
            drug_info_tool=drug_info_tool,
            episodic_memory_agent=episodic_memory_agent,
            tiered_memory=tiered_memory,
        )

        chat_engine = ChatEngine(
            memory_store=memory_store,
            vectorstore=vectorstore,
            intent_detector=IntentDetector(embedding_model=settings.embedding_model),
            safety_checker=SafetyChecker(),
            context_assembler=context_assembler,
            provider_router=provider_router,
            redis_url=settings.redis_url,  # Phase 0.7: AI governance audit trail
            episodic_memory_agent=episodic_memory_agent,
        )

        app.state.memory_store = memory_store
        app.state.chat_engine = chat_engine
        app.state.speech_service = speech_service
        app.state.llm_cache = llm_cache

        # P0-01: Validate at least one LLM provider is configured (moved from config.py module-level)
        _active_keys = [
            k for k in [
                "GROQ_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                "OPENROUTER_API_KEY", "HF_TOKEN", "GITHUB_TOKEN",
                "MISTRAL_API_KEY", "SARVAM_API_KEY", "NVIDIA_NIM_API_KEY",
                "CEREBRAS_API_KEY", "TOGETHER_API_KEY",
            ]
            if os.getenv(k)
        ]
        if not _active_keys:
            logger.warning(
                "No LLM provider API keys configured. "
                "The TemplateProvider (deterministic fallback) will be used. "
                "Set at least one API key (e.g. GROQ_API_KEY, GEMINI_API_KEY)."
            )

        # Initialize background task queue and worker
        from core.queue import BackgroundWorker, TaskQueue, set_global_chat_engine
        set_global_chat_engine(chat_engine)
        if hasattr(memory_store, '_client') and memory_store._client is not None:
            queue = TaskQueue(memory_store._client)
            worker = BackgroundWorker(memory_store._client, concurrency=1)
            app.state.queue = queue
            app.state.worker = worker
            await worker.start()
            logger.info("Chatbot asynchronous task queue and worker started successfully")
        else:
            logger.warning("Chatbot task queue broker not available (Redis offline). Synchronous execution active.")
            app.state.queue = None
            app.state.worker = None

        # S15/C7: Preload speech model at startup so the first real request
        # doesn't incur a multi-second cold-start delay (audit finding).
        # _ensure_model_loaded is synchronous (HuggingFace model load), so run in executor.
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, speech_service._ensure_model_loaded)
            logger.info("IndicSeamless speech model preloaded successfully")
        except Exception as _exc:  # model may be unavailable in CI / free tier
            logger.warning("Speech model preload skipped: %s", _exc)

        try:
            yield
        finally:
            if hasattr(app.state, 'worker') and app.state.worker is not None:
                await app.state.worker.stop()
            await chat_engine.close()  # Phase 0.7: Close governance resources
            await weather_tool.aclose()
            await backend_client.aclose()
            await w3w_tool.aclose()
            await geocode_client.aclose()
            await drug_info_tool.aclose()
            await submit_report_tool.aclose()
            await memory_store.close()
            await llm_cache.close()
            await user_pref_store.close()

    docs_url = None if settings.environment == 'production' else '/docs'
    redoc_url = None if settings.environment == 'production' else '/redoc'
    openapi_url = None if settings.environment == 'production' else '/openapi.json'
    app = FastAPI(
        title=settings.service_name,
        version='1.0.0',
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        # P0-04: Restrict methods and headers (audit issue H2)
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "X-Admin-Key",
            "X-Request-ID",
            "X-Requested-With",
        ],
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Global exception handler — catches all unhandled exceptions
    @app.exception_handler(Exception)
    async def _global_exception_handler(request: Request, exc: Exception):
        import traceback
        logger.error(
            "Unhandled exception: %s | path=%s | tb=%s",
            exc, request.url.path, "".join(traceback.format_tb(exc.__traceback__)),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."},
        )

    # OBSERVABILITY#2: Query profiler middleware (logs slow responses)
    setup_query_profiler(app)

    # OBSERVABILITY#3: Correlation ID middleware (ContextVar-based tracing)
    setup_correlation_id(app)

    # P2-02: Prometheus metrics middleware
    @app.middleware("http")
    async def _prometheus_metrics_middleware(request: Request, call_next):
        from core.metrics import api_request_time, api_request_total

        if request.url.path == "/metrics":
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start

        api_request_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        api_request_time.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response

    # Host header validation middleware — blocks Host header injection (production only)
    @app.middleware("http")
    async def _host_validation_middleware(request: Request, call_next):
        if get_settings().environment != "production":
            return await call_next(request)
        import os as _os
        from urllib.parse import urlparse
        settings = get_settings()
        cors_hosts = {urlparse(u).hostname for u in settings.cors_origins_list if u} - {None}
        extra_allowed = {h.strip().lower() for h in _os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()}
        allowed = cors_hosts | extra_allowed
        host = request.headers.get("host", "").split(":")[0].strip().lower()
        if host and host not in allowed and not any(host.endswith("." + h) for h in {a for a in allowed if a.startswith("*.")}):
            logger.warning("Blocked request with invalid Host header: %s", host)
            return JSONResponse(status_code=403, content={"detail": "Invalid Host header"})
        return await call_next(request)

    # Body size limit middleware — prevents oversized request bodies
    _MAX_BODY_BYTES = 1 * 1024 * 1024  # 1 MB default
    _SPEECH_PATH = "/speech/translate"

    @app.middleware("http")
    async def _body_size_middleware(request: Request, call_next):
        max_size = 10 * 1024 * 1024 if request.url.path == _SPEECH_PATH else _MAX_BODY_BYTES
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > max_size:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body too large (max {max_size // 1024 // 1024} MB)."},
            )
        return await call_next(request)

    # P2-02: Request-ID correlation middleware
    @app.middleware("http")
    async def _security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(self), "
            "microphone=(self), "
            "camera=(), "
            "accelerometer=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "payment=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' https: data: blob:; "
            "connect-src 'self' https: wss: ws:; "
            "media-src 'self' blob:; "
            "worker-src 'self' blob:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        return response

    @app.middleware("http")
    async def _request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        auth_header = request.headers.get("Authorization", "")
        user_id = "anonymous"
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            try:
                import base64 as _b64
                import json as _json
                parts = token.split(".")
                if len(parts) >= 2:
                    padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                    decoded = _b64.urlsafe_b64decode(padded)
                    payload = _json.loads(decoded)
                    user_id = payload.get("sub") or payload.get("user_id") or "authenticated"
            except Exception:
                user_id = "authenticated"
        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.get('/health', tags=['System'])
    async def health() -> dict:
        """Root health check for Render/load-balancer liveness probes."""
        memory_store = getattr(app.state, 'memory_store', None)
        memory_ok = await memory_store.ping() if memory_store else True
        return {
            'status': 'ok',
            'service': 'safevixai-chatbot',
            'memory_available': memory_ok,
        }

    @app.get('/', tags=['System'])
    async def root() -> dict:
        return {
            'service': 'SafeVixAI / SafeVixAI — Chatbot Service',
            'version': '1.0.0',
            'status': 'online',
            'description': (
                'Agentic RAG-powered road safety assistant for India. '
                'Multi-provider LLM fallback chain (Groq, Gemini, HuggingFace). '
                'Covers emergency response, MV Act legal queries, first aid, road reporting and more.'
            ),
            'docs': docs_url,
            'health': '/health',
            'endpoints': {
                'chat':          'POST /api/v1/chat/',
                'chat_stream':   'POST /api/v1/chat/stream',
                'chat_history':  'GET  /api/v1/chat/history/{session_id} (admin)',
                'chat_health':   'GET  /api/v1/chat/health',
                'speech_status': 'GET  /speech/status',
                'index_health':   'GET  /admin/health',
                'rebuild_index':  'POST /admin/rebuild-index',
            },
            'rag_index': {
                'note': 'Hit /admin/health for live chunk count and memory backend info',
            },
            'built_for': 'IIT Madras Road Safety Hackathon 2026',
        }

    app.include_router(api_router)

    @app.get('/metrics', tags=['Observability'])
    async def metrics():
        from fastapi.responses import Response

        from core.metrics import metrics_content_type, metrics_response
        return Response(
            content=metrics_response(),
            media_type=metrics_content_type(),
        )

    return app


app = create_app()
