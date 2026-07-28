# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def app():
    from api.v1.probes import set_startup_complete
    set_startup_complete()
    from main import create_app
    app = create_app()
    return app


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


class TestReadinessProbe:
    def test_readyz_all_ok(self, client):
        resp = client.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        # 2xx responses wrapped in ApiResponse envelope: {"success":true,"data":{...}}
        assert "data" in data
        assert "status" in data["data"]
        assert "services" in data["data"]

    def test_readyz_contains_all_services(self, client):
        resp = client.get("/readyz")
        data = resp.json()
        services = data.get("data", {}).get("services", data.get("services", {}))
        assert "database" in services
        assert "cache" in services
        assert "chatbot" in services

    def test_readyz_db_down_returns_degraded(self, client):
        with patch("api.v1.probes.check_database", return_value=False):
            resp = client.get("/readyz")
            data = resp.json()
            # 503 responses are NOT wrapped
            services = data.get("services", {})
            assert services.get("database") == "degraded"

    def test_readyz_cache_down_returns_degraded(self, client):
        with patch("api.v1.probes.asyncio_wrap", side_effect=Exception("timeout")):
            resp = client.get("/readyz")
            assert resp.status_code in (200, 503)

    def test_readyz_db_and_cache_down_returns_503(self, client):
        with patch("api.v1.probes.check_database", return_value=False):
            with patch("api.v1.probes.asyncio_wrap", side_effect=Exception("timeout")):
                resp = client.get("/readyz")
                assert resp.status_code == 503
                data = resp.json()
                assert data["status"] == "degraded"


class TestLivenessProbe:
    def test_livez_returns_200(self, client):
        resp = client.get("/livez")
        assert resp.status_code == 200

    def test_livez_returns_alive_status(self, client):
        resp = client.get("/livez")
        assert resp.json() == {"status": "alive"}

    def test_livez_is_instant(self, client):
        import time
        start = time.time()
        client.get("/livez")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100, "liveness probe must respond in under 100ms"


class TestStartupProbe:
    def test_startupz_after_startup(self, client):
        resp = client.get("/startupz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "started"

    def test_startupz_before_startup(self):
        import importlib
        import api.v1.probes as probes_mod
        importlib.reload(probes_mod)
        probes_mod._startup_complete = False
        from main import create_app
        test_app = create_app()
        from fastapi.testclient import TestClient
        with TestClient(test_app) as c:
            resp = c.get("/startupz")
            assert resp.status_code == 503
            assert resp.json()["status"] == "starting"

    def test_startupz_transitions_to_started(self, client):
        from api.v1.probes import set_startup_complete, _startup_complete
        # _startup_complete is already True here because app fixture calls set_startup_complete
        resp = client.get("/startupz")
        assert resp.status_code == 200
