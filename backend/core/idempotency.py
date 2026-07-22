# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Idempotency middleware for SafeVixAI Backend.

Ensures that duplicate POST/PUT requests with the same Idempotency-Key
header return the cached response instead of executing the operation again.

Usage:
    Add `IdempotencyMiddleware` to FastAPI app middleware stack.
    Clients send `Idempotency-Key: <unique-uuid>` header with POST/PUT requests.
    
Phase 0.5: Prevents duplicate side effects from network retries.
"""
from __future__ import annotations

import json
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.redis_client import create_cache

logger = logging.getLogger(__name__)

_IDEMPOTENCY_TTL = 86400  # 24 hours
_IDEMPOTENCY_PREFIX = "idempotency:"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces idempotency for POST/PUT requests."""

    async def dispatch(self, request: Request, call_next):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        cache = create_cache()
        cache_key = f"{_IDEMPOTENCY_PREFIX}{idempotency_key}"

        try:
            # Check if we already have a cached response
            cached = await cache.get(cache_key)
            if cached:
                logger.info("Idempotency cache hit for key: %s", idempotency_key)
                from core.audit import AuditEvent, AuditLog
                AuditLog.log(
                    AuditEvent.ADMIN_ACTION,
                    user_id=request.client.host if request.client else "unknown",
                    ip_address=request.client.host if request.client else None,
                    details={"action": "idempotency_replay_intercepted", "idempotency_key": idempotency_key},
                )
                data = json.loads(cached)
                return JSONResponse(
                    content=data["body"],
                    status_code=data["status_code"],
                    headers={"X-Idempotency-Cached": "true"},
                )

            # Execute the request
            response = await call_next(request)

            # Cache successful responses (2xx, 3xx)
            if 200 <= response.status_code < 400:
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                try:
                    body_str = body.decode("utf-8")
                    await cache.setex(
                        cache_key,
                        _IDEMPOTENCY_TTL,
                        json.dumps({
                            "status_code": response.status_code,
                            "body": json.loads(body_str) if body_str else None,
                        }),
                    )
                except (json.JSONDecodeError, UnicodeDecodeError):
                    logger.warning("Failed to cache idempotency response: non-JSON body")

                return JSONResponse(
                    content=json.loads(body) if body else None,
                    status_code=response.status_code,
                    headers={"X-Idempotency-Cached": "false"},
                )

            return response

        except Exception:
            logger.exception("Idempotency middleware error")
            return await call_next(request)
        finally:
            await cache.close()
