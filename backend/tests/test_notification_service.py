# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.sla_notification import SLANotificationService, _NOTIFIED_CACHE


class TestSLANotificationService:
    def teardown_method(self) -> None:
        _NOTIFIED_CACHE.clear()

    def test_init_no_env(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            svc = SLANotificationService()
            assert svc.email_enabled is False
            assert svc.webhook_enabled is False
            assert svc.recipients == []

    def test_init_with_env(self) -> None:
        with patch.dict("os.environ", {"SLA_ALERT_EMAIL": "a@b.com", "SLA_ALERT_RECIPIENTS": "c@d.com, e@f.com"}):
            svc = SLANotificationService()
            assert svc.email_enabled is True
            assert len(svc.recipients) == 2

    async def test_cooldown_suppresses_duplicate(self) -> None:
        svc = SLANotificationService()
        deadline = datetime.now(UTC) - timedelta(hours=2)
        _NOTIFIED_CACHE["ref1"] = datetime.now(UTC)
        result = await svc.notify_sla_breach("ref1", "pothole", 4, "chennai", "ward1", deadline)
        assert result is False

    async def test_email_sent(self) -> None:
        svc = SLANotificationService()
        svc.email_enabled = True
        svc.recipients = ["a@b.com"]
        svc.alert_email = "alert@test.com"
        svc.alert_password = "pass"
        deadline = datetime.now(UTC) - timedelta(hours=2)
        with patch.object(svc, "_send_email") as mock_send:
            result = await svc.notify_sla_breach("ref1", "pothole", 4, "chennai", "ward1", deadline)
            assert result is True
            mock_send.assert_called_once()

    async def test_webhook_sent(self) -> None:
        svc = SLANotificationService()
        svc.webhook_enabled = True
        svc.webhook_url = "https://hooks.slack.com/test"
        deadline = datetime.now(UTC) - timedelta(hours=2)
        with patch.object(svc, "_send_webhook") as mock_webhook:
            result = await svc.notify_sla_breach("ref1", "pothole", 4, "chennai", "ward1", deadline)
            assert result is True
            mock_webhook.assert_called_once()

    async def test_email_failure_logged(self) -> None:
        svc = SLANotificationService()
        svc.email_enabled = True
        svc.recipients = ["a@b.com"]
        svc.alert_email = "alert@test.com"
        svc.alert_password = "pass"
        deadline = datetime.now(UTC) - timedelta(hours=2)
        with patch.object(svc, "_send_email", side_effect=Exception("SMTP down")):
            result = await svc.notify_sla_breach("ref1", "pothole", 4, "chennai", "ward1", deadline)
            assert result is False

    async def test_both_email_and_webhook(self) -> None:
        svc = SLANotificationService()
        svc.email_enabled = True
        svc.webhook_enabled = True
        svc.recipients = ["a@b.com"]
        svc.alert_email = "alert@test.com"
        svc.alert_password = "pass"
        svc.webhook_url = "https://hooks.test.com"
        deadline = datetime.now(UTC) - timedelta(hours=2)
        with patch.object(svc, "_send_email") as mock_email:
            with patch.object(svc, "_send_webhook") as mock_webhook:
                result = await svc.notify_sla_breach("ref1", "pothole", 4, "chennai", "ward1", deadline)
                assert result is True
                mock_email.assert_called_once()
                mock_webhook.assert_called_once()

    def test_format_body_includes_sla_info(self) -> None:
        svc = SLANotificationService()
        deadline = datetime(2026, 7, 15, 14, 30, tzinfo=UTC)
        body = svc._format_body(complaint_ref="CMP-001", issue_type="pothole", severity=4, city="chennai", ward_id="W-1", sla_deadline=deadline, overdue_hours=3.5, escalation_path="escalate")
        assert "CMP-001" in body
        assert "pothole" in body
        assert "3.5" in body

    def test_send_email_smtp(self) -> None:
        svc = SLANotificationService()
        svc.alert_email = "a@b.com"
        svc.alert_password = "pass"
        with patch("smtplib.SMTP") as mock_smtp:
            instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = instance
            svc._send_email("Subject", "Body text")
            instance.send_message.assert_called_once()

    async def test_send_webhook_httpx(self) -> None:
        svc = SLANotificationService()
        svc.webhook_url = "https://hooks.test.com/webhook"
        with patch("httpx.AsyncClient") as mock_client:
            client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = client_instance
            await svc._send_webhook(complaint_ref="CMP-001", issue_type="pothole", severity=4, city="chennai", subject="SLA BREACH")
            client_instance.post.assert_called_once()

    async def test_no_notification_when_not_needed(self) -> None:
        svc = SLANotificationService()
        svc.email_enabled = False
        svc.webhook_enabled = False
        deadline = datetime.now(UTC) - timedelta(hours=1)
        result = await svc.notify_sla_breach("ref1", "pothole", 3, "mumbai", "ward2", deadline)
        assert result is False

    def test_format_body_with_string_deadline(self) -> None:
        svc = SLANotificationService()
        body = svc._format_body(complaint_ref="CMP-002", sla_deadline="2026-07-15 14:30 UTC")
        assert "CMP-002" in body
