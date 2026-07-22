# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Core API versioning tests — middleware headers, deprecation, versioning logic."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.versioning import (
    DEPRECATION_SCHEDULE,
    APIVersioningMiddleware,
    get_deprecation_headers,
)


class TestAPIVersioningMiddlewareHeaders:
    """Tests that middleware adds correct versioning headers."""

    def test_adds_x_api_version_header(self):
        app = FastAPI()
        app.add_middleware(APIVersioningMiddleware)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/api/v1/test")
        assert response.headers.get("X-API-Version") == "v1"

    def test_adds_supported_versions_header(self):
        app = FastAPI()
        app.add_middleware(APIVersioningMiddleware)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/api/v1/test")
        assert "v1" in response.headers.get("X-API-Supported-Versions", "")
        assert "v2" in response.headers.get("X-API-Supported-Versions", "")

    def test_non_api_path_no_headers(self):
        app = FastAPI()
        app.add_middleware(APIVersioningMiddleware)

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/health")
        assert "X-API-Version" not in response.headers

    def test_v2_path_gets_v2_header(self):
        app = FastAPI()
        app.add_middleware(APIVersioningMiddleware)

        @app.get("/api/v2/test")
        async def test_v2():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/api/v2/test")
        assert response.headers.get("X-API-Version") == "v2"


class TestAPIVersioningDeprecation:
    """Tests for deprecation headers."""

    def test_deprecated_version_adds_deprecation_header(self):
        schedule_backup = dict(DEPRECATION_SCHEDULE)
        DEPRECATION_SCHEDULE["v1"] = {
            "deprecated": True,
            "sunset_date": "2026-12-31",
            "documentation_url": "/docs/api/v2",
        }

        try:
            app = FastAPI()
            app.add_middleware(APIVersioningMiddleware)

            @app.get("/api/v1/test")
            async def test_endpoint():
                return {"ok": True}

            client = TestClient(app)
            response = client.get("/api/v1/test")
            assert response.headers.get("Deprecation") == "true"
            assert "Sunset" in response.headers
            assert "successor-version" in response.headers.get("Link", "")
        finally:
            DEPRECATION_SCHEDULE.clear()
            DEPRECATION_SCHEDULE.update(schedule_backup)

    def test_non_deprecated_version_no_deprecation_header(self):
        app = FastAPI()
        app.add_middleware(APIVersioningMiddleware)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/api/v1/test")
        assert "Deprecation" not in response.headers

    def test_deprecated_no_sunset_date_omits_sunset_header(self):
        schedule_backup = dict(DEPRECATION_SCHEDULE)
        DEPRECATION_SCHEDULE["v1"] = {
            "deprecated": True,
            "sunset_date": None,
            "documentation_url": "/docs/api/v2",
        }

        try:
            app = FastAPI()
            app.add_middleware(APIVersioningMiddleware)

            @app.get("/api/v1/test")
            async def test_endpoint():
                return {"ok": True}

            client = TestClient(app)
            response = client.get("/api/v1/test")
            assert response.headers.get("Deprecation") == "true"
            assert "Sunset" not in response.headers
        finally:
            DEPRECATION_SCHEDULE.clear()
            DEPRECATION_SCHEDULE.update(schedule_backup)

    def test_version_not_in_schedule_no_headers(self):
        app = FastAPI()
        app.add_middleware(APIVersioningMiddleware)

        @app.get("/api/v3/test")
        async def test_v3():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/api/v3/test")
        assert "X-API-Version" not in response.headers


class TestGetDeprecationHeaders:
    """Tests for the get_deprecation_headers utility."""

    def test_non_deprecated_returns_empty(self):
        headers = get_deprecation_headers("v1")
        assert headers == {}

    def test_deprecated_with_sunset(self):
        schedule_backup = dict(DEPRECATION_SCHEDULE)
        DEPRECATION_SCHEDULE["v1"] = {
            "deprecated": True,
            "sunset_date": "2026-12-31",
            "documentation_url": "/docs/api/v2",
        }

        try:
            headers = get_deprecation_headers("v1")
            assert headers["Deprecation"] == "true"
            assert headers["Sunset"] == "2026-12-31"
            assert "successor-version" in headers["Link"]
        finally:
            DEPRECATION_SCHEDULE.clear()
            DEPRECATION_SCHEDULE.update(schedule_backup)

    def test_unknown_version_returns_empty(self):
        headers = get_deprecation_headers("v99")
        assert headers == {}

    def test_deprecated_no_sunset(self):
        schedule_backup = dict(DEPRECATION_SCHEDULE)
        DEPRECATION_SCHEDULE["v1"] = {
            "deprecated": True,
            "sunset_date": None,
            "documentation_url": "/docs/api/v2",
        }

        try:
            headers = get_deprecation_headers("v1")
            assert headers["Deprecation"] == "true"
            assert "Sunset" not in headers
            assert "successor-version" in headers["Link"]
        finally:
            DEPRECATION_SCHEDULE.clear()
            DEPRECATION_SCHEDULE.update(schedule_backup)


class TestDeprecationSchedule:
    """Tests for deprecation schedule constants."""

    def test_v1_not_deprecated_by_default(self):
        assert DEPRECATION_SCHEDULE["v1"]["deprecated"] is False

    def test_v2_not_deprecated_by_default(self):
        assert DEPRECATION_SCHEDULE["v2"]["deprecated"] is False

    def test_schedule_has_two_versions(self):
        assert len(DEPRECATION_SCHEDULE) == 2

    def test_v1_has_documentation_url(self):
        assert "/docs/api/v1" in DEPRECATION_SCHEDULE["v1"]["documentation_url"]

    def test_v2_has_documentation_url(self):
        assert "/docs/api/v2" in DEPRECATION_SCHEDULE["v2"]["documentation_url"]
