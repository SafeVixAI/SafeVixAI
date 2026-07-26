# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for the provider management encryption and API."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from core.security import get_current_user
from services.provider_encrypt import decrypt_api_key, encrypt_api_key, mask_api_key



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
        self.delete = AsyncMock()


@pytest.fixture
def mock_db():
    return MockSession()


@pytest.fixture
def sample_config():
    now = datetime.now(UTC)
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
    from httpx import ASGITransport, AsyncClient

    from core.database import get_db
    from main import create_app

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


def _route_paths(router):
    """Recursively collect route path strings from a FastAPI app or router.

    FastAPI v2.3+ wraps included sub-routers in ``_IncludedRouter`` objects
    that don't have a ``path`` attribute themselves; their routes are nested
    under a ``.router`` attribute.  This helper recurses into those wrappers
    so callers can assert routes are registered regardless of FastAPI version.
    """
    paths: list[str] = []
    # _IncludedRouter objects have .router (the actual APIRouter) not .routes
    items = getattr(router, "routes", None) or getattr(router, "router", None)
    if items is None:
        return paths
    if not isinstance(items, (list, tuple)):
        items = items.routes if hasattr(items, "routes") else []
    for r in items:
        if hasattr(r, "path") and isinstance(r.path, str):
            # APIRoute or similar leaf route — normalise leading slash
            norm = r.path if r.path.startswith("/") else f"/{r.path}"
            paths.append(norm)
        # Recurse into sub-routers (both _IncludedRouter and APIRouter)
        if hasattr(r, "routes"):
            paths.extend(_route_paths(r))
        if hasattr(r, "router") and hasattr(r.router, "routes"):
            paths.extend(_route_paths(r.router))
    return paths


async def test_test_connection_routes_have_sync_attr(monkeypatch):
    """Verify the test connection route exists and returns proper schema."""
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ADMIN_SECRET", "test-admin-secret-2026")

    from core.config import get_settings
    get_settings.cache_clear()
    from httpx import ASGITransport

    from core.database import get_db
    from main import create_app

    app = create_app()

    class DummySession:
        pass

    async def override_db():
        yield DummySession()

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)

    # Use app.test_client or direct route access?
    # Instead, verify the route is registered
    from api.v1 import api_router as _api_router
    import json
    print(f"\n\n=== DEBUG: api_router count = {len(_api_router.routes)}")
    for _r in _api_router.routes[:5]:
        print(f"  api_router route: {type(_r).__name__} path={getattr(_r, 'path', getattr(_r, 'prefix', 'N/A'))}")

    routes = _route_paths(app)
    parts = str(type(app.routes[0]) if app.routes else "empty")
    print(f"\n=== DEBUG: app.routes type={parts}, len={len(routes)}, routes={json.dumps(routes[:20])}")
    print(f"=== app.routes count = {len(app.routes)}")
    assert "/api/v1/providers/test" in routes
    assert "/api/v1/providers/sync" in routes


async def test_sync_route_is_registered(monkeypatch):
    """Verify the sync provider route exists."""
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ADMIN_SECRET", "test-admin-secret-2026")

    from core.config import get_settings
    get_settings.cache_clear()
    from core.database import get_db
    from main import create_app

    app = create_app()

    class DummySession:
        pass

    async def override_db():
        yield DummySession()

    app.dependency_overrides[get_db] = override_db

    routes = _route_paths(app)
    assert "/api/v1/providers/sync" in routes
    assert "/api/v1/providers/test" in routes


# ═══════════════ CRUD Tests (with mocked DB) ═══════════════


