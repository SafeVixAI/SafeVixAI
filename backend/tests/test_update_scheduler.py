# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for the UpdateScheduler background task."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from services.update_scheduler import UpdateScheduler


@pytest.fixture
def scheduler() -> UpdateScheduler:
    return UpdateScheduler(session_factory=MagicMock())


class TestUpdateScheduler:
    """Test the update scheduler lifecycle and logic."""

    def test_init_not_running(self, scheduler: UpdateScheduler) -> None:
        assert scheduler.is_running is False
        assert scheduler.last_check is None

    def test_schedule_map_values(self) -> None:
        from services.update_scheduler import SCHEDULE_MAP
        assert SCHEDULE_MAP["immediate"] == 60
        assert SCHEDULE_MAP["hourly"] == 3600
        assert SCHEDULE_MAP["daily"] == 86400
        assert SCHEDULE_MAP["weekly"] == 604800

    @pytest.mark.asyncio
    async def test_start_stop(self, scheduler: UpdateScheduler) -> None:
        await scheduler.start()
        assert scheduler.is_running is True

        await scheduler.stop()
        assert scheduler.is_running is False
        assert scheduler.last_check is None

    @pytest.mark.asyncio
    async def test_start_twice_no_error(self, scheduler: UpdateScheduler) -> None:
        await scheduler.start()
        await scheduler.start()
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_get_status_not_running(self, scheduler: UpdateScheduler) -> None:
        status = await scheduler.get_status()
        assert status["running"] is False
        assert status["last_check"] is None
        assert status["task_active"] is False

    @pytest.mark.asyncio
    async def test_get_status_running(self, scheduler: UpdateScheduler) -> None:
        await scheduler.start()
        status = await scheduler.get_status()
        assert status["running"] is True
        await scheduler.stop()

    def test_is_check_due_no_last_check(self, scheduler: UpdateScheduler) -> None:
        settings = MagicMock()
        settings.last_checked_at = None
        assert scheduler._is_check_due(settings, 3600) is True

    def test_is_check_due_due(self, scheduler: UpdateScheduler) -> None:
        settings = MagicMock()
        settings.last_checked_at = datetime.now(UTC) - timedelta(hours=2)
        assert scheduler._is_check_due(settings, 3600) is True

    def test_is_check_due_not_due(self, scheduler: UpdateScheduler) -> None:
        settings = MagicMock()
        settings.last_checked_at = datetime.now(UTC) - timedelta(minutes=30)
        assert scheduler._is_check_due(settings, 3600) is False

    def test_get_interval_default(self, scheduler: UpdateScheduler) -> None:
        assert scheduler._get_interval("unknown") == 86400

    def test_get_interval_known(self, scheduler: UpdateScheduler) -> None:
        assert scheduler._get_interval("hourly") == 3600
        assert scheduler._get_interval("weekly") == 604800
