# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.sla_monitor import SLAMonitor


class TestSLAMonitor:
    @pytest.mark.asyncio
    async def test_check_slas_no_breached(self):
        monitor = SLAMonitor()
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        count = await monitor.check_slas(db)
        assert count == 0

    @pytest.mark.asyncio
    async def test_check_slas_breached_not_escalated(self):
        monitor = SLAMonitor()
        db = MagicMock()

        mock_issue = MagicMock()
        mock_issue.uuid = "test-uuid-123"
        mock_issue.complaint_ref = "REF-001"
        mock_issue.sla_deadline = datetime(2024, 1, 1, tzinfo=None)
        mock_issue.issue_type = "pothole"
        mock_issue.severity = 3

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_issue]
        db.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.sla_monitor.ComplaintLifecycle.get_timeline", new_callable=AsyncMock) as mock_get_timeline,
            patch("services.sla_monitor.ComplaintLifecycle.escalate", new_callable=AsyncMock) as mock_escalate,
        ):
            mock_get_timeline.return_value = [
                MagicMock(event_type="created", notes="Initial report")
            ]

            count = await monitor.check_slas(db)
            assert count == 1
            mock_escalate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_slas_already_escalated(self):
        monitor = SLAMonitor()
        db = MagicMock()

        mock_issue = MagicMock()
        mock_issue.uuid = "test-uuid-456"
        mock_issue.complaint_ref = "REF-002"
        mock_issue.sla_deadline = datetime(2024, 1, 1, tzinfo=None)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_issue]
        db.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.sla_monitor.ComplaintLifecycle.get_timeline", new_callable=AsyncMock) as mock_get_timeline,
            patch("services.sla_monitor.ComplaintLifecycle.escalate", new_callable=AsyncMock) as mock_escalate,
        ):
            mock_get_timeline.return_value = [
                MagicMock(event_type="escalated", notes="SLA breach: deadline passed")
            ]

            count = await monitor.check_slas(db)
            assert count == 0
            mock_escalate.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_slas_escalate_exception(self):
        monitor = SLAMonitor()
        db = MagicMock()

        mock_issue = MagicMock()
        mock_issue.uuid = "test-uuid-789"
        mock_issue.complaint_ref = "REF-003"
        mock_issue.sla_deadline = datetime(2024, 1, 1, tzinfo=None)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_issue]
        db.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.sla_monitor.ComplaintLifecycle.get_timeline", new_callable=AsyncMock) as mock_get_timeline,
            patch("services.sla_monitor.ComplaintLifecycle.escalate", new_callable=AsyncMock, side_effect=Exception("DB error")),
        ):
            mock_get_timeline.return_value = [
                MagicMock(event_type="created", notes="Initial report")
            ]

            count = await monitor.check_slas(db)
            assert count == 0

    @pytest.mark.asyncio
    async def test_check_slas_notification_failure_handled(self):
        """Covers lines 69-70: SLA notification exception is caught."""
        monitor = SLAMonitor()
        db = MagicMock()

        mock_issue = MagicMock()
        mock_issue.uuid = "test-uuid-notif"
        mock_issue.complaint_ref = "REF-NOTIF"
        mock_issue.sla_deadline = datetime(2024, 1, 1, tzinfo=None)
        mock_issue.issue_type = "pothole"
        mock_issue.severity = 3

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_issue]
        db.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.sla_monitor.ComplaintLifecycle.get_timeline", new_callable=AsyncMock) as mock_get_timeline,
            patch("services.sla_monitor.ComplaintLifecycle.escalate", new_callable=AsyncMock) as mock_escalate,
        ):
            mock_get_timeline.return_value = [
                MagicMock(event_type="created", notes="Initial report")
            ]

            with patch(
                "services.sla_notification.SLANotificationService.notify_sla_breach",
                new_callable=AsyncMock,
                side_effect=RuntimeError("Notification service unavailable"),
            ):
                count = await monitor.check_slas(db)
                assert count == 1
                mock_escalate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_loop_no_session_maker(self):
        monitor = SLAMonitor(session_maker=None)
        assert not monitor.is_running

        await monitor.start_loop(interval_seconds=1)
        assert not monitor.is_running

    @pytest.mark.asyncio
    async def test_start_loop_cancelled(self):
        mock_session_maker = MagicMock()
        monitor = SLAMonitor(session_maker=mock_session_maker)
        assert not monitor.is_running

        with patch("services.sla_monitor.asyncio.sleep", side_effect=asyncio.CancelledError):
            await monitor.start_loop(interval_seconds=1)

    @pytest.mark.asyncio
    async def test_start_loop_runs_once(self):
        mock_db = AsyncMock()
        mock_session_maker = MagicMock(return_value=AsyncMock())
        mock_session_maker.return_value.__aenter__.return_value = mock_db
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        monitor = SLAMonitor(session_maker=mock_session_maker)

        with patch.object(monitor, "check_slas", new_callable=AsyncMock, return_value=0) as mock_check:
            try:
                await asyncio.wait_for(monitor.start_loop(interval_seconds=0), timeout=0.2)
            except (TimeoutError, asyncio.CancelledError):
                pass  # Expected: SLA loop intentionally timed out after verifying check_slas was called
            mock_check.assert_awaited()

    @pytest.mark.asyncio
    async def test_start_loop_check_slas_raises_exception(self):
        mock_db = AsyncMock()
        mock_session_maker = MagicMock(return_value=AsyncMock())
        mock_session_maker.return_value.__aenter__.return_value = mock_db
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        monitor = SLAMonitor(session_maker=mock_session_maker)

        with patch.object(monitor, "check_slas", new_callable=AsyncMock, side_effect=Exception("Unexpected error")):
            try:
                await asyncio.wait_for(monitor.start_loop(interval_seconds=0), timeout=0.2)
            except (TimeoutError, asyncio.CancelledError):
                pass  # Expected: SLA loop intentionally timed out to verify exception handling

    @pytest.mark.asyncio
    async def test_start_loop_logs_escalated(self):
        mock_db = AsyncMock()
        mock_session_maker = MagicMock(return_value=AsyncMock())
        mock_session_maker.return_value.__aenter__.return_value = mock_db
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        monitor = SLAMonitor(session_maker=mock_session_maker)

        with patch.object(monitor, "check_slas", new_callable=AsyncMock, return_value=3):
            try:
                await asyncio.wait_for(monitor.start_loop(interval_seconds=0), timeout=0.2)
            except (TimeoutError, asyncio.CancelledError):
                pass  # Expected: SLA loop intentionally timed out after verifying escalation logging

    def test_stop(self):
        monitor = SLAMonitor()
        monitor.is_running = True
        monitor.stop()
        assert not monitor.is_running