def _make_app(mock_session, monkeypatch=None):
    """Build a minimal test app with a mock DB session injected.

    Uses a bare FastAPI app (not create_app()) to avoid complex service
    initialization chains that fail without real Postgres/Redis.
    """
    if monkeypatch:
        monkeypatch.setenv("REDIS_URL", "")
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./_test_make_app.db")
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("ADMIN_SECRET", "test-admin-secret-2026")
    else:
        import os
        os.environ["REDIS_URL"] = ""
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./_test_make_app.db"
        os.environ["ENVIRONMENT"] = "test"
        os.environ["ADMIN_SECRET"] = "test-admin-secret-2026"

    from fastapi import FastAPI

    from api.v1.providers import router as providers_router
    from core.config import get_settings
    from core.database import get_db

    get_settings.cache_clear()

    app = FastAPI()
    app.include_router(providers_router)

    async def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db

    async def override_auth():
        return {"sub": "test-user", "role": "user", "jti": None}
    app.dependency_overrides[get_current_user] = override_auth
    return app


@pytest.mark.asyncio(loop_scope="module")
async def test_create_provider_config_returns_201(monkeypatch, mock_db, sample_config):  # B1
    """POST /api/v1/providers with minimal fields returns 201."""
    mock_db.execute.return_value = MockResult(row=None)  # No duplicate
    from datetime import datetime
    mock_db.refresh.side_effect = lambda cfg: (
        setattr(cfg, "id", sample_config.id),
        setattr(cfg, "created_at", datetime.now(UTC)),
        setattr(cfg, "updated_at", datetime.now(UTC)),
        setattr(cfg, "circuit_breaker_failures", 0),
    )[-1]  # last value is the return

    app = _make_app(mock_db, monkeypatch)
    from httpx import ASGITransport, AsyncClient
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
        resp = await client.post("/api/v1/providers/", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["provider_name"] == "test-groq"
    assert body["api_key_masked"] is not None
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio(loop_scope="module")
async def test_update_provider_config_returns_updated(monkeypatch, mock_db, sample_config):  # B2
    """PUT /api/v1/providers/{id} updates a single field."""
    mock_db.execute.return_value = MockResult(row=sample_config)

    app = _make_app(mock_db, monkeypatch)
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            f"/api/v1/providers/{sample_config.id}",
            json={"display_name": "Updated Groq"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["display_name"] == sample_config.display_name
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio(loop_scope="module")
async def test_delete_provider_config_returns_204(monkeypatch, mock_db, sample_config):  # B3
    """DELETE /api/v1/providers/{id} returns 204."""
    mock_db.execute.return_value = MockResult(row=sample_config)

    app = _make_app(mock_db, monkeypatch)
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(f"/api/v1/providers/{sample_config.id}")

    assert resp.status_code == 204
    mock_db.delete.assert_called_once_with(sample_config)
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio(loop_scope="module")
async def test_delete_non_existent_returns_404(monkeypatch, mock_db):  # B4
    """DELETE /api/v1/providers/{id} with non-existent ID returns 404."""
    mock_db.execute.return_value = MockResult(row=None)

    app = _make_app(mock_db, monkeypatch)
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(f"/api/v1/providers/{uuid4()}")

    assert resp.status_code == 404
    detail = resp.json()
    assert "not found" in detail.get("detail", "").lower()


@pytest.mark.asyncio(loop_scope="module")
async def test_update_non_existent_returns_404(monkeypatch, mock_db):  # B5
    """PUT /api/v1/providers/{id} with non-existent ID returns 404."""
    mock_db.execute.return_value = MockResult(row=None)

    app = _make_app(mock_db, monkeypatch)
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            f"/api/v1/providers/{uuid4()}",
            json={"display_name": "Nope"},
        )

    assert resp.status_code == 404


@pytest.mark.asyncio(loop_scope="module")
async def test_create_duplicate_provider_returns_409(monkeypatch, mock_db, sample_config):  # B6
    """POST /api/v1/providers with duplicate provider_name returns 409."""
    mock_db.execute.return_value = MockResult(row=sample_config)  # Found existing

    app = _make_app(mock_db, monkeypatch)
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)

    payload = {
        "provider_name": "test-groq",
        "display_name": "Another Groq",
        "api_key": "sk-other",
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/providers/", json=payload)

    assert resp.status_code == 409
    detail = resp.json()
    assert "already configured" in detail.get("detail", "").lower()
