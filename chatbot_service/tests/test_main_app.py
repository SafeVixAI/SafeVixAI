# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

@pytest.fixture(scope="module")
def client():
    # We patch things that might require real network/DB connections on startup
    with patch("main.LocalVectorStore.init_db", new_callable=AsyncMock):
        with patch("main.LocalVectorStore.ensure_index", new_callable=AsyncMock):
            with TestClient(app) as c:
                yield c

def test_app_health(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_app_openapi_schema(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
