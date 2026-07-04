# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import os
import secrets
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
import uuid
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import jwt

import re

import logging

logger = logging.getLogger(__name__)

# Regex matching any development/static/mock token patterns
REJECTED_TOKEN_RE = re.compile(
    r'(?:mock|fake|test|demo|dev|hackathon|sample|placeholder).*(?:token|jwt|key|secret)',
    re.IGNORECASE,
)

# Static mock tokens that must be explicitly rejected
REJECTED_STATIC_TOKENS = {
    "mock-jwt-token-for-hackathon",
}

# JWT secrets must come from environment in production. In development, an
# ephemeral key avoids shipping a static secret while keeping local auth usable.
_ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()
_env_secret = os.environ.get("JWT_SECRET_KEY")
if _env_secret:
    if _ENVIRONMENT == "production" and len(_env_secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 bytes when ENVIRONMENT=production")
    SECRET_KEY = _env_secret
elif _ENVIRONMENT == "production":
    raise RuntimeError("JWT_SECRET_KEY is required when ENVIRONMENT=production")
else:
    SECRET_KEY = secrets.token_urlsafe(64)
    logger.warning(
        "JWT_SECRET_KEY not set; generated an ephemeral key. "
        "Tokens will not survive server restarts."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ.get("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

# P1-01: Audience and Issuer validation for internal operator tokens
APP_JWT_AUDIENCE = os.environ.get("APP_JWT_AUDIENCE", "safevixai-internal")
APP_JWT_ISSUER = os.environ.get("APP_JWT_ISSUER", "safevixai-auth-service")

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
SUPABASE_JWT_AUDIENCE = os.environ.get("SUPABASE_JWT_AUDIENCE", "authenticated").strip()

# Token revocation set (LRU-limited in-memory fallback, persisted to Redis when available)
# OrderedDict used as LRU: max 10k entries prevents unbounded memory growth.
_REVOKED_LRU_MAX = 10_000
_revoked_token_jtis: OrderedDict[str, None] = OrderedDict()
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

def _get_revocation_cache_key(jti: str) -> str:
    return f"revoked_token:{jti}"

async def revoke_token(jti: str, cache=None) -> None:
    # Move to end (most recently used) via pop + reassign
    _revoked_token_jtis.pop(jti, None)
    _revoked_token_jtis[jti] = None
    # LRU eviction: remove oldest (first) entry when over capacity
    if len(_revoked_token_jtis) > _REVOKED_LRU_MAX:
        _revoked_token_jtis.popitem(last=False)
    if cache:
        await cache.set_json(_get_revocation_cache_key(jti), True, ttl_seconds=86400 * 30)

async def is_token_revoked(jti: str, cache=None) -> bool:
    if jti in _revoked_token_jtis:
        # Refresh LRU order on hit
        _revoked_token_jtis.move_to_end(jti)
        return True
    if cache:
        result = await cache.get_json(_get_revocation_cache_key(jti))
        if result:
            _revoked_token_jtis[jti] = None
            if len(_revoked_token_jtis) > _REVOKED_LRU_MAX:
                _revoked_token_jtis.popitem(last=False)
            return True
    return False

# Phase 0.2: Cookie security flags
COOKIE_SECURE = _ENVIRONMENT == "production"
COOKIE_SAMESITE = "lax"
COOKIE_HTTPONLY = True
COOKIE_PATH = "/"

security = HTTPBearer(auto_error=False)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    role: str = "user",
) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
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
    now = datetime.now(timezone.utc)
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
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
        expires=expire,
        max_age=int((expire - datetime.now(timezone.utc)).total_seconds()),
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
        
    from core.rbac import Role
    try:
        Role(raw_role)
    except ValueError:
        logger.warning(f"Invalid role claim '{raw_role}' in token payload, rejecting token")
        raise HTTPException(status_code=401, detail="Invalid role claim in token")
        
    return {
        **payload,
        "sub": str(user_id),
        "role": raw_role,
        "org_id": str(org_id) if org_id else None,
        "auth_provider": provider,
    }


def require_role(required_role: str | Any):
    """FastAPI dependency that enforces role-based access.
    
    Accepts a Role enum or role string (e.g. 'admin', 'operator').
    """
    from core.rbac import Role, require_role as rbac_require_role
    if isinstance(required_role, str):
        try:
            role_enum = Role(required_role)
        except ValueError:
            raise ValueError(f"Invalid required role: {required_role}")
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
        raise jwt.InvalidTokenError("SUPABASE_JWT_SECRET is not configured")
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
            try:
                from core.jwks import JWKSManager
                # This will be called from request context where app.state is available
                # For now, fall back to static secret
                logger.debug("JWT verification failed; JWKS not available in this context")
            except ImportError:
                logger.debug("Suppressed exception", exc_info=True)
            logger.info("Bearer token rejected by app, Supabase, and JWKS validators")
            raise _unauthorized() from app_error


# Simple in-memory rate limiter fallback for internal auth bypass attempts
_internal_auth_attempts: dict[str, list[float]] = {}

async def _check_internal_auth_rate_limit(client_ip: str | None, cache=None) -> None:
    """Allow max 5 internal auth attempts per IP per 60 seconds (Redis-backed with in-memory fallback)."""
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
    attempts = _internal_auth_attempts.setdefault(key, [])
    # Prune old entries
    attempts[:] = [t for t in attempts if now - t < window]
    if len(attempts) >= 5:
        logger.warning("Internal auth rate limit exceeded for IP: %s (InMemory)", client_ip)
        raise HTTPException(status_code=429, detail="Too many authentication attempts. Try again later.")
    attempts.append(now)


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
        if await is_token_revoked(jti, cache):
            raise HTTPException(status_code=401, detail="Token has been revoked")
    return user
