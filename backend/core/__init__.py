# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from core.alert import AlertService, get_alert_service
from core.config import Settings, get_settings
from core.database import AsyncSessionLocal, check_database, check_replica_database, engine, get_db
from core.distributed_lock import Redlock, distributed_lock
from core.exception_handlers import register_exception_handlers
from core.idempotency import IdempotencyMiddleware
from core.jwks import JWKSManager
from core.limiter import limiter
from core.logging import configure_logging
from core.redis_client import CacheHelper, create_cache
from core.security import (
    SECRET_KEY, COOKIE_SECURE, COOKIE_SAMESITE, COOKIE_HTTPONLY, COOKIE_PATH,
    ACCESS_TOKEN_EXPIRE_HOURS, REFRESH_TOKEN_EXPIRE_DAYS,
    APP_JWT_AUDIENCE, APP_JWT_ISSUER,
    create_access_token, create_refresh_token, create_secure_cookie_response,
    get_current_user, get_current_user_optional,
    revoke_token, is_token_revoked,
    require_role,
)
from core.cqrs import CQRSBus, Command, Query, init_cqrs_bus, get_cqrs_bus
from core.versioning import APIVersioningMiddleware
from core.response_wrapper import ApiResponseMiddleware
from core.i18n_middleware import setup_backend_i18n

__all__ = [
    "AlertService", "get_alert_service",
    "Settings", "get_settings",
    "AsyncSessionLocal", "check_database", "check_replica_database", "engine", "get_db",
    "Redlock", "distributed_lock",
    "register_exception_handlers",
    "IdempotencyMiddleware",
    "JWKSManager",
    "limiter",
    "configure_logging",
    "CacheHelper", "create_cache",
    "SECRET_KEY", "COOKIE_SECURE", "COOKIE_SAMESITE", "COOKIE_HTTPONLY", "COOKIE_PATH",
    "ACCESS_TOKEN_EXPIRE_HOURS", "REFRESH_TOKEN_EXPIRE_DAYS",
    "APP_JWT_AUDIENCE", "APP_JWT_ISSUER",
    "create_access_token", "create_refresh_token", "create_secure_cookie_response",
    "get_current_user", "get_current_user_optional",
    "revoke_token", "is_token_revoked",
    "require_role",
    "CQRSBus", "Command", "Query", "init_cqrs_bus", "get_cqrs_bus",
    "APIVersioningMiddleware",
    "ApiResponseMiddleware",
    "setup_backend_i18n",
]
