# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.idempotency import IdempotencyMiddleware


class FakeRedis:
    """In-memory fake for idempotency cache with close support."""

    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def setex(self, key, ttl, value):
        self._store[key] = value

    async def close(self):
        self._store.clear()


@pytest.fixture
def app():
    app = FastAPI()

    @app.post("/test")
    async def test_post():
        return {"message": "ok"}

    @app.put("/test")
    async def test_put():
        return {"message": "updated"}

    @app.get("/test")
    async def test_get():
        return {"message": "get"}

    @app.post("/fail")
    async def test_fail():
        return {"message": "fail"}

    app.add_middleware(IdempotencyMiddleware)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_request_without_idempotency_key(client):
    response = client.post("/test")
    assert response.status_code == 200
    assert "X-Idempotency-Cached" not in response.headers


def test_get_ignores_idempotency(client):
    response = client.get("/test", headers={"Idempotency-Key": "test-key"})
    assert response.status_code == 200
    assert "X-Idempotency-Cached" not in response.headers


def test_first_request_caches_and_returns(client):
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    mock_cache.close = AsyncMock()

    with patch("core.idempotency.create_cache", return_value=mock_cache):
        response = client.post("/test", headers={"Idempotency-Key": "key-1"})
        assert response.status_code == 200
        assert response.headers.get("X-Idempotency-Cached") == "false"
        mock_cache.setex.assert_called_once()
        mock_cache.close.assert_called_once()


def test_second_request_returns_cached(client):
    cached_value = json.dumps({"status_code": 200, "body": {"message": "ok"}})
    mock_cache = AsyncMock()
    mock_cache.get.return_value = cached_value
    mock_cache.close = AsyncMock()

    with patch("core.idempotency.create_cache", return_value=mock_cache):
        response = client.post("/test", headers={"Idempotency-Key": "key-1"})
        assert response.status_code == 200
        assert response.headers.get("X-Idempotency-Cached") == "true"
        assert response.json() == {"message": "ok"}
        mock_cache.setex.assert_not_called()
        mock_cache.close.assert_called_once()


def test_different_keys_different_responses(client):
    cache = FakeRedis()

    with patch("core.idempotency.create_cache", return_value=cache):
        r1 = client.post("/test", headers={"Idempotency-Key": "key-1"})
        assert r1.status_code == 200
        assert r1.headers.get("X-Idempotency-Cached") == "false"

    with patch("core.idempotency.create_cache", return_value=cache):
        r2 = client.post("/test", headers={"Idempotency-Key": "key-2"})
        assert r2.status_code == 200
        assert r2.headers.get("X-Idempotency-Cached") == "false"


def test_cache_get_exception_falls_through(client):
    mock_cache = AsyncMock()
    mock_cache.get.side_effect = Exception("Redis down")
    mock_cache.close = AsyncMock()

    with patch("core.idempotency.create_cache", return_value=mock_cache):
        response = client.post("/test", headers={"Idempotency-Key": "key-1"})
        assert response.status_code == 200


def test_put_method_caches(client):
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    mock_cache.close = AsyncMock()

    with patch("core.idempotency.create_cache", return_value=mock_cache):
        response = client.put("/test", headers={"Idempotency-Key": "key-put"})
        assert response.status_code == 200
        assert response.headers.get("X-Idempotency-Cached") == "false"
        mock_cache.setex.assert_called_once()
        mock_cache.close.assert_called_once()
