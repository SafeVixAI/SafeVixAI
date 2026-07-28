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


class TestSpeechAPIVersioning:
    def test_legacy_speech_status(self, client):
        resp = client.get("/speech/status")
        assert resp.status_code in (200, 429)  # may be rate-limited

    def test_v1_speech_status(self, client):
        resp = client.get("/api/v1/speech/status")
        assert resp.status_code in (200, 429)


class TestAdminAPIVersioning:
    def test_legacy_admin_health_requires_auth(self, client):
        resp = client.get("/admin/health")
        # Should fail because admin auth is required
        assert resp.status_code in (403, 503)

    def test_v1_admin_health_requires_auth(self, client):
        resp = client.get("/api/v1/admin/health")
        assert resp.status_code in (403, 503)
