# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings

logger = logging.getLogger("safevixai.security_headers")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
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

        if request.method == "GET" and response.status_code < 400:
            path = request.url.path

            # ── Immutable / long-lived public data ──
            if path in ("/health",):
                response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=30"
            elif path.startswith("/api/v1/civic/municipalities") and path != "/api/v1/civic/municipalities/nearby":
                response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=600"
            elif path.startswith("/api/v1/public/"):
                response.headers["Cache-Control"] = "public, max-age=600, stale-while-revalidate=120"
            elif path.startswith("/api/v1/wards/") or path in ("/api/v1/emergency/numbers",):
                response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"

            # ── Short-lived / dynamic public data ──
            elif path.startswith("/api/v1/emergency/nearby"):
                response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=30"
            elif path.startswith("/api/v1/emergency/sos"):
                response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=60"
            elif path.startswith("/api/v1/challan/calculate") or path.startswith("/api/v1/challan/predict"):
                response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
            elif path.startswith("/api/v1/roadwatch/feed"):
                response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=60"
            elif path.startswith("/api/v1/geocode/"):
                response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=3600"
            elif path.startswith("/api/v1/civic/municipalities/nearby"):
                response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"

            # ── User-specific / private ──
            elif path.startswith("/api/v1/user/"):
                response.headers["Cache-Control"] = "private, max-age=60, stale-while-revalidate=30"
            elif path.startswith("/api/v1/providers/") or path.startswith("/api/v1/officers/") or path.startswith("/api/v1/garage/"):
                response.headers["Cache-Control"] = "private, max-age=30"

        return response


def setup_security_headers(app: FastAPI) -> None:
    app.add_middleware(SecurityHeadersMiddleware)
