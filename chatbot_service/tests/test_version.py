# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestVersionEndpoint:
    def test_version_returns_200(self, client):
        resp = client.get("/api/v1/version")
        assert resp.status_code == 200

    def test_version_contains_expected_fields(self, client):
        resp = client.get("/api/v1/version")
        data = resp.json()
        assert "version" in data
        assert "service" in data
        assert "environment" in data

    def test_version_string(self, client):
        resp = client.get("/api/v1/version")
        assert resp.json()["version"] == "1.0.0"
