# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import UTC

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from core.response_wrapper import ApiResponseMiddleware


@pytest.fixture
def plain_app():
    """A minimal FastAPI app with some test endpoints and the middleware."""
    app = FastAPI()

    @app.get("/api/v1/test/data")
    async def data():
        return {"key": "value", "count": 42}

    @app.get("/api/v1/test/list")
    async def list_data():
        return [1, 2, 3]

    @app.get("/api/v1/test/empty")
    async def empty():
        return {}

    @app.get("/api/v1/test/string")
    async def string():
        return JSONResponse(content="raw string", media_type="application/json")

    @app.get("/api/v1/test/error")
    async def error():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")

    @app.get("/api/v1/test/serverror")
    async def serverror():
        raise RuntimeError("Something went wrong")

    @app.get("/api/v1/test/html")
    async def html():
        return JSONResponse(content="<html></html>", media_type="text/html")

    @app.get("/api/v1/test/204")
    async def no_content():
        return JSONResponse(status_code=204, content=None)

    @app.get("/api/v1/test/text")
    async def text_plain():
        from starlette.responses import Response
        return Response(content="plain text", media_type="text/plain")

    # Exception handler must be registered BEFORE middleware so it catches errors
    # before the middleware layer processes the response
    from datetime import datetime

    from models.schemas import ApiErrorResponse

    @app.exception_handler(Exception)
    async def test_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content=ApiErrorResponse(
                error={"code": "INTERNAL_ERROR", "message": "Internal server error"},
                timestamp=datetime.now(UTC).isoformat(),
            ).model_dump(),
        )

    app.add_middleware(ApiResponseMiddleware)

    return app


@pytest.fixture
def client(plain_app):
    return TestClient(plain_app)


class TestApiResponseMiddleware:
    def test_wraps_200_dict_response(self, client):
        resp = client.get("/api/v1/test/data")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == {"key": "value", "count": 42}
        assert body["error"] is None
        assert "timestamp" in body

    def test_wraps_200_list_response(self, client):
        resp = client.get("/api/v1/test/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == [1, 2, 3]

    def test_wraps_200_empty_dict(self, client):
        resp = client.get("/api/v1/test/empty")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == {}

    def test_skips_4xx_error(self, client):
        resp = client.get("/api/v1/test/error")
        assert resp.status_code == 404
        body = resp.json()
        # Should NOT be wrapped — 404 is not 2xx
        assert "success" not in body
        assert body["detail"] == "Not found"

    def test_skips_non_json_media_type(self, client):
        resp = client.get("/api/v1/test/text")
        assert resp.status_code == 200
        assert resp.text == "plain text"

    def test_skips_empty_204_response(self, client):
        resp = client.get("/api/v1/test/204")
        assert resp.status_code == 204

    def test_500_returns_apierrorresponse(self, client):
        resp = client.get("/api/v1/test/serverror")
        assert resp.status_code == 500
        body = resp.json()
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"]["code"] == "INTERNAL_ERROR"

    def test_timestamp_is_iso_format(self, client):
        resp = client.get("/api/v1/test/data")
        body = resp.json()
        assert "T" in body["timestamp"]
        assert body["timestamp"].endswith("+00:00") or body["timestamp"].endswith("Z")

    def test_preserves_response_headers(self, client):
        resp = client.get("/api/v1/test/data")
        # Content-Type should still be json
        assert "application/json" in resp.headers.get("content-type", "")


class TestApiResponseModel:
    def test_model_defaults(self):
        from models.schemas import ApiResponse
        r = ApiResponse(data={"msg": "ok"})
        assert r.success is True
        assert r.data == {"msg": "ok"}
        assert r.error is None
        assert r.timestamp == ""

    def test_error_response_model(self):
        from models.schemas import ApiErrorResponse
        r = ApiErrorResponse(error={"code": "ERR", "message": "fail"})
        assert r.success is False
        assert r.data is None
        assert r.error["code"] == "ERR"


class TestHealthEndpoint:
    def test_health_returns_503_or_200(self, app, monkeypatch):
        from main import create_app
        monkeypatch.setenv("REDIS_URL", "")
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("ADMIN_SECRET", "test-admin-secret-2026")
        from core.config import get_settings
        get_settings.cache_clear()
        test_app = create_app()
        tc = TestClient(test_app)
        resp = tc.get("/health")
        # Health can be 503 (DB down) or 200 (DB up) in test
        assert resp.status_code in (200, 503)
        body = resp.json()
        # The middleware wraps it — check inside data
        if body.get("success") is True:
            data = body["data"]
            assert "status" in data
            assert "dependencies" in data
        else:
            assert "status" in body

    def test_root_endpoint(self, app):
        tc = TestClient(app)
        resp = tc.get("/")
        assert resp.status_code == 200
        body = resp.json()
        if "success" in body:
            data = body["data"]
            assert "service" in data
        else:
            assert "service" in body
