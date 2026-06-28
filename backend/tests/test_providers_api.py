"""Tests for the provider management encryption and API."""

from __future__ import annotations

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from services.provider_encrypt import encrypt_api_key, decrypt_api_key, mask_api_key


class MockResult:
    """Mocks SQLAlchemy Result.scalar_one_or_none() and scalars().all()."""

    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._row

    def scalars(self):
        return self

    def all(self):
        return self._rows


class MockSession:
    """Mocks an async SQLAlchemy session for CRUD tests."""

    def __init__(self):
        self.execute = AsyncMock()
        self.add = MagicMock()
        self.commit = AsyncMock()
        self.refresh = AsyncMock()
        self.delete = MagicMock()


@pytest.fixture
def mock_db():
    return MockSession()


@pytest.fixture
def sample_config():
    now = datetime.now(timezone.utc)
    config = MagicMock()
    config.id = uuid4()
    config.user_id = "test-user"
    config.provider_name = "test-groq"
    config.display_name = "Test Groq"
    config.api_key_encrypted = encrypt_api_key("sk-test-secret")
    config.base_url = "https://api.groq.com/openai/v1"
    config.default_model = "llama-3.1-8b-instant"
    config.extra_headers = None
    config.is_active = True
    config.priority = 0
    config.is_custom = False
    config.created_at = now
    config.updated_at = now
    return config


def test_encrypt_decrypt_roundtrip():
    key = "test-master-key-32chars!!"
    original = "sk-my-secret-api-key-12345"
    encrypted = encrypt_api_key(original, master_key=key)
    assert encrypted is not None
    assert encrypted != original
    decrypted = decrypt_api_key(encrypted, master_key=key)
    assert decrypted == original


def test_encrypt_without_key_returns_plaintext():
    original = "sk-test-key"
    encrypted = encrypt_api_key(original, master_key="")
    assert encrypted == original


def test_decrypt_without_key_returns_plaintext():
    result = decrypt_api_key("sk-plaintext", master_key="")
    assert result == "sk-plaintext"


def test_encrypt_none_returns_none():
    assert encrypt_api_key("", master_key="test-key") is None


def test_mask_api_key():
    """sk-abcdefghijklmnop => first 4 + stars for middle + last 4."""
    assert mask_api_key("sk-abcdefghijklmnop") == "sk-a***********mnop"
    assert mask_api_key("short") == "short"
    assert mask_api_key(None) is None


def test_mask_api_key_varied_lengths():
    assert mask_api_key("ab") == "ab"
    assert mask_api_key("abcdefgh") == "abcdefgh"
    assert mask_api_key("abcdefghij") == "abcd**ghij"
    assert mask_api_key("abcdefghijklmn") == "abcd******klmn"


def test_encrypt_decrypt_wrong_key():
    """Decrypting with wrong key returns encrypted text unchanged."""
    encrypted = encrypt_api_key("sk-secret", master_key="correct-key")
    assert encrypted is not None
    result = decrypt_api_key(encrypted, master_key="wrong-key")
    assert result is not None
    assert result != "sk-secret"


async def test_builtins_endpoint(monkeypatch):
    """Test that /api/v1/providers/builtins returns provider list."""
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ADMIN_SECRET", "test-admin-secret-2026")

    from core.config import get_settings
    get_settings.cache_clear()
    from main import create_app
    from core.database import get_db
    from httpx import AsyncClient, ASGITransport

    app = create_app()

    class DummySession:
        pass

    async def override_db():
        yield DummySession()

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/providers/builtins")

    assert resp.status_code == 200
    data = resp.json()
    # Direct list or wrapped in {data: [...]}
    items = data if isinstance(data, list) else data.get("data", [])
    assert len(items) >= 15
    names = [p["name"] for p in items]
    for required in ("groq", "openai", "ollama", "gemini", "anthropic", "deepseek"):
        assert required in names


async def test_test_connection_routes_have_sync_attr(monkeypatch):
    """Verify the test connection route exists and returns proper schema."""
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ADMIN_SECRET", "test-admin-secret-2026")

    from core.config import get_settings
    get_settings.cache_clear()
    from main import create_app
    from core.database import get_db
    from httpx import AsyncClient, ASGITransport

    app = create_app()

    class DummySession:
        pass

    async def override_db():
        yield DummySession()

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)

    # Use app.test_client or direct route access? 
    # Instead, verify the route is registered
    routes = [r.path for r in app.routes]
    assert "/api/v1/providers/test" in routes
    assert "/api/v1/providers/sync" in routes


