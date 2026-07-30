# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Comprehensive tests for the enterprise notification system."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from models.notification import (
    Notification,
    NotificationCategory,
    NotificationChannel,
    NotificationDigest,
    NotificationEvent,
    NotificationPreference,
    NotificationPriority,
    NotificationStatus,
    NotificationTemplate,
    WebhookEndpoint,
)
from services.notification_service import NotificationService, create_default_templates


def _make_notification(**kwargs) -> Notification:
    data = dict(
        id=UUID('00000000-0000-0000-0000-000000000001'),
        user_id='test-user',
        channel=NotificationChannel.IN_APP,
        category=NotificationCategory.GENERAL,
        title='Test',
        status=NotificationStatus.PENDING,
    )
    data.update(kwargs)
    return Notification(**data)


def _make_mock_result(scalar_one_or_none_return=None, scalars_all_return=None):
    rows = scalars_all_return or []
    m = MagicMock()
    m.scalar_one_or_none = MagicMock(return_value=scalar_one_or_none_return)
    m.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=rows)))
    m.__iter__ = MagicMock(return_value=iter(rows))
    return m


def _make_db(**kwargs):
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock(return_value=_make_mock_result(**kwargs))
    return db


# ── Send Tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_creates_notification():
    db = _make_db(scalar_one_or_none_return=None)
    service = NotificationService(db=db)
    n = await service.send(
        user_id='u1', channel=NotificationChannel.IN_APP,
        category=NotificationCategory.GENERAL, title='Hello',
        body='World', priority=NotificationPriority.NORMAL,
        source='test', correlation_id='c1',
    )
    assert n.title == 'Hello'
    assert n.body == 'World'
    assert n.channel == NotificationChannel.IN_APP
    assert n.category == NotificationCategory.GENERAL
    assert n.correlation_id == 'c1'


@pytest.mark.asyncio
async def test_send_with_scheduled_future():
    db = _make_db(scalar_one_or_none_return=None)
    service = NotificationService(db=db)
    n = await service.send(
        user_id='u1', channel=NotificationChannel.IN_APP,
        category=NotificationCategory.GENERAL, title='T',
        scheduled_for=datetime.now(UTC) + timedelta(hours=2),
    )
    assert n.status == NotificationStatus.PENDING


@pytest.mark.asyncio
async def test_send_with_channel():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    for ch in NotificationChannel:
        n = await service.send(
            user_id='u1', channel=ch,
            category=NotificationCategory.GENERAL, title='T',
        )
        assert n.channel == ch


@pytest.mark.asyncio
async def test_send_with_category():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    for cat in NotificationCategory:
        n = await service.send(
            user_id='u1', channel=NotificationChannel.IN_APP,
            category=cat, title='T',
        )
        assert n.category == cat


@pytest.mark.asyncio
async def test_send_with_priority():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    for pri in NotificationPriority:
        n = await service.send(
            user_id='u1', channel=NotificationChannel.IN_APP,
            category=NotificationCategory.GENERAL, title='T',
            priority=pri,
        )
        assert n.priority == pri


@pytest.mark.asyncio
async def test_send_with_payload():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    payload = {'key': 'val'}
    n = await service.send(
        user_id='u1', channel=NotificationChannel.IN_APP,
        category=NotificationCategory.GENERAL, title='T',
        metadata=payload,
    )
    assert n.payload == payload


