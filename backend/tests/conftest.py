# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Global test configuration and fixtures for SafeVixAI backend."""
from __future__ import annotations

import os
import sys
from pathlib import Path, PosixPath, WindowsPath

# Python 3.11.9 removed Path._flavour which some libraries (PIL) depend on.
# Monkey-patch it back so Path() calls work without AttributeError.
if not hasattr(Path, '_flavour'):
    Path._flavour = PosixPath._flavour if os.name != 'nt' else WindowsPath._flavour

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from core.circuit_breaker import CircuitBreakerRegistry  # noqa: E402
from core.database import get_db  # noqa: E402
from core.security import create_access_token  # noqa: E402
from main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset all circuit breakers before each test to avoid shared state."""
    CircuitBreakerRegistry.reset_all()


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiting():
    """Disable rate limiting globally during test runs to prevent 429 errors."""
    from core.limiter import limiter
    limiter.enabled = False



class DummySession:
    pass


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ADMIN_SECRET", "test-admin-secret-2026")
    from core.config import get_settings
    get_settings.cache_clear()
    application = create_app()

    async def override_db():
        yield DummySession()

    application.dependency_overrides[get_db] = override_db
    return application


@pytest.fixture
def auth_headers():
    token = create_access_token({'sub': 'test-user', 'role': 'operator'})
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_auth_headers():
    token = create_access_token({'sub': 'admin-user'}, role='admin')
    return {'Authorization': f'Bearer {token}'}
