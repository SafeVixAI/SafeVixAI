# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for core/database.py module-level code using fresh imports.

Uses sys.modules manipulation + fresh importlib.import_module to force
coverage.py to track module-level code execution (unlike importlib.reload()
which reuses the existing module object and may not be tracked).

Covers:
- Module-level connect_args with non-asyncpg URL (else branch)
- Module-level engine initialization with non-asyncpg URL  
- Conditional replica engine, session factories, and event listeners
- get_read_db with replica, check_replica_database branches
"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest


def _make_settings(
    database_url: str = "postgresql+asyncpg://localhost:5432/testdb",
    replica_url: str | None = None,
    **overrides,
) -> MagicMock:
    """Create a mock settings object with sensible defaults."""
    mock = MagicMock()
    mock.database_url = database_url
    mock.database_replica_url = replica_url
    mock.db_pool_size = 10
    mock.db_max_overflow = 20
    mock.db_pool_timeout_seconds = 30.0
    mock.db_pool_recycle_seconds = 1800
    mock.echo_queries = False
    mock.environment = "test"
    for key, value in overrides.items():
        setattr(mock, key, value)
    return mock


def _make_mock_engine():
    """Create a mock async engine whose sync_engine supports SQLAlchemy events."""
    from sqlalchemy import create_engine
    mock_engine = MagicMock()
    mock_engine.url = MagicMock()
    mock_engine.url.__str__ = MagicMock(return_value="mock://engine")
    mock_engine.sync_engine = create_engine("sqlite://", echo=False)
    return mock_engine


def _multi_patch(patches):
    """Context manager that applies multiple patches."""
    from contextlib import ExitStack
    stack = ExitStack()
    for p in patches:
        stack.enter_context(p)
    return stack


def _fresh_database_import(settings_mock, mock_engine=None):
    """Remove core.database from sys.modules and re-import fresh under patches.

    Uses fresh import (not reload) so coverage.py properly tracks the
    module-level code execution.
    """
    key = "core.database"
    if key in sys.modules:
        del sys.modules[key]

    patches = [
        patch("core.config.get_settings", return_value=settings_mock),
    ]
    if mock_engine is not None:
        patches.append(
            patch("sqlalchemy.ext.asyncio.create_async_engine", return_value=mock_engine)
        )

    with _multi_patch(patches):
        db = importlib.import_module(key)
        return db


# ── Teardown: restore real module after all tests ──────────────────────────

def teardown_module(module):
    """Restore core.database to original state after all tests."""
    key = "core.database"
    if key in sys.modules:
        del sys.modules[key]
    importlib.import_module(key)


# ── Tests ───────────────────────────────────────────────────────────────────

class TestModuleLevelConnectArgs:
    """Tests for module-level connect_args with different URL schemes."""

    def test_connect_args_empty_for_non_asyncpg(self):
        """connect_args should be empty dict for non-asyncpg URLs."""
        engine = _make_mock_engine()
        settings = _make_settings(database_url="postgresql://localhost/testdb")
        db = _fresh_database_import(settings, mock_engine=engine)
        assert db.connect_args == {}, f"Expected empty connect_args, got {db.connect_args}"

    def test_connect_args_has_cache_size_for_asyncpg(self):
        """connect_args should have prepared_statement_cache_size for asyncpg."""
        engine = _make_mock_engine()
        settings = _make_settings(database_url="postgresql+asyncpg://localhost/db")
        db = _fresh_database_import(settings, mock_engine=engine)
        assert db.connect_args.get("prepared_statement_cache_size") == 0

    def test_engine_created_with_non_asyncpg(self):
        """Module-level engine should be created with mock for non-asyncpg URL."""
        engine = _make_mock_engine()
        settings = _make_settings(database_url="postgresql://localhost/testdb")
        db = _fresh_database_import(settings, mock_engine=engine)
        assert db.engine is not None

    def test_engine_created_with_asyncpg_url(self):
        """Module-level engine should be created with asyncpg URL."""
        engine = _make_mock_engine()
        settings = _make_settings(database_url="postgresql+asyncpg://me:secret@localhost/mydb")
        db = _fresh_database_import(settings, mock_engine=engine)
        assert db.engine is not None