@pytest.mark.asyncio
async def test_send_with_expiry():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    n = await service.send(
        user_id='u1', channel=NotificationChannel.IN_APP,
        category=NotificationCategory.GENERAL, title='T',
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    assert n.expires_at is not None


@pytest.mark.asyncio
async def test_send_without_user_id():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    n = await service.send(
        channel=NotificationChannel.IN_APP,
        category=NotificationCategory.GENERAL, title='T',
    )
    assert n.user_id is None


# ── Preferences Tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dnd_blocks_normal():
    prefs = NotificationPreference(
        user_id='u1', dnd_enabled=True, dnd_start_hour=0, dnd_end_hour=23,
    )
    db = _make_db(scalar_one_or_none_return=prefs)
    service = NotificationService(db=db)
    n = await service.send(
        user_id='u1', channel=NotificationChannel.IN_APP,
        category=NotificationCategory.GENERAL, title='DND',
        priority=NotificationPriority.NORMAL,
    )
    assert n.status == NotificationStatus.PENDING
    assert n.payload and n.payload.get('dnd_queued')


@pytest.mark.asyncio
async def test_dnd_critical_bypasses():
    prefs = NotificationPreference(
        user_id='u1', dnd_enabled=True, dnd_start_hour=0, dnd_end_hour=23,
    )
    db = _make_db(scalar_one_or_none_return=prefs)
    service = NotificationService(db=db)
    service._dispatch_email = AsyncMock()
    n = await service.send(
        user_id='u1', channel=NotificationChannel.EMAIL,
        category=NotificationCategory.SECURITY, title='Critical',
        priority=NotificationPriority.CRITICAL,
    )
    assert n.status != NotificationStatus.PENDING
    assert not (n.payload or {}).get('dnd_queued')


@pytest.mark.asyncio
async def test_channel_disabled():
    prefs = NotificationPreference(
        user_id='u1', channels_enabled={'email': False, 'in_app': True},
    )
    db = _make_db(scalar_one_or_none_return=prefs)
    service = NotificationService(db=db)
    n = await service.send(
        user_id='u1', channel=NotificationChannel.EMAIL,
        category=NotificationCategory.GENERAL, title='Disabled',
    )
    assert n.status == NotificationStatus.CANCELLED


@pytest.mark.asyncio
async def test_category_disabled():
    prefs = NotificationPreference(
        user_id='u1', categories_enabled={'general': False},
    )
    db = _make_db(scalar_one_or_none_return=prefs)
    service = NotificationService(db=db)
    n = await service.send(
        user_id='u1', channel=NotificationChannel.IN_APP,
        category=NotificationCategory.GENERAL, title='Disabled',
    )
    assert n.status == NotificationStatus.CANCELLED


@pytest.mark.asyncio
async def test_quiet_hours_high_passes():
    prefs = NotificationPreference(
        user_id='u1', quiet_hours_enabled=True,
        quiet_hours_start='00:00', quiet_hours_end='23:59',
    )
    db = _make_db(scalar_one_or_none_return=prefs)
    service = NotificationService(db=db)
    n = await service.send(
        user_id='u1', channel=NotificationChannel.IN_APP,
        category=NotificationCategory.INCIDENT, title='Incident',
        priority=NotificationPriority.HIGH,
    )
    assert n.status in (NotificationStatus.SENT, NotificationStatus.PENDING)


@pytest.mark.asyncio
async def test_dnd_is_active():
    service = NotificationService(db=_make_db())
    off = NotificationPreference(user_id='t', dnd_enabled=False)
    assert not service._is_dnd_active(off)
    on = NotificationPreference(user_id='t', dnd_enabled=True, dnd_start_hour=0, dnd_end_hour=23)
    assert service._is_dnd_active(on)


@pytest.mark.asyncio
async def test_quiet_hours_detection():
    service = NotificationService(db=_make_db())
    disabled = NotificationPreference(user_id='t', quiet_hours_enabled=False)
    assert not service._is_quiet_hours(disabled)
    bad = NotificationPreference(user_id='t', quiet_hours_enabled=True, quiet_hours_start='x', quiet_hours_end='y')
    assert not service._is_quiet_hours(bad)


# ── Digest Tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_digest_mode_enqueues():
    prefs = NotificationPreference(user_id='u1', digest_enabled=True, digest_frequency='daily')
    db = _make_db(scalar_one_or_none_return=prefs)
    db.execute = AsyncMock(side_effect=[
        _make_mock_result(scalar_one_or_none_return=prefs),
        _make_mock_result(scalar_one_or_none_return=None),
    ])
    service = NotificationService(db=db)
    n = await service.send(
        user_id='u1', channel=NotificationChannel.IN_APP,
        category=NotificationCategory.GENERAL, title='Digest',
    )
    assert n.title == 'Digest'


@pytest.mark.asyncio
async def test_process_digests():
    digest = NotificationDigest(
        user_id='u1',
        period_start=datetime.now(UTC) - timedelta(hours=25),
        period_end=datetime.now(UTC) - timedelta(hours=1),
        notification_ids=['00000000-0000-0000-0000-000000000001'],
        total_count=1, channels=['email'],
    )
    notif = _make_notification(
        channel=NotificationChannel.EMAIL, category=NotificationCategory.GENERAL,
        priority=NotificationPriority.NORMAL, title='Digest item',
    )
    prefs = NotificationPreference(user_id='u1', email_address='test@example.com')
    db = _make_db()
    db.execute = AsyncMock(side_effect=[
        _make_mock_result(scalars_all_return=[digest]),
        _make_mock_result(scalars_all_return=[notif]),
        _make_mock_result(scalar_one_or_none_return=prefs),
    ])
    service = NotificationService(db=db)
    count = await service.process_digests()
    assert isinstance(count, int)


# ── Broadcast Tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_broadcast_to_users():
    service = NotificationService(db=_make_db())
    sent = []

    async def track(**kw):
        sent.append(kw.get('user_id'))
        return _make_notification()

    service.send = track
    r = await service.send_broadcast(
        channel=NotificationChannel.IN_APP, category=NotificationCategory.GENERAL,
        title='B', user_ids=['a', 'b', 'c'],
    )
    assert len(r) == 3
    assert set(sent) == {'a', 'b', 'c'}


@pytest.mark.asyncio
async def test_broadcast_with_org_ids():
    db = _make_db(scalars_all_return=[('u1',), ('u2',)], scalar_one_or_none_return=None)
    service = NotificationService(db=db)
    service.send = AsyncMock(return_value=_make_notification())
    r = await service.send_broadcast(
        channel=NotificationChannel.IN_APP, category=NotificationCategory.GENERAL,
        title='B', org_ids=['org-1'],
    )
    assert len(r) == 2


# ── Retry Tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retry_failed():
    failed = [
        _make_notification(
            id=UUID(f'00000000-0000-0000-0000-{i:012d}'),
            title=f'F{i}', status=NotificationStatus.FAILED,
            retry_count=0, max_retries=3, last_error='x',
        ) for i in range(3)
    ]
    db = _make_db(scalars_all_return=failed, scalar_one_or_none_return=None)
    service = NotificationService(db=db)
    c = await service.retry_failed(db=db)
    assert isinstance(c, int)


# ── Mark Read Tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mark_read():
    n = _make_notification(status=NotificationStatus.SENT)
    db = _make_db(scalar_one_or_none_return=n)
    service = NotificationService(db=db)
    ok = await service.mark_read(str(n.id), 'test-user')
    assert ok
    assert n.status == NotificationStatus.READ


@pytest.mark.asyncio
async def test_mark_read_not_found():
    db = _make_db(scalar_one_or_none_return=None)
    service = NotificationService(db=db)
    ok = await service.mark_read('x', 'u1')
    assert not ok


@pytest.mark.asyncio
async def test_mark_all_read():
    items = [_make_notification(id=UUID(f'00000000-0000-0000-0000-{i:012d}'), title=f'N{i}', status=NotificationStatus.SENT) for i in range(5)]
    db = _make_db(scalars_all_return=items)
    service = NotificationService(db=db)
    assert await service.mark_all_read('u1') == 5


# ── Cleanup Tests ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cleanup_expired():
    expired = [
        _make_notification(id=UUID(f'00000000-0000-0000-0000-{i:012d}'), title=f'E{i}', status=NotificationStatus.PENDING, expires_at=datetime.now(UTC) - timedelta(hours=1))
        for i in range(2)
    ]
    db = _make_db(scalars_all_return=expired)
    service = NotificationService(db=db)
    assert await service.cleanup_expired() == 2
    assert all(n.status == NotificationStatus.CANCELLED for n in expired)


# ── Webhook Endpoint Tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_webhook():
    service = NotificationService(db=_make_db())
    wh = await service.register_webhook(
        user_id='u1', name='Hook',
        url='https://hook.example.com',
        events=['e1', 'e2'], channel_type='slack',
    )
    assert wh.name == 'Hook'
    assert wh.url == 'https://hook.example.com'


@pytest.mark.asyncio
async def test_test_webhook_ok():
    service = NotificationService()
    service._http_client = AsyncMock()
    service._http_client.post = AsyncMock(return_value=MagicMock(status_code=200))
    assert await service.test_webhook('https://example.com/hook') is True


@pytest.mark.asyncio
async def test_test_webhook_fail():
    service = NotificationService()
    service._http_client = AsyncMock()
    service._http_client.post = AsyncMock(side_effect=Exception('fail'))
    assert await service.test_webhook('https://example.com/hook') is False


# ── Record Event Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_event():
    db = _make_db()
    service = NotificationService(db=db)
    n = _make_notification()
    await service._record_event(n, 'dispatch', NotificationChannel.EMAIL, NotificationStatus.SENT, '42.5', db)
    db.add.assert_called()


# ── Template Tests ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_default_templates():
    db = _make_db(scalar_one_or_none_return=None)
    await create_default_templates(db)
    assert db.add.call_count >= 1


# ── Channel Dispatchers (real) ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatch_email_no_address():
    service = NotificationService(db=_make_db())
    n = _make_notification(channel=NotificationChannel.EMAIL)
    with pytest.raises(Exception):
        await service._dispatch_email(n, NotificationPreference(user_id='t'))


@pytest.mark.asyncio
async def test_slack_dispatch_no_url():
    service = NotificationService(db=_make_db())
    n = _make_notification(channel=NotificationChannel.SLACK)
    prefs = NotificationPreference(user_id='t', slack_webhook_url=None)
    with pytest.raises(Exception):
        await service._dispatch_slack(n, prefs)


@pytest.mark.asyncio
async def test_discord_dispatch_no_url():
    service = NotificationService(db=_make_db())
    n = _make_notification(channel=NotificationChannel.DISCORD)
    prefs = NotificationPreference(user_id='t', discord_webhook_url=None)
    with pytest.raises(Exception):
        await service._dispatch_discord(n, prefs)


@pytest.mark.asyncio
async def test_teams_dispatch_no_url():
    service = NotificationService(db=_make_db())
    n = _make_notification(channel=NotificationChannel.TEAMS)
    with pytest.raises(Exception):
        await service._dispatch_teams(n, NotificationPreference(user_id='t'))


@pytest.mark.asyncio
async def test_dispatch_sms_no_phone():
    service = NotificationService(db=_make_db())
    n = _make_notification(channel=NotificationChannel.SMS)
    with pytest.raises(Exception):
        await service._dispatch_sms(n, NotificationPreference(user_id='t'))


@pytest.mark.asyncio
async def test_dispatch_push_no_token():
    service = NotificationService(db=_make_db())
    n = _make_notification(channel=NotificationChannel.PUSH)
    with pytest.raises(Exception):
        await service._dispatch_push(n, NotificationPreference(user_id='t'))


@pytest.mark.asyncio
async def test_dispatch_webhook_no_url():
    service = NotificationService(db=_make_db())
    n = _make_notification(channel=NotificationChannel.WEBHOOK)
    with pytest.raises(Exception):
        await service._dispatch_webhook(n, NotificationPreference(user_id='t'))


# ── Serialization ─────────────────────────────────────────────────────────────


def test_notification_attrs():
    n = _make_notification(
        channel=NotificationChannel.EMAIL, category=NotificationCategory.SECURITY,
        priority=NotificationPriority.HIGH, status=NotificationStatus.SENT,
        title='Alert', body='Detail', source='svc', correlation_id='c1',
    )
    assert n.channel.value == 'email'
    assert n.category.value == 'security'
    assert n.priority.value == 'high'
    assert n.status.value == 'sent'
    assert n.title == 'Alert'
    assert n.body == 'Detail'


def test_preference_defaults():
    p = NotificationPreference(user_id='test')
    assert p.user_id == 'test'


def test_webhook_endpoint_defaults():
    wh = WebhookEndpoint(name='Test', url='https://ex.com')
    assert wh.name == 'Test'
    assert wh.url == 'https://ex.com'


# ── Dispatch with HTTP Client ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_slack_dispatch_with_url():
    prefs = NotificationPreference(user_id='t', slack_webhook_url='https://hooks.slack.com/t')
    service = NotificationService(db=_make_db())
    service._http_client = AsyncMock()
    service._http_client.post = AsyncMock(return_value=MagicMock(status_code=200))
    n = _make_notification(channel=NotificationChannel.SLACK, category=NotificationCategory.DEPLOYMENT, priority=NotificationPriority.CRITICAL, title='Fail', body='Deploy failed.')
    await service._dispatch_slack(n, prefs)
    service._http_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_discord_dispatch_with_url():
    prefs = NotificationPreference(user_id='t', discord_webhook_url='https://discord.com/api/webhooks/t')
    service = NotificationService(db=_make_db())
    service._http_client = AsyncMock()
    service._http_client.post = AsyncMock(return_value=MagicMock(status_code=200))
    n = _make_notification(channel=NotificationChannel.DISCORD, category=NotificationCategory.INCIDENT, priority=NotificationPriority.HIGH, title='Incident', body='Critical.')
    await service._dispatch_discord(n, prefs)
    service._http_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_teams_dispatch_with_url():
    prefs = NotificationPreference(user_id='t', teams_webhook_url='https://outlook.office.com/webhook/t')
    service = NotificationService(db=_make_db())
    service._http_client = AsyncMock()
    service._http_client.post = AsyncMock(return_value=MagicMock(status_code=200))
    n = _make_notification(channel=NotificationChannel.TEAMS, category=NotificationCategory.DEPLOYMENT, title='Deploy', body='Done.', priority=NotificationPriority.NORMAL)
    await service._dispatch_teams(n, prefs)
    service._http_client.post.assert_called_once()


# ── Category-specific Alerts ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_system_health_alert():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    n = await service.send(
        user_id='u1', channel=NotificationChannel.EMAIL,
        category=NotificationCategory.SYSTEM_HEALTH,
        title='DB pool exhausted',
        priority=NotificationPriority.HIGH, source='monitor',
    )
    assert n.category == NotificationCategory.SYSTEM_HEALTH


