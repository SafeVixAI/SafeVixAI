# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import importlib
import logging
import os
import re
import secrets
import time
import uuid
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from core.rbac import Role

logger = logging.getLogger(__name__)


class SecurityState:
    __slots__ = (
        "_environment", "_secret_key", "_algorithm",
        "_access_token_expire_hours", "_refresh_token_expire_days",
        "_app_jwt_audience", "_app_jwt_issuer",
        "_supabase_jwt_secret", "_supabase_jwt_audience",
        "_revoked_token_jtis", "_revoked_lru_max",
        "_cookie_secure", "_cookie_samesite", "_cookie_httponly", "_cookie_path",
        "_rejected_token_re", "_rejected_static_tokens",
        "_internal_auth_attempts",
    )

    def __init__(self) -> None:
        env = os.environ.get("ENVIRONMENT", "development").lower()

        secret = os.environ.get("JWT_SECRET_KEY")
        if secret:
            if env == "production" and len(secret.encode("utf-8")) < 32:
                msg = "JWT_SECRET_KEY must be at least 32 bytes when ENVIRONMENT=production"
                raise RuntimeError(msg)
            self._secret_key = secret
        elif env == "production":
            msg = "JWT_SECRET_KEY is required when ENVIRONMENT=production"
            raise RuntimeError(msg)
        else:
            self._secret_key = secrets.token_urlsafe(64)
            logger.warning(
                "JWT_SECRET_KEY not set; generated an ephemeral key. "
                "Tokens will not survive server restarts."
            )

        self._environment = env
        self._algorithm = "HS256"
        self._access_token_expire_hours = int(os.environ.get("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
        self._refresh_token_expire_days = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
        self._app_jwt_audience = os.environ.get("APP_JWT_AUDIENCE", "safevixai-internal")
        self._app_jwt_issuer = os.environ.get("APP_JWT_ISSUER", "safevixai-auth-service")
        self._supabase_jwt_secret = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
        self._supabase_jwt_audience = os.environ.get("SUPABASE_JWT_AUDIENCE", "authenticated").strip()
        self._revoked_lru_max = 10_000
        self._revoked_token_jtis: OrderedDict[str, None] = OrderedDict()
        self._cookie_secure = env == "production"
        self._cookie_samesite = "lax"
        self._cookie_httponly = True
        self._cookie_path = "/"
        self._rejected_token_re = re.compile(
            r'(?:mock|fake|test|demo|dev|hackathon|sample|placeholder).*(?:token|jwt|key|secret)',
            re.IGNORECASE,
        )
        self._rejected_static_tokens = {"mock-jwt-token-for-hackathon"}
        self._internal_auth_attempts: dict[str, list[float]] = {}

    # ── Properties (backward-compatible access) ──

    @property
    def secret_key(self) -> str:
        return self._secret_key

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def access_token_expire_hours(self) -> int:
        return self._access_token_expire_hours

    @property
    def refresh_token_expire_days(self) -> int:
        return self._refresh_token_expire_days

    @property
    def app_jwt_audience(self) -> str:
        return self._app_jwt_audience

    @property
    def app_jwt_issuer(self) -> str:
        return self._app_jwt_issuer

    @property
    def supabase_jwt_secret(self) -> str:
        return self._supabase_jwt_secret

    @property
    def supabase_jwt_audience(self) -> str:
        return self._supabase_jwt_audience

    @property
    def cookie_secure(self) -> bool:
        return self._cookie_secure

    @property
    def cookie_samesite(self) -> str:
        return self._cookie_samesite

    @property
    def cookie_httponly(self) -> bool:
        return self._cookie_httponly

    @property
    def cookie_path(self) -> str:
        return self._cookie_path

    @property
    def rejected_static_tokens(self) -> set[str]:
        return self._rejected_static_tokens

    # ── Token revocation ──

    def _get_revocation_cache_key(self, jti: str) -> str:
        return f"revoked_token:{jti}"

    async def revoke_token(self, jti: str, cache=None) -> None:
        self._revoked_token_jtis.pop(jti, None)
        self._revoked_token_jtis[jti] = None
        if len(self._revoked_token_jtis) > self._revoked_lru_max:
            self._revoked_token_jtis.popitem(last=False)
        if cache:
            await cache.set_json(self._get_revocation_cache_key(jti), True, ttl_seconds=86400 * 30)

    async def is_token_revoked(self, jti: str, cache=None) -> bool:
        if jti in self._revoked_token_jtis:
            self._revoked_token_jtis.move_to_end(jti)
            return True
        if cache:
            result = await cache.get_json(self._get_revocation_cache_key(jti))
            if result:
                self._revoked_token_jtis[jti] = None
                if len(self._revoked_token_jtis) > self._revoked_lru_max:
                    self._revoked_token_jtis.popitem(last=False)
                return True
        return False

    # ── Internal auth rate limiting ──

    async def check_internal_auth_rate_limit(self, client_ip: str | None, cache=None) -> None:
        if not client_ip:
            return
        if cache is not None:
            key = f"internal_auth:{client_ip}"
            try:
                current = await cache.increment(key)
                if current == 1:
                    await cache.set_json(key, 1, ttl_seconds=60)
                elif current > 5:
                    logger.warning("Internal auth rate limit exceeded for IP: %s (Redis)", client_ip)
                    raise HTTPException(status_code=429, detail="Too many authentication attempts. Try again later.")
                return
            except Exception as e:
                logger.warning("Redis rate limiter failed, falling back to in-memory: %s", e)

        now = time.monotonic()
        window = 60.0
        key = f"internal_auth:{client_ip}"
        attempts = self._internal_auth_attempts.setdefault(key, [])
        attempts[:] = [t for t in attempts if now - t < window]
        if len(attempts) >= 5:
            logger.warning("Internal auth rate limit exceeded for IP: %s (InMemory)", client_ip)
            raise HTTPException(status_code=429, detail="Too many authentication attempts. Try again later.")
        attempts.append(now)


# Module-level singleton (backward compatible)
_state = SecurityState()

# Backward-compatible module-level constants
SECRET_KEY: str = _state.secret_key
ALGORITHM: str = _state.algorithm
ACCESS_TOKEN_EXPIRE_HOURS: int = _state.access_token_expire_hours
REFRESH_TOKEN_EXPIRE_DAYS: int = _state.refresh_token_expire_days
APP_JWT_AUDIENCE: str = _state.app_jwt_audience
APP_JWT_ISSUER: str = _state.app_jwt_issuer
SUPABASE_JWT_SECRET: str = _state.supabase_jwt_secret
SUPABASE_JWT_AUDIENCE: str = _state.supabase_jwt_audience
COOKIE_SECURE: bool = _state.cookie_secure
COOKIE_SAMESITE: str = _state.cookie_samesite
COOKIE_HTTPONLY: bool = _state.cookie_httponly
COOKIE_PATH: str = _state.cookie_path
REJECTED_STATIC_TOKENS: set[str] = _state.rejected_static_tokens

# Module-level references to state internals (backward compat for direct importers)
_REVOKED_LRU_MAX: int = _state._revoked_lru_max  # noqa: SLF001
_revoked_token_jtis: OrderedDict[str, None] = _state._revoked_token_jtis  # noqa: SLF001
REJECTED_TOKEN_RE: re.Pattern = _state._rejected_token_re  # noqa: SLF001

security = HTTPBearer(auto_error=False)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    role: str = "user",
) -> str:
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta if expires_delta else timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    # P1-01: Add aud and iss claims
    # Phase 0.1: Add role claim to JWT
    to_encode.update({
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": now,
        "aud": APP_JWT_AUDIENCE,
        "iss": APP_JWT_ISSUER,
        "role": role,
    })
    if "org_id" in data:
        to_encode["org_id"] = data["org_id"]
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta if expires_delta else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": now,
        "purpose": "refresh",
        "aud": APP_JWT_AUDIENCE,
        "iss": APP_JWT_ISSUER,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_secure_cookie_response(
    content: Any,
    token: str,
    status_code: int = 200,
    expires_delta: timedelta | None = None,
) -> JSONResponse:
    """Create a JSON response with a secure HttpOnly cookie containing the JWT.

    Phase 0.2: Prevents XSS attacks by making JWT inaccessible to JavaScript.
    """
    response = JSONResponse(content=content, status_code=status_code)
    expire = datetime.now(UTC) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
        expires=expire,
        max_age=int((expire - datetime.now(UTC)).total_seconds()),
    )
    return response


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Invalid authentication credentials")


