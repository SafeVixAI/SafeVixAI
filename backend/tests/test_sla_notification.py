# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.sla_notification import (
    _NOTIFIED_CACHE,
    COOLDOWN_MINUTES,
    SLANotificationService,
)


@pytest.fixture(autouse=True)
def clear_cache():
    _NOTIFIED_CACHE.clear()
    yield


class TestConstructor:
    def test_defaults_without_env(self):
        svc = SLANotificationService()
        assert svc.email_enabled is False
        assert svc.webhook_enabled is False
        assert svc.alert_email == ""
        assert svc.alert_password == ""
        assert svc.smtp_host == "smtp.gmail.com"
        assert svc.smtp_port == 587
        assert svc.webhook_url == ""
        assert svc.recipients == []

    def test_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("SLA_ALERT_EMAIL", "alerts@example.com")
        monkeypatch.setenv("SLA_ALERT_EMAIL_PASSWORD", "secret")
        monkeypatch.setenv("SLA_WEBHOOK_URL", "https://hooks.slack.com/xyz")
        monkeypatch.setenv("SLA_ALERT_RECIPIENTS", "a@b.com, c@d.com")
        monkeypatch.setenv("SLA_SMTP_HOST", "smtp.mailgun.org")
        monkeypatch.setenv("SLA_SMTP_PORT", "465")

        svc = SLANotificationService()
        assert svc.email_enabled is True
        assert svc.webhook_enabled is True
        assert svc.alert_email == "alerts@example.com"
        assert svc.webhook_url == "https://hooks.slack.com/xyz"
        assert svc.recipients == ["a@b.com", "c@d.com"]
        assert svc.smtp_host == "smtp.mailgun.org"
        assert svc.smtp_port == 465

    def test_empty_recipients_parsed(self, monkeypatch):
        monkeypatch.setenv("SLA_ALERT_RECIPIENTS", "")
        svc = SLANotificationService()
        assert svc.recipients == []

    def test_whitespace_recipients_skipped(self, monkeypatch):
        monkeypatch.setenv("SLA_ALERT_RECIPIENTS", "  , , ")
        svc = SLANotificationService()
        assert svc.recipients == []


