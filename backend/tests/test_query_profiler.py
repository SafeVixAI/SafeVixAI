# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

from middleware.query_profiler import QueryProfilerMiddleware, setup_query_profiler


@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(QueryProfilerMiddleware, threshold_ms=1)

    @app.get("/fast")
    async def fast():
        return JSONResponse({"status": "ok"})

    return app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


class TestQueryProfiler:
    def test_response_time_header(self, client):
        resp = client.get("/fast")
        assert resp.status_code == 200
        assert "X-Response-Time-Ms" in resp.headers

    def test_fast_request(self, client):
        resp = client.get("/fast")
        elapsed = float(resp.headers["X-Response-Time-Ms"])
        assert elapsed >= 0

    def test_json_response(self, client):
        resp = client.get("/fast")
        assert resp.json() == {"status": "ok"}

    def test_fast_request_logs_debug(self, client, caplog):
        """Fast requests should log at DEBUG level (line 34 fast path)."""
        caplog.set_level(logging.DEBUG)
        with patch("middleware.query_profiler.logger") as mock_logger:
            resp = client.get("/fast")
            assert resp.status_code == 200
            # Should call logger.debug for fast requests
            mock_logger.debug.assert_called_once()
            mock_logger.warning.assert_not_called()

    def test_setup_query_profiler_registers_middleware(self):
        """setup_query_profiler should add middleware to app."""
        app = FastAPI()
        setup_query_profiler(app, threshold_ms=500)
        # Verify middleware is registered by making a request
        @app.get("/health")
        async def health():
            return {"ok": True}
        client = TestClient(app)
        resp = client.get("/health")
        assert "X-Response-Time-Ms" in resp.headers
