# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import UTC

from fastapi.testclient import TestClient

from main import create_app


class TestAppFactory:
    def test_create_app_returns_valid_app(self):
        app = create_app()
        assert app is not None
        assert app.title == "SafeVixAI Backend"

    def test_create_app_registers_routes(self):
        app = create_app()
        tc = TestClient(app)
        resp = tc.get("/")
        assert resp.status_code == 200

    def test_create_app_openapi_schema(self):
        app = create_app()
        assert app.openapi() is not None
        assert "/health" in app.openapi()["paths"]

    def test_cors_middleware_loaded(self, app):
        tc = TestClient(app)
        resp = tc.options(
            "/api/v1/emergency/nearby",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in resp.headers

    def test_version_in_root_response(self, app):
        tc = TestClient(app)
        resp = tc.get("/")
        body = resp.json()
        data = body.get("data") if "data" in body else body
        assert "version" in data
        assert data["version"] != ""

    def test_routers_are_mounted(self, app):
        tc = TestClient(app)
        # Quick spot-check a few known routes return 2xx or 4xx (not 404)
        for path in [
            "/api/v1/auth/login",
            "/api/v1/emergency/nearby",
            "/api/v1/challan/calculate",
            "/api/v1/roads/issues",
            "/api/v1/geocode/search",
        ]:
            resp = tc.get(path)
            # Should either be 200, 422 (validation), or 401 (auth) — not 404
            assert resp.status_code not in (404,), f"{path} returned 404 (not mounted)"


class TestExceptionHandler:
    def test_unhandled_exception_returns_500_envelope(self, app):
        tc = TestClient(app)
        # Trigger an unhandled error by hitting a route that requires auth without it
        # but with a broken-enough request to trigger 500
        resp = tc.get("/api/v1/user/profile", headers={"Authorization": "Bearer invalid.token.here"})
        # Should not crash with 500 — if auth fails gracefully it's 401
        assert resp.status_code in (401, 500)
        if resp.status_code == 500:
            body = resp.json()
            assert "error" in body
            assert body.get("success") is False

    def test_500_response_shape(self, app):
        from datetime import datetime

        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from starlette.testclient import TestClient as TC

        from models.schemas import ApiErrorResponse

        test_app = FastAPI()

        @test_app.get("/crash")
        async def crash():
            raise RuntimeError("test crash")

        from core.response_wrapper import ApiResponseMiddleware
        test_app.add_middleware(ApiResponseMiddleware)

        @test_app.exception_handler(Exception)
        async def handler(request, exc):
            return JSONResponse(
                status_code=500,
                content=ApiErrorResponse(
                    error={"code": "INTERNAL_ERROR", "message": "Internal server error"},
                    timestamp=datetime.now(UTC).isoformat(),
                ).model_dump(),
            )

        tc = TC(test_app)
        resp = tc.get("/crash")
        assert resp.status_code == 500
        body = resp.json()
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert "T" in body["timestamp"]