class TestNotifySLABreach:
    def _make_svc(self, **env_vars):
        svc = SLANotificationService()
        for k, v in env_vars.items():
            setattr(svc, k, v)
        return svc

    @pytest.mark.asyncio
    async def test_cooldown_returns_false(self):
        svc = self._make_svc()
        _NOTIFIED_CACHE["REF-001"] = datetime.now(UTC) - timedelta(minutes=5)
        result = await svc.notify_sla_breach(
            complaint_ref="REF-001", issue_type="pothole", severity=3,
            city="Chennai", ward_id="W1",
            sla_deadline=datetime.now(UTC) - timedelta(hours=2),
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_cooldown_expired_allows_notification(self):
        svc = self._make_svc()
        _NOTIFIED_CACHE["REF-002"] = datetime.now(UTC) - timedelta(minutes=COOLDOWN_MINUTES + 1)
        svc.email_enabled = True
        svc.recipients = ["admin@example.com"]
        with (
            patch.object(svc, "_send_email") as mock_email,
            patch.object(svc, "_send_webhook", new_callable=AsyncMock),
        ):
            result = await svc.notify_sla_breach(
                complaint_ref="REF-002", issue_type="pothole", severity=4,
                city="Chennai", ward_id="W1",
                sla_deadline=datetime.now(UTC) - timedelta(hours=3),
            )
        assert result is True
        mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_disabled_webhook_enabled(self):
        svc = self._make_svc(webhook_url="https://hooks.example.com", webhook_enabled=True)
        with patch.object(svc, "_send_webhook", new_callable=AsyncMock) as mock_webhook:
            result = await svc.notify_sla_breach(
                complaint_ref="REF-003", issue_type="flooding", severity=5,
                city=None, ward_id=None,
                sla_deadline=datetime.now(UTC) - timedelta(hours=1),
            )
        assert result is True
        mock_webhook.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_webhook_disabled_email_enabled(self):
        svc = self._make_svc(
            email_enabled=True, alert_email="a@b.com",
            recipients=["admin@example.com"],
        )
        with patch.object(svc, "_send_email") as mock_email:
            result = await svc.notify_sla_breach(
                complaint_ref="REF-004", issue_type="pothole", severity=2,
                city="Delhi", ward_id="W2",
                sla_deadline=datetime.now(UTC) - timedelta(hours=4),
            )
        assert result is True
        mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_both_disabled_returns_false(self):
        svc = self._make_svc()
        result = await svc.notify_sla_breach(
            complaint_ref="REF-005", issue_type="pothole", severity=1,
            city="Mumbai", ward_id="W3",
            sla_deadline=datetime.now(UTC) - timedelta(hours=2),
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_both_enabled_both_succeed(self):
        svc = self._make_svc(
            email_enabled=True, alert_email="a@b.com",
            recipients=["admin@example.com"],
            webhook_url="https://hooks.example.com", webhook_enabled=True,
        )
        with (
            patch.object(svc, "_send_email") as mock_email,
            patch.object(svc, "_send_webhook", new_callable=AsyncMock) as mock_webhook,
        ):
            result = await svc.notify_sla_breach(
                complaint_ref="REF-006", issue_type="flooding", severity=5,
                city="Kolkata", ward_id="W4",
                sla_deadline=datetime.now(UTC) - timedelta(hours=6),
            )
        assert result is True
        mock_email.assert_called_once()
        mock_webhook.assert_awaited_once()
        assert "REF-006" in _NOTIFIED_CACHE

    @pytest.mark.asyncio
    async def test_email_fails_webhook_succeeds(self):
        svc = self._make_svc(
            email_enabled=True, alert_email="a@b.com",
            recipients=["admin@example.com"],
            webhook_url="https://hooks.example.com", webhook_enabled=True,
        )
        with (
            patch.object(svc, "_send_email", side_effect=RuntimeError("SMTP down")),
            patch.object(svc, "_send_webhook", new_callable=AsyncMock) as mock_webhook,
        ):
            result = await svc.notify_sla_breach(
                complaint_ref="REF-007", issue_type="pothole", severity=3,
                city="Chennai", ward_id="W1",
                sla_deadline=datetime.now(UTC) - timedelta(hours=2),
            )
        assert result is True
        mock_webhook.assert_awaited_once()
        assert "REF-007" in _NOTIFIED_CACHE

    @pytest.mark.asyncio
    async def test_webhook_fails_email_succeeds(self):
        svc = self._make_svc(
            email_enabled=True, alert_email="a@b.com",
            recipients=["admin@example.com"],
            webhook_url="https://hooks.example.com", webhook_enabled=True,
        )
        with (
            patch.object(svc, "_send_email") as mock_email,
            patch.object(svc, "_send_webhook", new_callable=AsyncMock, side_effect=httpx.HTTPError("500")) as mock_webhook,
        ):
            result = await svc.notify_sla_breach(
                complaint_ref="REF-008", issue_type="flooding", severity=4,
                city="Delhi", ward_id="W5",
                sla_deadline=datetime.now(UTC) - timedelta(hours=3),
            )
        assert result is True
        mock_email.assert_called_once()
        mock_webhook.assert_awaited_once()
        assert "REF-008" in _NOTIFIED_CACHE

    @pytest.mark.asyncio
    async def test_both_fail_returns_false(self):
        svc = self._make_svc(
            email_enabled=True, alert_email="a@b.com",
            recipients=["admin@example.com"],
            webhook_url="https://hooks.example.com", webhook_enabled=True,
        )
        with (
            patch.object(svc, "_send_email", side_effect=RuntimeError("fail")),
            patch.object(svc, "_send_webhook", new_callable=AsyncMock, side_effect=httpx.HTTPError("fail")),
        ):
            result = await svc.notify_sla_breach(
                complaint_ref="REF-009", issue_type="pothole", severity=2,
                city="Mumbai", ward_id="W6",
                sla_deadline=datetime.now(UTC) - timedelta(hours=5),
            )
        assert result is False
        assert "REF-009" not in _NOTIFIED_CACHE

    @pytest.mark.asyncio
    async def test_with_escalation_path(self):
        svc = self._make_svc(
            email_enabled=True, alert_email="a@b.com",
            recipients=["admin@example.com"],
        )
        with patch.object(svc, "_send_email") as mock_email:
            result = await svc.notify_sla_breach(
                complaint_ref="REF-010", issue_type="pothole", severity=3,
                city="Chennai", ward_id="W7",
                sla_deadline=datetime.now(UTC) - timedelta(hours=1),
                escalation_path="NHAI > Ministry",
            )
        assert result is True
        mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_recipients_skips_email(self):
        svc = self._make_svc(email_enabled=True, alert_email="a@b.com", webhook_enabled=True, webhook_url="https://hooks.example.com")
        with patch.object(svc, "_send_webhook", new_callable=AsyncMock) as mock_webhook:
            result = await svc.notify_sla_breach(
                complaint_ref="REF-011", issue_type="pothole", severity=3,
                city="Chennai", ward_id="W8",
                sla_deadline=datetime.now(UTC) - timedelta(hours=2),
            )
        assert result is True
        mock_webhook.assert_awaited_once()


class TestFormatBody:
    def test_contains_all_fields(self):
        svc = SLANotificationService()
        body = svc._format_body(
            complaint_ref="REF-001", issue_type="pothole", severity=3,
            city="Chennai", ward_id="W1",
            sla_deadline=datetime(2026, 5, 23, 12, 0, 0),
            overdue_hours=5.5, escalation_path="NHAI",
        )
        assert "REF-001" in body
        assert "pothole" in body
        assert "3" in body
        assert "Chennai" in body
        assert "W1" in body
        assert "2026-05-23 12:00" in body
        assert "5.5" in body
        assert "NHAI" in body

    def test_without_escalation_path(self):
        svc = SLANotificationService()
        body = svc._format_body(
            complaint_ref="REF-002", issue_type="flooding", severity=4,
            city="None", ward_id="None",
            sla_deadline=datetime(2026, 5, 22, 10, 0, 0),
            overdue_hours=2.0, escalation_path=None,
        )
        assert "REF-002" in body

    def test_handles_string_deadline(self):
        svc = SLANotificationService()
        body = svc._format_body(
            complaint_ref="REF-003", issue_type="pothole", severity=2,
            city="Delhi", ward_id="W3",
            sla_deadline="2026-05-23",
            overdue_hours=3.0, escalation_path="Test",
        )
        assert "2026-05-23" in body


class TestSendEmail:
    def test_sends_via_smtp(self):
        svc = SLANotificationService()
        svc.alert_email = "alerts@example.com"
        svc.alert_password = "secret"
        svc.recipients = ["admin@example.com"]
        svc.smtp_host = "smtp.gmail.com"
        svc.smtp_port = 587

        mock_server = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_server

        with patch("services.sla_notification.smtplib.SMTP", return_value=mock_context):
            svc._send_email("Subject", "Body text")

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("alerts@example.com", "secret")
        mock_server.send_message.assert_called_once()
        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["Subject"] == "Subject"
        assert sent_msg["From"] == "alerts@example.com"
        assert sent_msg["To"] == "admin@example.com"


class TestSendWebhook:
    @pytest.mark.asyncio
    async def test_sends_post_with_correct_payload(self):
        svc = SLANotificationService()
        svc.webhook_url = "https://hooks.example.com/webhook"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        with patch("services.sla_notification.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)

            await svc._send_webhook(
                complaint_ref="REF-001", issue_type="pothole", severity=3,
                city="Chennai", overdue_hours=5.5,
                subject="SLA BREACH: REF-001",
            )

        mock_client.post.assert_awaited_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://hooks.example.com/webhook"
        payload = call_args[1]["json"]
        assert payload["text"] is not None
        assert "REF-001" in payload["text"]
        assert "pothole" in payload["text"]
        assert "blocks" in payload

    @pytest.mark.asyncio
    async def test_handles_http_error(self):
        svc = SLANotificationService()
        svc.webhook_url = "https://hooks.example.com/webhook"

        with patch("services.sla_notification.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_cls.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))

            with pytest.raises(httpx.HTTPError):
                await svc._send_webhook(
                    complaint_ref="REF-001", issue_type="pothole", severity=3,
                    city="Chennai", overdue_hours=5.5,
                    subject="SLA BREACH",
                )
