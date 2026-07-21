# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import secrets
import logging

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections.abc import Callable
from typing import Any

from core.config import get_settings

logger = logging.getLogger("safevixai.csrf")


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        csrf_cookie = request.cookies.get("csrf_token")

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            has_bearer = request.headers.get("Authorization", "").startswith("Bearer ")
            skip_paths = (
                request.url.path.startswith("/api/v1/auth/login")
                or request.url.path.startswith("/mcp")
            )
            settings = get_settings()
            if settings.environment != "test" and not has_bearer and not skip_paths:
                csrf_header = request.headers.get("X-CSRF-Token")
                if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF token missing or invalid"},
                    )

        response = await call_next(request)

        if not csrf_cookie:
            new_token = secrets.token_urlsafe(32)
            settings = get_settings()
            is_prod = settings.environment == "production"
            response.set_cookie(
                key="csrf_token",
                value=new_token,
                httponly=False,
                secure=is_prod,
                samesite="lax",
                path="/",
            )
        return response


def setup_csrf(app: FastAPI) -> None:
    app.add_middleware(CSRFMiddleware)
