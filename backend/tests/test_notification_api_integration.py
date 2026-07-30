# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""pytest-httpx recording tests for notification dispatch HTTP calls."""

import pytest

try:
    from unittest.mock import AsyncMock, MagicMock, patch
except ImportError:
    pass

pytestmark = pytest.mark.skipif(
    not __import__('importlib').util.find_spec('pytest_httpx'),
    reason="requires pytest-httpx library",
)

from models.notification import (
    Notification,
    NotificationCategory,
    NotificationPriority,
)
from services.notification_service import NotificationService


def _make_mock_notification(**overrides):
    """Create a mock Notification-like object with minimal fields."""
    n = MagicMock(spec=Notification)
    n.id = '00000000-0000-0000-0000-000000000001'
    n.user_id = 'test_user'
    n.channel = MagicMock()
    n.channel.value = overrides.get('channel', 'slack')
    n.category = MagicMock()
    n.category.value = overrides.get('category', 'system_health')
    n.priority = MagicMock()
    n.priority.value = overrides.get('priority', 'normal')
    n.status = MagicMock()
    n.status.value = 'sent'
    n.title = overrides.get('title', 'Test Alert')
    n.body = overrides.get('body', 'Test notification body')
    n.payload = {}
    n.source = None
    n.correlation_id = None
    n.read_at = None
    n.delivered_at = None
    n.scheduled_for = None
    n.expires_at = None
    n.created_at = None
    n.updated_at = None
    return n


def _make_mock_prefs(**overrides):
    p = MagicMock()
    p.email_address = overrides.get('email', 'test@example.com')
    p.phone_number = overrides.get('phone', '+911234567890')
    p.push_token = overrides.get('push_token', '')
    p.slack_webhook_url = overrides.get('slack_webhook_url', '')
    p.discord_webhook_url = overrides.get('discord_webhook_url', '')
    p.teams_webhook_url = overrides.get('teams_webhook_url', '')
    p.webhook_url = overrides.get('webhook_url', '')
    p.channels_enabled = {}
    p.categories_enabled = {}
    p.dnd_enabled = False
    p.digest_enabled = False
    return p


# ── Slack Dispatch ──────────────────────────────────────────────────────


class TestSlackDispatchHTTP:
    """Verify Slack webhook HTTP call patterns."""

    @pytest.mark.asyncio
    async def test_slack_dispatch_success(self, httpx_mock):
        httpx_mock.add_response(status_code=200)
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(slack_webhook_url='https://hooks.slack.com/services/TEST/TOKEN')
        await svc._dispatch_slack(n, p)

    @pytest.mark.asyncio
    async def test_slack_dispatch_rate_limit(self, httpx_mock):
        httpx_mock.add_response(status_code=429)
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(slack_webhook_url='https://hooks.slack.com/services/TEST/TOKEN')
        with pytest.raises(Exception):
            await svc._dispatch_slack(n, p)

    @pytest.mark.asyncio
    async def test_slack_dispatch_no_url(self):
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(slack_webhook_url='')
        with pytest.raises(Exception, match='No Slack webhook URL'):
            await svc._dispatch_slack(n, p)


# ── Discord Dispatch ────────────────────────────────────────────────────


class TestDiscordDispatchHTTP:
    """Verify Discord webhook HTTP call patterns."""

    @pytest.mark.asyncio
    async def test_discord_dispatch_success(self, httpx_mock):
        httpx_mock.add_response(status_code=204)
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(discord_webhook_url='https://discord.com/api/webhooks/TEST/TOKEN')
        await svc._dispatch_discord(n, p)

    @pytest.mark.asyncio
    async def test_discord_dispatch_failure(self, httpx_mock):
        httpx_mock.add_response(status_code=400)
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(discord_webhook_url='https://discord.com/api/webhooks/TEST/TOKEN')
        with pytest.raises(Exception):
            await svc._dispatch_discord(n, p)

    @pytest.mark.asyncio
    async def test_discord_dispatch_no_url(self):
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(discord_webhook_url='')
        with pytest.raises(Exception, match='No Discord webhook URL'):
            await svc._dispatch_discord(n, p)


