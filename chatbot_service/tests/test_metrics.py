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


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_has_correct_content_type(self, client):
        resp = client.get("/metrics")
        assert resp.headers.get("content-type", "").startswith("text/plain")

    def test_metrics_contains_expected_keys(self, client):
        resp = client.get("/metrics")
        body = resp.text
        assert "chatbot_request_total" in body
        assert "chatbot_response_time_seconds" in body
        assert "chatbot_fallback_total" in body
        assert "api_request_total" in body
