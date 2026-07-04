# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
import logging.config
import time
import uuid
from contextlib import asynccontextmanager

import jwt
import httpx
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.v1 import api_router
from core.alert import get_alert_service
from core.config import get_settings
from core.database import check_database, check_replica_database
from core.limiter import limiter
from core.idempotency import IdempotencyMiddleware
from core.versioning import APIVersioningMiddleware
from core.jwks import JWKSManager
from core.response_wrapper import ApiResponseMiddleware
from core.i18n_middleware import setup_backend_i18n
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.redis_client import create_cache
from models.schemas import ApiErrorResponse, DependencyHealth, HealthResponse
from services.authority_router import AuthorityRouter
from services.challan_service import ChallanService
from services.emergency_locator import EmergencyLocatorService
from services.geocoding_service import GeocodingService
from services.llm_service import LLMService
from services.overpass_service import OverpassService
from services.roadwatch_service import RoadWatchService
from services.routing_service import RoutingService

# alert_service imported at top level


# P2-01: Structured JSON logging (audit H35)
# In production, emit newline-delimited JSON for Render/Cloud log aggregators.
# In development, use a human-readable format with colour-coded levels.
class _JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line for machine-parseable log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Include any extra fields attached via LogRecord (e.g. request_id)
        for key in ("request_id", "method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def _configure_logging(environment: str) -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Remove any existing handlers set by uvicorn/gunicorn
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    if environment == "production":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
    root.addHandler(handler)
    # Keep uvicorn access logs quiet — our middleware handles request logging
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("safevixai.backend")

_start_time = time.time()


def _get_uptime() -> float:
    return time.time() - _start_time


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_logging(settings.environment)

    # OBSERVABILITY#1: Sentry error tracking (free tier: 5K errors/month)
    if settings.sentry_dsn and sentry_sdk is not None:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.05,
            profiles_sample_rate=0.05,
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        import asyncio
        import signal
        from core.database import AsyncSessionLocal, engine
        from services.sla_monitor import SLAMonitor

        _shutdown_requested = False
        def _handle_signal():
            nonlocal _shutdown_requested
            _shutdown_requested = True
            logger.info("Received shutdown signal — draining connections")
        try:
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, _handle_signal)
        except (NotImplementedError, ValueError, RuntimeError):
            logger.warning("Signal handlers not supported on this platform")

        cache = create_cache(settings.redis_url)
        jwks_manager = JWKSManager(jwks_url=settings.jwks_url if hasattr(settings, 'jwks_url') else None)
        await jwks_manager.start()
        
        overpass_service = OverpassService(settings)
        geocoding_service = GeocodingService(settings, cache)
        authority_router = AuthorityRouter(settings, overpass_service, cache)
        emergency_service = EmergencyLocatorService(settings=settings, cache=cache, overpass_service=overpass_service)
        routing_service = RoutingService(settings=settings, cache=cache)
        challan_service = ChallanService(settings=settings)
        llm_service = LLMService(settings=settings)
        roadwatch_service = RoadWatchService(
            settings=settings,
            cache=cache,
            geocoding_service=geocoding_service,
            authority_router=authority_router,
        )

        app.state.cache = cache
        app.state.jwks_manager = jwks_manager
        app.state.overpass_service = overpass_service
        app.state.geocoding_service = geocoding_service
        app.state.authority_router = authority_router
        app.state.emergency_service = emergency_service
        app.state.routing_service = routing_service
        app.state.challan_service = challan_service
        app.state.llm_service = llm_service
        app.state.roadwatch_service = roadwatch_service

        # Initialize Event Bus and Redis adapter
        from services.event_bus import get_event_bus, RedisPubSubAdapter
        event_bus = get_event_bus()
        try:
            adapter = RedisPubSubAdapter(cache)
            event_bus.set_redis_adapter(adapter)
        except Exception as e:
            logger.warning("Could not attach Redis adapter to EventBus: %s", e)

        # Global audit event logger
        async def global_event_logger(event):
            logger.info("DOMAIN EVENT PROCESSED: %s [%s] payload=%s", event.event_type, event.event_id[:8], event.payload)
        
        event_bus.subscribe("*", global_event_logger)
        app.state.event_bus = event_bus

        # Initialize and start SLAMonitor background task
        sla_monitor = SLAMonitor(AsyncSessionLocal)
        app.state.sla_monitor = sla_monitor
        sla_interval = 60 if settings.environment == "development" else 900
        app.state.sla_task = asyncio.create_task(sla_monitor.start_loop(interval_seconds=sla_interval))

        # Initialize and start ETL Scheduler for civic intelligence pipelines
        from services.civic_intel.etl_scheduler import ETLScheduler
        etl_scheduler = ETLScheduler(
            session_factory=AsyncSessionLocal,
            overpass_service=overpass_service,
        )
        app.state.etl_scheduler = etl_scheduler
        await etl_scheduler.start()

        # Initialize and start DataRetentionScheduler for privacy compliance
        from services.data_retention import DataRetentionScheduler
        data_retention = DataRetentionScheduler(AsyncSessionLocal)
        app.state.data_retention = data_retention
        retention_interval = 3600 if settings.environment == "development" else 86400  # 1 hour dev, 24 hours prod
        await data_retention.start(interval_seconds=retention_interval)

        # Initialize and start background task queue and worker daemon
        from core.queue import TaskQueue, BackgroundWorker
        if cache._client is not None:
            queue = TaskQueue(cache._client)
            worker = BackgroundWorker(cache._client, concurrency=2)
            app.state.queue = queue
            app.state.worker = worker
            await worker.start()
            logger.info("Asynchronous background queue and worker started successfully")
        else:
            logger.warning("Queue broker not available (Redis is offline). Tasks will fall back to synchronous execution.")
            app.state.queue = None
            app.state.worker = None

        try:
            yield
        finally:
            if hasattr(app.state, 'worker') and app.state.worker is not None:
                await app.state.worker.stop()
            if hasattr(app.state, 'sla_monitor'):
                app.state.sla_monitor.stop()
            if hasattr(app.state, 'sla_task'):
                app.state.sla_task.cancel()
            if hasattr(app.state, 'data_retention'):
                app.state.data_retention.stop()
            if hasattr(app.state, 'etl_scheduler'):
                await app.state.etl_scheduler.stop()
            
            await jwks_manager.stop()
            from services.safe_spaces import close_safe_spaces_client
            await close_safe_spaces_client()
            await llm_service.aclose()
            await routing_service.aclose()
            await geocoding_service.aclose()
            await overpass_service.aclose()
            from services.osm_contributor import get_osm_contributor
            await get_osm_contributor().close()
            await cache.close()
            try:
                await engine.dispose()
                logger.info("Database connection pool disposed")
            except Exception:
                logger.warning("Database pool disposal failed (expected if already closed)")

    docs_url = None if settings.environment == 'production' else '/docs'
    redoc_url = None if settings.environment == 'production' else '/redoc'
    openapi_url = None if settings.environment == 'production' else '/openapi.json'
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    
    # Mount backend multi-language exception and validation localization
    setup_backend_i18n(app)
    
    # OBSERVABILITY#2: OpenTelemetry distributed tracing
    try:
        from core.tracing import setup_tracing
        setup_tracing(app)
    except ImportError as exc:
        # opentelemetry not installed (dev-only dependency)
        logger.debug("OpenTelemetry not installed, tracing disabled: %s", exc)
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Phase 0.5: Idempotency middleware for POST/PUT requests
    app.add_middleware(IdempotencyMiddleware)

    # Phase 0.4: API versioning middleware
    app.add_middleware(APIVersioningMiddleware)

    # P2-01: Request-ID correlation middleware
    # Stamps every request with a unique ID so all log lines for a single
    # request can be correlated in Render / any log aggregator.
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
        is_prod = get_settings().environment == "production"
        script_src = "'self' 'unsafe-inline'" + ("" if is_prod else " 'unsafe-eval'")
        response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; "
            f"script-src {script_src}; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' https: data: blob:; "
            "connect-src 'self' https: wss: ws:; "
            "media-src 'self' blob:; "
        )
        # Performance: Cache-Control headers for suitable GET endpoints
        if request.method == "GET" and response.status_code < 400:
            path = request.url.path
            if path == "/api/v1/emergency/numbers" or path == "/health":
                response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
            elif path.startswith("/api/v1/emergency/nearby"):
                response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=30"
            elif path.startswith("/api/v1/emergency/sos"):
                response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=60"
            elif path.startswith("/api/v1/challan/calculate"):
                response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
            elif path.startswith("/api/v1/roadwatch/feed"):
                response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=60"
            elif path.startswith("/api/v1/user/"):
                response.headers["Cache-Control"] = "private, max-age=60, stale-while-revalidate=30"
        return response

    @app.middleware("http")
    async def _request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        # Extract user_id from JWT payload WITHOUT signature verification.
        # This is safe because we only read the 'sub' claim for logging correlation.
        # We do NOT trust any claims from an unverified token.
        user_id = "anonymous"
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            try:
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False},
                )
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

    # OBSERVABILITY#4: Prometheus API metrics middleware
    @app.middleware("http")
    async def _prometheus_metrics_middleware(request: Request, call_next):
        from core.metrics import api_request_total, api_request_time
        
        # Skip metrics endpoint itself to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
        
        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start
        
        # Record metrics
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

    @app.middleware("http")
    async def _csrf_middleware(request: Request, call_next):
        csrf_cookie = request.cookies.get("csrf_token")

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # CSRF only matters for cookie-based auth. Bearer token requests are immune.
            has_bearer = request.headers.get("Authorization", "").startswith("Bearer ")
            skip_paths = (
                request.url.path.startswith("/api/v1/auth/login")
                or request.url.path.startswith("/mcp")
            )
            if settings.environment != "test" and not has_bearer and not skip_paths:
                csrf_header = request.headers.get("X-CSRF-Token")
                if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF token missing or invalid"}
                    )

        response = await call_next(request)

        if not csrf_cookie:
            import secrets
            new_token = secrets.token_urlsafe(32)
            is_prod = settings.environment == "production"
            response.set_cookie(
                key="csrf_token",
                value=new_token,
                httponly=False,
                secure=is_prod,
                samesite="lax",
                path="/"
            )
        return response

    # Phase 0.6: Tenant isolation middleware
    # Automatically filters database queries by org_id for multi-tenant data isolation

    @app.middleware("http")
    async def _tenant_isolation_middleware(request: Request, call_next):
        from fastapi.responses import JSONResponse
        from fastapi import HTTPException
        from core.tenant import get_tenant_id
        
        try:
            # Get tenant ID from authenticated user
            tenant_id = await get_tenant_id(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        
        # Store tenant ID in request state for downstream use
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        return response

    # Phase 0.7: API deprecation middleware — adds Sunset/Deprecation headers
    from api.deprecation import get_deprecation_headers

    @app.middleware("http")
    async def _deprecation_middleware(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        headers = get_deprecation_headers(path)
        for key, value in headers.items():
            response.headers[key] = value
        return response

    # Phase 3.3: Allowed hosts middleware — blocks Host header injection
    from middleware.allowed_hosts import setup_allowed_hosts
    setup_allowed_hosts(app, settings)

    # Phase 3.2: Query profiler middleware — logs slow queries
    from middleware.query_profiler import setup_query_profiler
    setup_query_profiler(app)

    # Phase 3.2: GeoJSON compression middleware
    from middleware.compression import setup_compression
    setup_compression(app)

    # SECURITY#03: CORS origin validator — rejects requests from origins not in allowlist
    cors_origins = settings.cors_origins
    if cors_origins == ['*']:
        logger.warning("CORS configured with wildcard origin — all origins accepted")
    else:
        cors_set = set(cors_origins)
        @app.middleware("http")
        async def _cors_origin_check(request: Request, call_next):
            origin = request.headers.get("origin")
            if origin and origin not in cors_set:
                logger.warning("Blocked request from unauthorized origin: %s", origin)
                return JSONResponse(status_code=403, content={"detail": "Origin not allowed"})
            return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        # P0-04: Restrict methods and headers (audit issue H2)
        # Wildcard allow_methods + allow_headers with allow_credentials=True is a CORS misconfiguration
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "X-Admin-Key",
            "X-CSRF-Token",
            "X-Request-ID",
            "X-Requested-With",
        ],
    )
    # Phase 7: ApiResponse<T> envelope wrapping — outermost middleware
    app.add_middleware(ApiResponseMiddleware)

    app.mount('/uploads', StaticFiles(directory=settings.upload_dir), name='uploads')

    # ── Global unhandled exception handler with alerting ─────────────────
    from core.exception_handlers import register_exception_handlers
    register_exception_handlers(app)

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
        # SECURITY#18: Sanitize exception message — don't leak SQL, PII, or secrets in alerts
        exc_msg = str(exc)
        if len(exc_msg) > 500:
            exc_msg = exc_msg[:500] + "...[truncated]"
        # Remove potential SQL queries from error messages
        exc_msg = exc_msg.replace("SELECT", "[REDACTED]").replace("INSERT", "[REDACTED]").replace("DELETE", "[REDACTED]")
        # Redact PII patterns: emails, phone numbers, IP addresses
        exc_msg = re.sub(r'[\w\.-]+@[\w\.-]+\.\w{2,}', '[EMAIL REDACTED]', exc_msg)
        exc_msg = re.sub(r'\b\d{10}\b', '[PHONE REDACTED]', exc_msg)
        exc_msg = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP REDACTED]', exc_msg)
        get_alert_service().alert_external_api_failed(
            service_name="Backend Unhandled Error",
            endpoint=f"{request.method} {request.url.path}",
            status_code=500,
            error_msg=exc_msg,
        )
        return JSONResponse(
            status_code=500,
            content=ApiErrorResponse(
                error={"code": "INTERNAL_ERROR", "message": "Internal server error. The team has been notified."},
                timestamp=datetime.now(timezone.utc).isoformat(),
            ).model_dump(),
        )

    @app.get('/', tags=['System'])
    async def root() -> dict:
        return {
            'service': 'SafeVixAI / SafeVixAI — Backend API',
            'version': settings.version,
            'status': 'online',
            'description': (
                'AI-powered road safety platform for India. '
                'Real-time emergency locator, road issue reporting, '
                'challan calculator, and smart routing.'
            ),
            'docs': docs_url,
            'health': '/health',
            'endpoints': {
                'emergency_nearby':    'GET  /api/v1/emergency/nearby?lat=&lon=',
                'emergency_sos':       'POST /api/v1/emergency/sos?lat=&lon=',
                'emergency_numbers':   'GET  /api/v1/emergency/numbers',
                'challan_calculate':   'POST /api/v1/challan/calculate',
                'road_issues':         'GET  /api/v1/roads/issues?lat=&lon=',
                'road_report':         'POST /api/v1/roads/report',
                'road_infrastructure': 'GET  /api/v1/roads/infrastructure?lat=&lon=',
                'routing_preview':     'GET  /api/v1/routing/preview?origin_lat=&origin_lon=&destination_lat=&destination_lon=',
                'geocode_search':      'GET  /api/v1/geocode/search?q=',
                'chat':                'POST /api/v1/chat/',
                **({
                    'mcp_server_sse': 'GET  /mcp/sse',
                    'mcp_server_msg': 'POST /mcp/messages',
                } if settings.mcp_enabled else {}),
            },
            'built_for': 'IIT Madras Road Safety Hackathon 2026',
        }

    @app.get('/health', response_model=HealthResponse, tags=['System'])
    async def health() -> HealthResponse:
        import time as _time_module
        dependencies = []
        db_start = _time_module.time()
        database_available = await check_database()
        db_latency = (_time_module.time() - db_start) * 1000
        dependencies.append(DependencyHealth(
            name="database", available=database_available, latency_ms=round(db_latency, 1)
        ))

        replica_start = _time_module.time()
        replica_available = await check_replica_database()
        replica_latency = (_time_module.time() - replica_start) * 1000
        dependencies.append(DependencyHealth(
            name="database_replica", available=replica_available, latency_ms=round(replica_latency, 1),
            error=None if replica_available else "Read replica unavailable or not configured"
        ))

        cache_available = False
        cache_backend = 'disabled'
        cache_start = _time_module.time()
        cache = getattr(app.state, 'cache', None)
        if cache is not None:
            cache_available = await cache.ping()
            cache_backend = getattr(cache, 'backend_name', 'unknown')
        cache_latency = (_time_module.time() - cache_start) * 1000
        dependencies.append(DependencyHealth(
            name="cache", available=cache_available, latency_ms=round(cache_latency, 1),
            error=None if cache_available else "Cache ping failed"
        ))

        chatbot_available = settings.chatbot_ready
        chatbot_latency = 0.0
        if settings.environment != 'test' and settings.chatbot_service_url:
            chatbot_start = _time_module.time()
            try:
                cb_health_url = f"{settings.chatbot_service_url.replace('/api/v1', '')}/health"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    cb_resp = await client.get(cb_health_url)
                    chatbot_available = cb_resp.status_code == 200
            except Exception:
                chatbot_available = False
            chatbot_latency = (_time_module.time() - chatbot_start) * 1000
        dependencies.append(DependencyHealth(
            name="chatbot", available=chatbot_available, latency_ms=round(chatbot_latency, 1),
            error=None if chatbot_available else "Chatbot service unreachable"
        ))

        circuit_breakers = {}
        try:
            from core.circuit_breaker import CircuitBreakerRegistry
            cb_stats = CircuitBreakerRegistry.all_stats()
            circuit_breakers = {name: stats["state"] for name, stats in cb_stats.items()}
        except ImportError:
            logger.debug("Suppressed exception", exc_info=True)

        overall_status = 'ok'
        if not database_available:
            overall_status = 'degraded'

        from core.database import engine as db_engine
        pool = db_engine.pool
        pool_stats = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "overflow": pool.overflow(),
        }
        from core.metrics import db_connection_pool_size
        db_connection_pool_size.set(pool.size())

        resp = HealthResponse(
            status=overall_status,
            database_available=database_available,
            chatbot_ready=chatbot_available,
            chatbot_mode=settings.chatbot_mode,
            cache_available=cache_available,
            cache_backend=cache_backend,
            environment='production',  # SECURITY#21: Don't leak actual environment name
            version=settings.version,
            dependencies=dependencies,
            circuit_breakers=circuit_breakers if circuit_breakers else None,
            pool_stats=pool_stats,
            uptime_seconds=round(_get_uptime(), 2),
        )
        if not database_available:
            get_alert_service().alert_supabase_failed(
                operation="Health check — database unreachable",
                error_msg="PostgreSQL connection failed during /health endpoint",
            )
            return JSONResponse(status_code=503, content=resp.model_dump())
        return resp

    # OBSERVABILITY#3: Prometheus metrics endpoint
    @app.get('/metrics', tags=['Observability'])
    async def metrics():
        from fastapi.responses import Response
        from core.metrics import metrics_response, metrics_content_type
        return Response(
            content=metrics_response(),
            media_type=metrics_content_type(),
        )

    # SECURITY#19: CSP violation report collector
    # Browsers POST CSP violation reports here when report-uri is specified.
    @app.post('/api/v1/csp-report', tags=['Security'])
    async def csp_report(request: Request):
        body = await request.body()
        logger.warning('CSP violation: %s', body[:2000].decode('utf-8', errors='replace'))
        return JSONResponse(status_code=204)

    app.include_router(api_router)
    
    if settings.mcp_enabled:
        from api.v1.mcp_server import router as mcp_info_router
        from api.v1.mcp_server import sse_app as mcp_app

        app.include_router(mcp_info_router)
        app.mount('/mcp', mcp_app)
    
    return app


# SECURITY#17: Configure uvicorn ws-max-size via environment variable
# Set WEBSOCKET_MAX_SIZE=1048576 (1MB) in production to prevent memory exhaustion
app = create_app()