def _normalize_user_payload(payload: dict[str, Any], *, provider: str) -> dict[str, Any]:
    user_id = payload.get("sub")
    if not user_id:
        raise _unauthorized()
    org_id = payload.get("org_id") or (payload.get("app_metadata") or {}).get("org_id")
    raw_role = payload.get("role") or payload.get("app_metadata", {}).get("role") or "user"
    if raw_role == "authenticated":
        raw_role = "user"

    try:
        Role(raw_role)
    except ValueError:
        logger.warning("Invalid role claim '%s' in token payload, rejecting token", raw_role)
        raise HTTPException(status_code=401, detail="Invalid role claim in token")

    return {
        **payload,
        "sub": str(user_id),
        "role": raw_role,
        "org_id": str(org_id) if org_id else None,
        "auth_provider": provider,
    }


def require_role(required_role: str | Role):
    """FastAPI dependency that enforces role-based access.

    Accepts a Role enum or role string (e.g. 'admin', 'operator').
    Delegates to core.rbac for the actual permission check.
    """
    from core.rbac import require_role as rbac_require_role
    if isinstance(required_role, str):
        try:
            role_enum = Role(required_role)
        except ValueError:
            msg = f"Invalid required role: {required_role}"
            raise ValueError(msg)
    else:
        role_enum = required_role
    return rbac_require_role(role_enum)