# ── Teams Dispatch ──────────────────────────────────────────────────────


class TestTeamsDispatchHTTP:
    """Verify Microsoft Teams webhook HTTP call patterns."""

    @pytest.mark.asyncio
    async def test_teams_dispatch_success(self, httpx_mock):
        httpx_mock.add_response(status_code=200)
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(teams_webhook_url='https://outlook.office.com/webhook/TEST')
        await svc._dispatch_teams(n, p)

    @pytest.mark.asyncio
    async def test_teams_dispatch_failure(self, httpx_mock):
        httpx_mock.add_response(status_code=500)
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(teams_webhook_url='https://outlook.office.com/webhook/TEST')
        with pytest.raises(Exception):
            await svc._dispatch_teams(n, p)


# ── Webhook Endpoint Test ───────────────────────────────────────────────


class TestWebhookTestHTTP:
    """Verify webhook test endpoint HTTP call patterns."""

    @pytest.mark.asyncio
    async def test_webhook_test_success(self, httpx_mock):
        httpx_mock.add_response(status_code=200)
        svc = NotificationService(db=MagicMock())
        result = await svc.test_webhook('https://example.com/hook')
        assert result is True

    @pytest.mark.asyncio
    async def test_webhook_test_404(self, httpx_mock):
        httpx_mock.add_response(status_code=404)
        svc = NotificationService(db=MagicMock())
        result = await svc.test_webhook('https://example.com/hook')
        assert result is False


# ── Template Render Tests (no HTTP) ─────────────────────────────────────


class TestNotificationTemplateRender:
    """Verify template rendering — no HTTP involved."""

    @pytest.mark.asyncio
    async def test_template_email_html(self):
        from services.email_templates import render_email_html
        cat = NotificationCategory.SYSTEM_HEALTH
        pri = NotificationPriority.CRITICAL
        html = render_email_html(title='Alert', body='System down', category=cat, priority=pri)
        assert 'Alert' in html

    @pytest.mark.asyncio
    async def test_template_sms_text(self):
        from services.email_templates import SMS_TEMPLATES
        assert isinstance(SMS_TEMPLATES, dict)
        assert len(SMS_TEMPLATES) > 0

    @pytest.mark.asyncio
    async def test_template_digest_html(self):
        from services.email_templates import render_digest_html
        html = render_digest_html(
            title='Daily Digest',
            categories={'system_health': 3, 'security': 1},
            period_start='2026-07-28T00:00:00Z',
            period_end='2026-07-28T23:59:59Z',
            total_count=4,
        )
        assert 'Daily' in html or 'Digest' in html or 'system_health' in html


# ── Email Dispatch ──────────────────────────────────────────────────────


class TestEmailDispatch:
    """Verify email dispatch via SMTP (no HTTP)."""

    @pytest.mark.asyncio
    async def test_email_dispatch_no_address(self):
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(email='')
        with pytest.raises(Exception, match='No email address'):
            await svc._dispatch_email(n, p)

    @pytest.mark.asyncio
    async def test_email_dispatch_uses_prefs_address(self):
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(email='test@example.com')
        with patch.object(svc, '_send_smtp', new_callable=AsyncMock) as mock_smtp:
            await svc._dispatch_email(n, p)
            mock_smtp.assert_called_once_with('test@example.com', 'Test Alert', 'Test notification body')


# ── SMS Dispatch ────────────────────────────────────────────────────────


class TestSMSDispatch:
    """Verify SMS dispatch (no HTTP — uses logging)."""

    @pytest.mark.asyncio
    async def test_sms_dispatch_no_phone(self):
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(phone='')
        with pytest.raises(Exception, match='No phone'):
            await svc._dispatch_sms(n, p)

    @pytest.mark.asyncio
    async def test_sms_dispatch_logs(self):
        svc = NotificationService(db=MagicMock())
        n = _make_mock_notification()
        p = _make_mock_prefs(phone='+911234567890')
        with patch.object(svc, '_send_sms_via_provider', new_callable=AsyncMock) as mock_sms:
            await svc._dispatch_sms(n, p)
            mock_sms.assert_called_once()
