# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.providers import router as providers_router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(providers_router)

    mock_engine = MagicMock()
    mock_router = MagicMock()
    mock_router.configure_user_providers.return_value = [
        {"provider_name": "groq", "model": "mixtral"}
    ]
    mock_router.get_active_provider_info.return_value = {
        "providers": [{"name": "groq", "model": "mixtral"}]
    }
    mock_engine.provider_router = mock_router
    app.state.chat_engine = mock_engine
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestConfigureProviders:
    def test_configure_providers(self, client):
        resp = client.post("/api/v1/providers/configure", json=[
            {"provider_name": "groq", "api_key": "key123", "base_url": None, "default_model": "mixtral", "is_custom": False, "priority": 1}
        ])
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["configured"] == 1

    def test_configure_providers_empty(self, client):
        resp = client.post("/api/v1/providers/configure", json=[])
        assert resp.status_code == 200


class TestGetActiveProviders:
    def test_get_active_providers(self, client):
        resp = client.get("/api/v1/providers/active")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert data["providers"][0]["name"] == "groq"


class TestTestProvider:
    def test_test_provider_missing_base_url(self, client):
        resp = client.post("/api/v1/providers/test", json={})
        assert resp.status_code == 400
        assert "base_url is required" in resp.json()["detail"]

    def test_test_provider_success(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(status_code=200)
            mock_client.return_value = mock_instance

            resp = client.post("/api/v1/providers/test", json={
                "api_key": "key123",
                "base_url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-3.5-turbo",
                "provider_name": "openai"
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"

    def test_test_provider_http_error(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(status_code=401, text="Unauthorized")
            mock_client.return_value = mock_instance

            resp = client.post("/api/v1/providers/test", json={
                "api_key": "bad_key",
                "base_url": "https://api.openai.com/v1/chat/completions"
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "error"

    def test_test_provider_exception(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.side_effect = ConnectionError("timeout")
            mock_client.return_value = mock_instance

            resp = client.post("/api/v1/providers/test", json={
                "api_key": "key",
                "base_url": "https://api.example.com/chat/completions"
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "error"
            assert "timeout" in data["message"]


class TestResetProviders:
    def test_reset_providers(self, client):
        resp = client.post("/api/v1/providers/reset")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