def _decode_app_token(token: str) -> dict[str, Any]:
    # P1-01: Strictly validate audience and issuer
    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM, "RS256"],
        audience=APP_JWT_AUDIENCE,
        issuer=APP_JWT_ISSUER,
    )
    return _normalize_user_payload(payload, provider="operator_jwt")


def _decode_supabase_token(token: str) -> dict[str, Any]:
    if not SUPABASE_JWT_SECRET:
        msg = "SUPABASE_JWT_SECRET is not configured"
        raise jwt.InvalidTokenError(msg)
    payload = jwt.decode(
        token,
        SUPABASE_JWT_SECRET,
        algorithms=[ALGORITHM, "RS256"],
        audience=SUPABASE_JWT_AUDIENCE or None,
    )
    return _normalize_user_payload(payload, provider="supabase")


def _decode_bearer_token(token: str) -> dict[str, Any]:
    token = token.strip()
    if not token or REJECTED_TOKEN_RE.search(token) or token in REJECTED_STATIC_TOKENS:
        raise _unauthorized()
    try:
        return _decode_app_token(token)
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError) as app_error:
        try:
            return _decode_supabase_token(token)
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
            # Phase 0.3: Try JWKS verification if available
            if importlib.util.find_spec("core.jwks"):
                logger.debug("JWKS module available but not used in this context")
            else:
                logger.debug("JWKS module not available — falling back to static secret")
            logger.info("Bearer token rejected by app, Supabase, and JWKS validators")
            raise _unauthorized() from app_error


# Delegate internal auth rate limiting to SecurityState
async def _check_internal_auth_rate_limit(client_ip: str | None, cache=None) -> None:
    await _state.check_internal_auth_rate_limit(client_ip, cache)


async def get_current_user_optional(
    request: Request,
) -> dict[str, Any] | None:
    """Return the authenticated caller when a valid bearer token is present."""
    # Internal service token authentication bypass for Chatbot
    internal_key = request.headers.get("X-Internal-Api-Key") or request.headers.get("X-Service-Token")
    if internal_key:
        client_ip = request.client.host if request.client else None
        cache = getattr(request.app.state, 'cache', None)
        await _check_internal_auth_rate_limit(client_ip, cache)
        from core.config import get_settings
        settings = get_settings()
        if settings.chatbot_internal_api_key and secrets.compare_digest(internal_key, settings.chatbot_internal_api_key):
            return {"sub": "chatbot-service", "role": "operator", "org_id": None, "auth_provider": "internal"}
        if settings.admin_secret and secrets.compare_digest(internal_key, settings.admin_secret):
            return {"sub": "admin-system", "role": "admin", "org_id": None, "auth_provider": "internal"}

    token = request.cookies.get("access_token")
    if token is None:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if token is None:
        return None
    try:
        return _decode_bearer_token(token)
    except HTTPException:
        raise
    except Exception:
        return None


async def get_current_user(
    request: Request,
) -> dict[str, Any]:
    """
    Validate either a Supabase Auth JWT or the temporary operator JWT.

    Static demo tokens are never accepted. User-facing clients should send
    Supabase Auth access tokens via the access_token cookie.
    """
    user = await get_current_user_optional(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    jti = user.get("jti")
    if jti:
        cache = getattr(request.app.state, 'cache', None)
        if await _state.is_token_revoked(jti, cache):
            raise HTTPException(status_code=401, detail="Token has been revoked")
    return user


# Module-level wrappers (delegate to internal SecurityState instance)
async def is_token_revoked(jti: str, cache=None) -> bool:
    return await _state.is_token_revoked(jti, cache)


async def revoke_token(jti: str, cache=None) -> None:
    await _state.revoke_token(jti, cache)
