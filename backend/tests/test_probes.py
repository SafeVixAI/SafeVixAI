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
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "services" in data

    def test_readyz_structure(self, client):
        resp = client.get("/readyz")
        data = resp.json()
        assert "database" in data["services"]
        assert "cache" in data["services"]
        assert "chatbot" in data["services"]


class TestLivenessProbe:
    def test_livez_returns_200(self, client):
        resp = client.get("/livez")
        assert resp.status_code == 200
        assert resp.json() == {"status": "alive"}


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
