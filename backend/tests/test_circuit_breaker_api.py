# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def disable_limiter():
    from core.limiter import limiter
    limiter.enabled = False
    yield


@pytest.fixture
def admin_auth_headers():
    token = MagicMock()
    return {"Authorization": "Bearer test-admin-token"}


@pytest.fixture
def cb_app():
    app = FastAPI()
    from api.v1.circuit_breaker_api import router, get_current_user
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: {"sub": "admin-user", "role": "admin"}
    return app


class TestListCircuitBreakers:
    def test_list_all(self, cb_app):
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry.all_stats") as mock_stats:
            mock_stats.return_value = {"overpass": {"state": "closed"}, "osm": {"state": "closed"}}
            client = TestClient(cb_app)
            response = client.get("/api/v1/circuit-breaker/")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2

    def test_list_empty(self, cb_app):
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry.all_stats") as mock_stats:
            mock_stats.return_value = {}
            client = TestClient(cb_app)
            response = client.get("/api/v1/circuit-breaker/")
            assert response.json()["count"] == 0


class TestGetCircuitBreaker:
    def test_get_existing(self, cb_app):
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry.all_stats") as mock_stats:
            mock_stats.return_value = {"overpass": {"state": "open", "failure_count": 5}}
            client = TestClient(cb_app)
            response = client.get("/api/v1/circuit-breaker/overpass")
            assert response.status_code == 200
            assert response.json()["breaker"]["state"] == "open"

    def test_get_not_found(self, cb_app):
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry.all_stats") as mock_stats:
            mock_stats.return_value = {}
            client = TestClient(cb_app)
            response = client.get("/api/v1/circuit-breaker/nonexistent")
            assert response.status_code == 404

    def test_get_requires_admin(self):
        app = FastAPI()
        from api.v1.circuit_breaker_api import router, get_current_user
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: {"sub": "user", "role": "operator"}
        client = TestClient(app)
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry.all_stats"):
            response = client.get("/api/v1/circuit-breaker/overpass")
            assert response.status_code in (401, 403)


class TestResetCircuitBreaker:
    def test_reset_all(self, cb_app):
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry.reset_all") as mock_reset:
            client = TestClient(cb_app)
            response = client.post("/api/v1/circuit-breaker/reset")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
            mock_reset.assert_called_once()

    def test_reset_requires_admin(self):
        app = FastAPI()
        from api.v1.circuit_breaker_api import router, get_current_user
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: {"sub": "user"}
        client = TestClient(app)
        response = client.post("/api/v1/circuit-breaker/reset")
        assert response.status_code in (401, 403)


class TestTriggerBreaker:
    def test_trigger_existing(self, cb_app):
        mock_cb = MagicMock()
        mock_cb.force_open = MagicMock()
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry._breakers", {"overpass": mock_cb}):
            client = TestClient(cb_app)
            response = client.post("/api/v1/circuit-breaker/trigger/overpass")
            assert response.status_code == 200
            mock_cb.force_open.assert_called_once()

    def test_trigger_not_found(self, cb_app):
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry._breakers", {}):
            client = TestClient(cb_app)
            response = client.post("/api/v1/circuit-breaker/trigger/nonexistent")
            assert response.status_code == 404

    def test_trigger_requires_admin(self):
        app = FastAPI()
        from api.v1.circuit_breaker_api import router, get_current_user
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: {"sub": "user"}
        client = TestClient(app)
        response = client.post("/api/v1/circuit-breaker/trigger/test")
        assert response.status_code in (401, 403)


class TestCloseBreaker:
    def test_close_existing(self, cb_app):
        mock_cb = MagicMock()
        mock_cb.force_close = MagicMock()
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry._breakers", {"overpass": mock_cb}):
            client = TestClient(cb_app)
            response = client.post("/api/v1/circuit-breaker/close/overpass")
            assert response.status_code == 200
            mock_cb.force_close.assert_called_once()

    def test_close_not_found(self, cb_app):
        with patch("api.v1.circuit_breaker_api.CircuitBreakerRegistry._breakers", {}):
            client = TestClient(cb_app)
            response = client.post("/api/v1/circuit-breaker/close/nonexistent")
            assert response.status_code == 404

    def test_close_requires_admin(self):
        app = FastAPI()
        from api.v1.circuit_breaker_api import router, get_current_user
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: {"sub": "user"}
        client = TestClient(app)
        response = client.post("/api/v1/circuit-breaker/close/test")
        assert response.status_code in (401, 403)