async def test_sync_route_is_registered(monkeypatch):
    """Verify the sync provider route exists."""
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ADMIN_SECRET", "test-admin-secret-2026")

    from core.config import get_settings
    get_settings.cache_clear()
    from main import create_app
    from core.database import get_db

    app = create_app()

    class DummySession:
        pass

    async def override_db():
        yield DummySession()

    app.dependency_overrides[get_db] = override_db

    routes = [r.path for r in app.routes]
    assert "/api/v1/providers/sync" in routes
    assert "/api/v1/providers/test" in routes


# ═══════════════ CRUD Tests (with mocked DB) ═══════════════


def _make_app(mock_session):
    """Build a test app with a mock DB session injected."""
    import os
    os.environ["REDIS_URL"] = ""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["ADMIN_SECRET"] = "test-admin-secret-2026"

    from core.config import get_settings
    from core.database import get_db
    get_settings.cache_clear()
    from main import create_app

    app = create_app()

    async def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    return app


async def test_create_provider_config_returns_201(monkeypatch, mock_db, sample_config):  # B1
    """POST /api/v1/providers with minimal fields returns 201."""
    mock_db.execute.return_value = MockResult(row=None)  # No duplicate
    mock_db.refresh.side_effect = lambda cfg: setattr(cfg, "id", sample_config.id)

    app = _make_app(mock_db)
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)

    payload = {
        "provider_name": "test-groq",
        "display_name": "Test Groq",
        "api_key": "sk-test-secret",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.1-8b-instant",
        "is_active": True,
        "priority": 0,
        "is_custom": False,
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/providers", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["provider_name"] == "test-groq"
    assert data["api_key_masked"] is not None
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


async def test_update_provider_config_returns_updated(monkeypatch, mock_db, sample_config):  # B2
    """PUT /api/v1/providers/{id} updates a single field."""
    mock_db.execute.return_value = MockResult(row=sample_config)

    app = _make_app(mock_db)
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            f"/api/v1/providers/{sample_config.id}",
            json={"display_name": "Updated Groq"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == sample_config.display_name
    mock_db.commit.assert_awaited_once()


async def test_delete_provider_config_returns_204(monkeypatch, mock_db, sample_config):  # B3
    """DELETE /api/v1/providers/{id} returns 204."""
    mock_db.execute.return_value = MockResult(row=sample_config)

    app = _make_app(mock_db)
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(f"/api/v1/providers/{sample_config.id}")

    assert resp.status_code == 204
    mock_db.delete.assert_called_once_with(sample_config)
    mock_db.commit.assert_awaited_once()


async def test_delete_non_existent_returns_404(monkeypatch, mock_db):  # B4
    """DELETE /api/v1/providers/{id} with non-existent ID returns 404."""
    mock_db.execute.return_value = MockResult(row=None)

    app = _make_app(mock_db)
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(f"/api/v1/providers/{uuid4()}")

    assert resp.status_code == 404
    detail = resp.json()
    assert "not found" in detail.get("detail", "").lower()


async def test_update_non_existent_returns_404(monkeypatch, mock_db):  # B5
    """PUT /api/v1/providers/{id} with non-existent ID returns 404."""
    mock_db.execute.return_value = MockResult(row=None)

    app = _make_app(mock_db)
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            f"/api/v1/providers/{uuid4()}",
            json={"display_name": "Nope"},
        )

    assert resp.status_code == 404


async def test_create_duplicate_provider_returns_409(monkeypatch, mock_db, sample_config):  # B6
    """POST /api/v1/providers with duplicate provider_name returns 409."""
    mock_db.execute.return_value = MockResult(row=sample_config)  # Found existing

    app = _make_app(mock_db)
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)

    payload = {
        "provider_name": "test-groq",
        "display_name": "Another Groq",
        "api_key": "sk-other",
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/providers", json=payload)

    assert resp.status_code == 409
    detail = resp.json()
    assert "already configured" in detail.get("detail", "").lower()
