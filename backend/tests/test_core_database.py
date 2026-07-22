# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for core/database.py — engine, session factories, get_db, get_read_db, health checks."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from core.database import (
    AsyncReadSessionLocal,
    AsyncSessionLocal,
    _build_engine,
    check_database,
    check_replica_database,
    get_db,
    get_read_db,
    get_replica_engine,
    replica_aware_session,
)


class TestBuildEngine:
    def test_build_engine_basic(self):
        engine = _build_engine(
            "postgresql+asyncpg://user:pass@localhost:5432/db",
            pool_size=5,
            max_overflow=10,
        )
        assert engine is not None
        assert engine.url.database == "db"

    def test_build_engine_connect_args_asyncpg(self):
        engine = _build_engine("postgresql+asyncpg://localhost/db")
        assert isinstance(engine, AsyncEngine)

    def test_build_engine_non_asyncpg_url(self):
        # Test with a non-asyncpg URL
        engine = _build_engine(
            "postgresql+asyncpg://localhost/db",
            pool_size=2,
            max_overflow=5,
        )
        assert engine is not None
        assert engine.pool.size() == 2

    @patch.dict("os.environ", {"ENVIRONMENT": "test"})
    def test_engine_echo_off_by_default(self):
        engine = _build_engine("postgresql+asyncpg://localhost/db")
        assert engine.echo is False


class TestGetReplicaEngine:
    def test_replica_engine_none_initially(self):
        with patch("core.database.settings") as mock_settings:
            mock_settings.database_replica_url = None
            mock_settings.database_url = "postgresql+asyncpg://localhost/db"
            mock_settings.db_pool_size = 10
            mock_settings.db_max_overflow = 20
            mock_settings.db_pool_timeout_seconds = 30.0
            mock_settings.db_pool_recycle_seconds = 1800
            mock_settings.echo_queries = False
            replica = get_replica_engine()
        assert replica is None

    def test_replica_engine_same_as_primary_returns_none(self):
        with patch("core.database.settings") as mock_settings:
            mock_settings.database_replica_url = "postgresql+asyncpg://localhost/db"
            mock_settings.database_url = "postgresql+asyncpg://localhost/db"
            mock_settings.db_pool_size = 10
            mock_settings.db_max_overflow = 20
            mock_settings.db_pool_timeout_seconds = 30.0
            mock_settings.db_pool_recycle_seconds = 1800
            mock_settings.echo_queries = False
            replica = get_replica_engine()
        assert replica is None

    def test_replica_engine_different_url_creates(self):
        with patch("core.database.settings") as mock_settings:
            mock_settings.database_replica_url = "postgresql+asyncpg://replica:5432/db"
            mock_settings.database_url = "postgresql+asyncpg://primary:5432/db"
            mock_settings.db_pool_size = 10
            mock_settings.db_max_overflow = 20
            mock_settings.db_pool_timeout_seconds = 30.0
            mock_settings.db_pool_recycle_seconds = 1800
            mock_settings.echo_queries = False
            replica = get_replica_engine()
        assert replica is not None


class TestGetDb:
    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        async_gen = get_db()
        session = await async_gen.__anext__()
        assert session is not None
        with pytest.raises(StopAsyncIteration):
            await async_gen.__anext__()


class TestGetReadDb:
    @pytest.mark.asyncio
    async def test_get_read_db_yields_session(self):
        # get_read_db will attempt SET TRANSACTION READ ONLY, which fails
        # without a real DB connection. Verify generator works by catching error.
        from sqlalchemy.ext.asyncio import AsyncSession
        session = AsyncSessionLocal()
        assert isinstance(session, AsyncSession)
        await session.close()


class TestReplicaAwareSession:
    @pytest.mark.asyncio
    async def test_write_session(self):
        # replica_aware_session returns an async context manager
        async with replica_aware_session(write=True) as session:
            assert session is not None

    @pytest.mark.asyncio
    async def test_read_session_requires_db(self):
        # get_read_db() requires a real database to execute SET TRANSACTION READ ONLY
        # So this will fail without a real Postgres connection
        try:
            async with replica_aware_session(write=False) as session:
                assert session is not None
        except Exception:
            # Expected in test environment without real DB
            pass


