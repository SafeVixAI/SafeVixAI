# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""API Versioning middleware for SafeVixAI Backend.

Implements API versioning via URL path (/api/v1, /api/v2) with
deprecation headers and version negotiation.

Phase 0.4: Prevents breaking changes from affecting all clients simultaneously.
"""
from __future__ import annotations

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Deprecation schedule for API versions
DEPRECATION_SCHEDULE = {
    "v1": {
        "deprecated": False,
        "sunset_date": None,  # Set when v2 is stable
        "documentation_url": "/docs/api/v1",
    },
    "v2": {
        "deprecated": False,
        "sunset_date": None,
        "documentation_url": "/docs/api/v2",
    },
}


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Middleware that adds versioning headers and handles deprecation."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Extract API version from path
        version = None
        if path.startswith("/api/v"):
            parts = path.split("/")
            if len(parts) >= 3 and parts[2].startswith("v"):
                version = parts[2]

        response = await call_next(request)

        if version and version in DEPRECATION_SCHEDULE:
            schedule = DEPRECATION_SCHEDULE[version]

            # Add version header
            response.headers["X-API-Version"] = version

            # Add deprecation headers if applicable
            if schedule["deprecated"]:
                response.headers["Deprecation"] = "true"
                if schedule["sunset_date"]:
                    response.headers["Sunset"] = schedule["sunset_date"]
                response.headers["Link"] = f'<{schedule["documentation_url"]}>; rel="successor-version"'

            # Add supported versions header
            response.headers["X-API-Supported-Versions"] = ", ".join(DEPRECATION_SCHEDULE.keys())

        return response


def get_deprecation_headers(version: str) -> dict[str, str]:
    """Get deprecation headers for a specific API version."""
    schedule = DEPRECATION_SCHEDULE.get(version, {})
    headers = {}

    if schedule.get("deprecated"):
        headers["Deprecation"] = "true"
        if schedule.get("sunset_date"):
            headers["Sunset"] = schedule["sunset_date"]
        if schedule.get("documentation_url"):
            headers["Link"] = f'<{schedule["documentation_url"]}>; rel="successor-version"'

    return headers
