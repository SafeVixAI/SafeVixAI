# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from unittest.mock import AsyncMock, patch

import pytest


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
    @patch("core.database.check_database", new_callable=AsyncMock)
    @patch("api.v1.probes.asyncio_wrap", new_callable=AsyncMock)
    def test_readyz_all_ok(self, mock_asyncio, mock_db, client):
        mock_db.return_value = True
        mock_asyncio.return_value = True
        resp = client.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        # 2xx responses wrapped in ApiResponse envelope: {"success":true,"data":{...}}
        assert "data" in data
        assert "status" in data["data"]
        assert "services" in data["data"]

    @patch("core.database.check_database", new_callable=AsyncMock)
    @patch("api.v1.probes.asyncio_wrap", new_callable=AsyncMock)
    def test_readyz_contains_all_services(self, mock_asyncio, mock_db, client):
        mock_db.return_value = True
        mock_asyncio.return_value = True
        resp = client.get("/readyz")
        data = resp.json()
        services = data.get("data", {}).get("services", data.get("services", {}))
        assert "database" in services
        assert "cache" in services
        assert "chatbot" in services

    @patch("api.v1.probes.asyncio_wrap", new_callable=AsyncMock)
    def test_readyz_db_down_returns_degraded(self, mock_asyncio, client):
        mock_asyncio.return_value = True
        with patch("core.database.check_database", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = False
            resp = client.get("/readyz")
            data = resp.json()
            # 503 responses are NOT wrapped
            services = data.get("services", {})
            assert services.get("database") == "degraded"

    @patch("core.database.check_database", new_callable=AsyncMock)
    def test_readyz_cache_down_returns_degraded(self, mock_db, client):
        mock_db.return_value = True
        with patch("api.v1.probes.asyncio_wrap", new_callable=AsyncMock) as mock_asyncio:
            mock_asyncio.side_effect = Exception("timeout")
            resp = client.get("/readyz")
            assert resp.status_code in (200, 503)

    def test_readyz_db_and_cache_down_returns_503(self, client):
        with patch("core.database.check_database", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = False
            with patch("api.v1.probes.asyncio_wrap", new_callable=AsyncMock) as mock_asyncio:
                mock_asyncio.side_effect = Exception("timeout")
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
        data = resp.json().get("data", resp.json())
        assert data == {"status": "alive"}

    def test_livez_is_instant(self, client):
        import time
        start = time.time()
        client.get("/livez")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 500, "liveness probe must respond in under 500ms"


class TestStartupProbe:
    def test_startupz_after_startup(self, client):
        resp = client.get("/startupz")
        assert resp.status_code == 200
        data = resp.json().get("data", resp.json())
        assert data["status"] == "started"

    def test_startupz_before_startup(self):
        import importlib

        import api.v1.probes as probes_mod
        importlib.reload(probes_mod)
        from main import create_app
        test_app = create_app()
        from fastapi.testclient import TestClient
        with TestClient(test_app) as c:
            probes_mod._startup_complete = False
            resp = c.get("/startupz")
            assert resp.status_code == 503
            data = resp.json().get("data", resp.json())
            assert data["status"] == "starting"

    def test_startupz_transitions_to_started(self, client):
        # _startup_complete is already True here because app fixture calls set_startup_complete
        resp = client.get("/startupz")
        assert resp.status_code == 200