class TestModuleLevelReplica:
    """Tests for module-level replica engine initialization."""

    def test_no_replica_same_session_factory(self):
        """Without replica, AsyncReadSessionLocal should be AsyncSessionLocal (line 95)."""
        engine = _make_mock_engine()
        settings = _make_settings(replica_url=None)
        db = _fresh_database_import(settings, mock_engine=engine)
        assert db.AsyncReadSessionLocal is db.AsyncSessionLocal

    def test_with_replica_different_session_factory(self):
        """With replica, AsyncReadSessionLocal should differ from AsyncSessionLocal (line 90)."""
        engine = _make_mock_engine()
        settings = _make_settings(replica_url="postgresql+asyncpg://replica:5432/db")
        db = _fresh_database_import(settings, mock_engine=engine)
        assert db.AsyncReadSessionLocal is not db.AsyncSessionLocal

    def test_replica_engine_returns_replica(self):
        """With replica URL, get_replica_engine() should return a replica engine."""
        engine = _make_mock_engine()
        settings = _make_settings(replica_url="postgresql+asyncpg://replica:5432/db")
        db = _fresh_database_import(settings, mock_engine=engine)
        replica = db.get_replica_engine()
        assert replica is not None

    def test_replica_engine_none_without_replica(self):
        """Without replica URL, get_replica_engine() should return None."""
        engine = _make_mock_engine()
        settings = _make_settings(replica_url=None)
        db = _fresh_database_import(settings, mock_engine=engine)
        replica = db.get_replica_engine()
        assert replica is None


class TestModuleLevelEvents:
    """Tests for module-level event listeners with replica (lines 128-130)."""

    def test_replica_event_functions_exist(self):
        """Replica event listener functions should be defined when replica URL is set."""
        engine = _make_mock_engine()
        settings = _make_settings(replica_url="postgresql+asyncpg://replica:5432/db")
        db = _fresh_database_import(settings, mock_engine=engine)
        assert hasattr(db, "_replica_before_cursor_execute")
        assert hasattr(db, "_replica_after_cursor_execute")

    def test_replica_before_execute_sets_start_time(self):
        """_replica_before_cursor_execute should set query start time."""
        engine = _make_mock_engine()
        settings = _make_settings(replica_url="postgresql+asyncpg://replica:5432/db")
        db = _fresh_database_import(settings, mock_engine=engine)
        conn = MagicMock()
        db._replica_before_cursor_execute(conn, None, "SELECT 1", {}, None, False)
        assert hasattr(conn, "_query_start_time")
        assert conn._query_start_time > 0

    def test_no_replica_event_functions_absent(self):
        """Without replica URL, replica event functions should NOT be defined."""
        engine = _make_mock_engine()
        settings = _make_settings(replica_url=None)
        db = _fresh_database_import(settings, mock_engine=engine)
        assert not hasattr(db, "_replica_before_cursor_execute")
        assert not hasattr(db, "_replica_after_cursor_execute")


class TestModuleLevelCheckReplica:
    """Tests for check_replica_database with mock replica (line 151 branch)."""

    @pytest.mark.asyncio
    async def test_check_replica_database_connection_error(self):
        """check_replica_database should handle connection errors (line 151->exit)."""
        engine = _make_mock_engine()
        settings = _make_settings(replica_url="postgresql+asyncpg://replica:5432/db")
        db = _fresh_database_import(settings, mock_engine=engine)
        # Make check_replica_database fail
        with patch.object(db, "get_replica_engine") as mock_get_replica:
            mock_replica_engine = MagicMock()
            mock_conn_cm = MagicMock()
            mock_conn = MagicMock()
            mock_conn.execute.side_effect = Exception("Connection timeout")
            mock_conn_cm.__aenter__.return_value = mock_conn
            mock_conn_cm.__aexit__.return_value = False
            mock_replica_engine.connect.return_value = mock_conn_cm
            mock_get_replica.return_value = mock_replica_engine
            result = await db.check_replica_database()
            assert result is False


class TestModuleLevelFunctions:
    """Tests that functions from a fresh import work correctly."""

    def test_get_async_session_is_get_db(self):
        """get_async_session alias should point to get_db."""
        engine = _make_mock_engine()
        settings = _make_settings()
        db = _fresh_database_import(settings, mock_engine=engine)
        assert db.get_async_session is db.get_db

    @pytest.mark.asyncio
    async def test_check_database_test_env(self):
        """check_database should return True in test env."""
        engine = _make_mock_engine()
        settings = _make_settings(environment="test")
        db = _fresh_database_import(settings, mock_engine=engine)
        result = await db.check_database()
        assert result is True

    @pytest.mark.asyncio
    async def test_get_db_works(self):
        """get_db should yield sessions."""
        engine = _make_mock_engine()
        settings = _make_settings()
        db = _fresh_database_import(settings, mock_engine=engine)
        gen = db.get_db()
        session = await gen.__anext__()
        assert session is not None
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()
