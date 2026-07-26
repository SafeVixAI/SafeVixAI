# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.elements import TextClause

from services.data_retention import DataRetentionScheduler


@pytest.fixture
def session_factory():
    mock_session = AsyncMock(spec=AsyncSession)
    maker = MagicMock(spec=async_sessionmaker)
    maker.return_value.__aenter__.return_value = mock_session
    maker.return_value.__aexit__ = AsyncMock(return_value=None)
    return maker


@pytest.fixture
def scheduler(session_factory):
    return DataRetentionScheduler(session_factory)


class TestDataRetentionScheduler:
    def test_init(self, scheduler, session_factory):
        assert scheduler.session_factory is session_factory
        assert scheduler._running is False
        assert scheduler._task is None

    @pytest.mark.asyncio
    async def test_start_sets_running_and_creates_task(self, scheduler):
        await scheduler.start(interval_seconds=86400)
        assert scheduler._running is True
        assert scheduler._task is not None
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_when_already_running_does_nothing(self, scheduler):
        scheduler._running = True
        with patch.object(scheduler, '_task', None):
            await scheduler.start(interval_seconds=86400)
            # _task should still be None since start returned early
            assert scheduler._task is None
        scheduler._running = False

    def test_stop_sets_running_false(self, scheduler):
        scheduler._running = True
        scheduler._task = MagicMock()
        scheduler.stop()
        assert scheduler._running is False
        scheduler._task.cancel.assert_called_once()

    def test_stop_no_task(self, scheduler):
        scheduler._running = True
        scheduler._task = None
        scheduler.stop()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_cleanup_executes_stored_procedure(self, scheduler, session_factory):
        mock_session = session_factory.return_value.__aenter__.return_value
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rowcount = 0

        await scheduler.cleanup()

        calls = [c.args[0] for c in mock_session.execute.await_args_list
                 if isinstance(c.args[0], (str, TextClause))]
        assert any(
            "safevixai_cleanup_expired_data" in str(c) for c in calls
        ), "stored proc call not found"
        assert mock_session.commit.await_count >= 1

    @pytest.mark.asyncio
    async def test_cleanup_rollback_on_error(self, scheduler, session_factory):
        mock_session = session_factory.return_value.__aenter__.return_value
        mock_session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session.rollback = AsyncMock()

        await scheduler.cleanup()

        mock_session.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_loop_calls_cleanup_and_handles_cancel(self, scheduler):
        scheduler._running = True
        cleanup_called = False

        async def fake_cleanup():
            nonlocal cleanup_called
            cleanup_called = True
            scheduler._running = False  # Stop after first iteration

        scheduler.cleanup = fake_cleanup

        with patch("asyncio.sleep", AsyncMock()):
            await scheduler._loop(1)

        assert cleanup_called

    @pytest.mark.asyncio
    async def test_loop_handles_cancelled_error(self, scheduler):
        scheduler._running = True
        scheduler.cleanup = AsyncMock()

        with patch("asyncio.sleep", AsyncMock(side_effect=asyncio.CancelledError)):
            await scheduler._loop(1)

        scheduler.cleanup.assert_not_called()
        assert scheduler._running is True

    @pytest.mark.asyncio
    async def test_loop_handles_exception_in_cleanup(self, scheduler):
        scheduler._running = True

        async def fake_cleanup():
            scheduler._running = False
            raise RuntimeError("Unexpected error")

        scheduler.cleanup = fake_cleanup

        with patch("asyncio.sleep", AsyncMock()):
            await scheduler._loop(1)

    @pytest.mark.asyncio
    async def test_loop_skips_cleanup_when_stopped_during_sleep(self, scheduler):
        scheduler._running = True

        async def fake_sleep(_):
            scheduler._running = False

        with patch("asyncio.sleep", fake_sleep):
            await scheduler._loop(1)

    @pytest.mark.asyncio
    async def test_start_and_stop_workflow(self, session_factory):
        scheduler = DataRetentionScheduler(session_factory)
        assert scheduler._running is False

        await scheduler.start(interval_seconds=86400)
        assert scheduler._running is True

        scheduler.stop()
        assert scheduler._running is False
        assert scheduler._task is not None