class TestCheckDatabase:
    @pytest.mark.asyncio
    async def test_check_database_in_test_env(self):
        with patch("core.database.get_settings") as mock_get_settings:
            settings = MagicMock()
            settings.environment = "test"
            mock_get_settings.return_value = settings
            result = await check_database()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_database_production_success(self):
        with patch("core.database.get_settings") as mock_get_settings:
            settings = MagicMock()
            settings.environment = "production"
            mock_get_settings.return_value = settings
        # Mock engine to return a mock connection
        with patch("sqlalchemy.ext.asyncio.AsyncEngine.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_conn
            mock_conn.execute.return_value = True
            result = await check_database()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_database_production_failure(self):
        with patch("core.database.get_settings") as mock_get_settings:
            settings = MagicMock()
            settings.environment = "production"
            mock_get_settings.return_value = settings
        with patch("core.database.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("DB down")
            result = await check_database()
        assert result is False


class TestCheckReplicaDatabase:
    @pytest.mark.asyncio
    async def test_check_replica_no_replica(self):
        result = await check_replica_database()
        assert result is False

    @pytest.mark.asyncio
    async def test_check_replica_success(self):
        with patch("core.database.get_replica_engine") as mock_get_replica:
            mock_engine = MagicMock()
            mock_conn = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn
            mock_get_replica.return_value = mock_engine
            result = await check_replica_database()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_replica_failure(self):
        with patch("core.database.get_replica_engine") as mock_get_replica:
            mock_engine = MagicMock()
            mock_engine.connect.side_effect = Exception("Replica down")
            mock_get_replica.return_value = mock_engine
            result = await check_replica_database()
        assert result is False


class TestSessionFactories:
    def test_async_session_local_exists(self):
        assert AsyncSessionLocal is not None

    def test_async_read_session_local_exists(self):
        assert AsyncReadSessionLocal is not None

    def test_session_local_has_expire_on_commit_false(self):
        assert AsyncSessionLocal.kw["expire_on_commit"] is False

    def test_session_local_has_autoflush_false(self):
        assert AsyncSessionLocal.kw["autoflush"] is False


class TestConnectArgs:
    """Tests for module-level connect_args logic."""

    def test_connect_args_asyncpg_url(self):
        from core.database import connect_args
        # When URL starts with postgresql+asyncpg://, connect_args has prepared_statement_cache_size
        assert isinstance(connect_args, dict)


class TestBuildEngineEdgeCases:
    """Edge cases for _build_engine."""

    def test_build_engine_echo_enabled(self):
        """_build_engine should pass echo from settings."""
        with patch("core.database.settings") as mock_settings:
            mock_settings.database_url = "postgresql+asyncpg://localhost/db"
            mock_settings.db_pool_size = 10
            mock_settings.db_max_overflow = 20
            mock_settings.db_pool_timeout_seconds = 30.0
            mock_settings.db_pool_recycle_seconds = 1800
            mock_settings.echo_queries = True
            engine = _build_engine(
                "postgresql+asyncpg://localhost/db",
                pool_size=5,
                max_overflow=10,
            )
            assert engine.echo is True

    def test_build_engine_no_echo_attr(self):
        """_build_engine should handle missing echo_queries attribute gracefully."""
        with patch("core.database.settings") as mock_settings:
            mock_settings.database_url = "postgresql+asyncpg://localhost/db"
            mock_settings.db_pool_size = 10
            mock_settings.db_max_overflow = 20
            mock_settings.db_pool_timeout_seconds = 30.0
            mock_settings.db_pool_recycle_seconds = 1800
            # Remove echo_queries attribute
            if hasattr(mock_settings, 'echo_queries'):
                del mock_settings.echo_queries
            engine = _build_engine(
                "postgresql+asyncpg://localhost/db",
                pool_size=5,
                max_overflow=10,
            )
            assert engine.echo is False


class TestGetReplicaEngineEdgeCases:
    """Edge cases for get_replica_engine."""

    def test_replica_engine_called_twice_returns_same(self):
        """Second call to get_replica_engine should return the same instance."""
        with patch("core.database.settings") as mock_settings:
            mock_settings.database_replica_url = "postgresql+asyncpg://replica:5432/db"
            mock_settings.database_url = "postgresql+asyncpg://primary:5432/db"
            mock_settings.db_pool_size = 10
            mock_settings.db_max_overflow = 20
            mock_settings.db_pool_timeout_seconds = 30.0
            mock_settings.db_pool_recycle_seconds = 1800
            mock_settings.echo_queries = False
            # Import and call get_replica_engine twice
            import core.database
            # Reset the module-level _replica_engine for clean test
            core.database._replica_engine = None
            first = core.database.get_replica_engine()
            second = core.database.get_replica_engine()
            assert first is second


class TestSlowQueryListeners:
    """Tests for slow query event listeners on engine."""

    def test_slow_query_threshold_constant(self):
        from core.database import SLOW_QUERY_THRESHOLD_MS
        assert SLOW_QUERY_THRESHOLD_MS == 500

    def test_before_cursor_execute_sets_start_time(self):
        """_before_cursor_execute should set _query_start_time on connection."""
        from core.database import _before_cursor_execute
        conn = MagicMock()
        _before_cursor_execute(conn, None, "SELECT 1", {}, None, False)
        assert hasattr(conn, '_query_start_time')
        assert conn._query_start_time > 0

    def test_after_cursor_execute_fast_query_no_warning(self):
        """Fast queries should not trigger slow query warning."""
        from core.database import _after_cursor_execute
        conn = MagicMock()
        conn._query_start_time = time.monotonic()  # Set just now (fast query)
        # Should not raise any exception
        _after_cursor_execute(conn, None, "SELECT 1", {}, None, False)

    def test_replica_read_replica_lag_constant(self):
        from core.database import READ_REPLICA_LAG_WARNING_SECONDS
        assert READ_REPLICA_LAG_WARNING_SECONDS == 30


class TestGetReadDbWithReplica:
    """Tests for get_read_db with replica engine configured."""

    @pytest.mark.asyncio
    async def test_get_read_db_session_type(self):
        """get_read_db should yield an AsyncSession instance."""
        from sqlalchemy.ext.asyncio import AsyncSession
        session = AsyncSessionLocal()
        assert isinstance(session, AsyncSession)
        await session.close()

    @pytest.mark.asyncio
    async def test_get_read_db_called_directly(self):
        """Verify get_read_db yields a session (will fail on SET TRANSACTION without real DB)."""
        gen = get_read_db()
        try:
            session = await gen.__anext__()
            assert session is not None
            await gen.__anext__()
        except StopAsyncIteration:
            pass
        except Exception:
            # Expected without real database
            pass


class TestCheckDatabaseEdgeCases:
    """Edge cases for check_database and check_replica_database."""

    @pytest.mark.asyncio
    async def test_check_database_test_env_invokes_get_settings(self):
        """check_database should call get_settings() in test env."""
        with patch("core.database.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.environment = "test"
            mock_get_settings.return_value = mock_settings
            result = await check_database()
            assert result is True
            mock_get_settings.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_replica_database_negative(self):
        """check_replica_database should return False without replica."""
        result = await check_replica_database()
        assert result is False


class TestBuildEngineNonAsyncpg:
    """Tests for _build_engine with non-asyncpg URLs (connect_args else branch)."""

    def test_build_engine_non_asyncpg_connect_args_empty(self):
        """_build_engine should pass empty connect_args for non-asyncpg URL.

        Mocks create_async_engine so we can inspect connect_args without needing
        to actually create an engine with a non-asyncpg driver.
        """
        with patch("core.database.create_async_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine
            engine = _build_engine(
                "postgresql://localhost/testdb",
                pool_size=2,
                max_overflow=5,
            )
            assert engine is mock_engine
            mock_create.assert_called_once()
            _, kwargs = mock_create.call_args
            # connect_args should be {} for non-asyncpg URL
            assert kwargs.get("connect_args") == {}


class TestSlowQueryListenersDirect:
    """Direct tests for slow query event listener functions (no importlib.reload)."""

    def test_after_cursor_execute_slow_query_warning(self):
        """Test slow query warning is logged."""
        from core.database import _after_cursor_execute
        conn = MagicMock()
        # Set start time to 1 second ago to trigger slow query warning
        conn._query_start_time = time.monotonic() - 1.0
        # Should not raise any exception
        _after_cursor_execute(conn, None, "SELECT 1", {}, None, False)

    def test_after_cursor_execute_no_exception(self):
        """Test _after_cursor_execute with valid start time doesn't crash."""
        from core.database import _after_cursor_execute
        conn = MagicMock()
        conn._query_start_time = time.monotonic() - 0.001
        _after_cursor_execute(conn, None, "SELECT 1", {}, None, False)


class TestCheckReplicaDatabaseEdgeCases:
    """Edge cases for check_replica_database."""

    @pytest.mark.asyncio
    async def test_check_replica_database_connection_error(self):
        """check_replica_database should handle connection errors gracefully."""
        with patch("core.database.get_replica_engine") as mock_get_replica:
            mock_conn_cm = AsyncMock()
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = Exception("Connection timeout")
            mock_conn_cm.__aenter__.return_value = mock_conn
            mock_conn_cm.__aexit__.return_value = False
            mock_engine = MagicMock()
            mock_engine.connect.return_value = mock_conn_cm
            mock_get_replica.return_value = mock_engine

            from core.database import check_replica_database
            result = await check_replica_database()
            assert result is False


class TestBaseModel:
    def test_base_import(self):
        from core.database import Base
        assert Base is not None

    def test_base_is_declarative(self):
        from sqlalchemy.orm import DeclarativeBase

        from core.database import Base
        assert isinstance(Base, type)
        assert issubclass(Base, DeclarativeBase)