@pytest.mark.asyncio
async def test_security_alert():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    n = await service.send(
        user_id='u1', channel=NotificationChannel.EMAIL,
        category=NotificationCategory.SECURITY,
        title='Unauthorized access',
        priority=NotificationPriority.CRITICAL, source='auth',
    )
    assert n.category == NotificationCategory.SECURITY


@pytest.mark.asyncio
async def test_billing_alert():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    n = await service.send(
        user_id='u1', channel=NotificationChannel.EMAIL,
        category=NotificationCategory.BILLING,
        title='Usage report',
        priority=NotificationPriority.NORMAL, source='billing',
    )
    assert n.category == NotificationCategory.BILLING


@pytest.mark.asyncio
async def test_update_alert():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    n = await service.send(
        user_id='u1', channel=NotificationChannel.IN_APP,
        category=NotificationCategory.UPDATE,
        title='New version', source='updater',
    )
    assert n.category == NotificationCategory.UPDATE


@pytest.mark.asyncio
async def test_sos_alert():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    n = await service.send(
        user_id='u1', channel=NotificationChannel.SMS,
        category=NotificationCategory.SOS,
        title='SOS: Help needed',
        priority=NotificationPriority.CRITICAL, source='sos',
        correlation_id='sos-001',
    )
    assert n.category == NotificationCategory.SOS


@pytest.mark.asyncio
async def test_maintenance_alert():
    service = NotificationService(db=_make_db(scalar_one_or_none_return=None))
    n = await service.send(
        user_id='u1', channel=NotificationChannel.EMAIL,
        category=NotificationCategory.MAINTENANCE,
        title='Scheduled maintenance',
        priority=NotificationPriority.LOW, source='ops',
    )
    assert n.category == NotificationCategory.MAINTENANCE
