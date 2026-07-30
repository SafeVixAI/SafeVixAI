# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Notification API routes — CRUD, preferences, WebSocket, and admin endpoints."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.notification_ws import notification_manager
from core.rbac import require_role
from models.notification import (
    Notification,
    NotificationCategory,
    NotificationChannel,
    NotificationDigest,
    NotificationPreference,
    NotificationPriority,
    NotificationStatus,
    WebhookEndpoint,
)
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/notifications', tags=['notifications'])


def _get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db=db)


# ── Notification CRUD ──────────────────────────────────────────────────────────


@router.get('')
async def list_notifications(
    user_id: str = Query(...),
    status: str | None = Query(None),
    category: str | None = Query(None),
    channel: str | None = Query(None),
    priority: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(Notification.user_id == user_id)
    if status:
        stmt = stmt.where(Notification.status == NotificationStatus(status))
    if category:
        stmt = stmt.where(Notification.category == NotificationCategory(category))
    if channel:
        stmt = stmt.where(Notification.channel == NotificationChannel(channel))
    if priority:
        stmt = stmt.where(Notification.priority == NotificationPriority(priority))
    stmt = stmt.order_by(desc(Notification.created_at)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    notifications = result.scalars().all()

    count_stmt = select(func.count(Notification.id)).where(Notification.user_id == user_id)
    if status:
        count_stmt = count_stmt.where(Notification.status == NotificationStatus(status))
    if category:
        count_stmt = count_stmt.where(Notification.category == NotificationCategory(category))
    total = (await db.execute(count_stmt)).scalar()

    unread_stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED]),
    )
    unread = (await db.execute(unread_stmt)).scalar()

    return {
        'notifications': [_serialize(n) for n in notifications],
        'total': total or 0,
        'unread': unread or 0,
        'limit': limit,
        'offset': offset,
    }


@router.get('/{notification_id}')
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail='Notification not found')
    return _serialize(notification)


@router.post('/{notification_id}/read')
async def mark_notification_read(
    notification_id: UUID,
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db=db)
    success = await service.mark_read(str(notification_id), user_id)
    if not success:
        raise HTTPException(status_code=404, detail='Notification not found')
    return {'status': 'ok'}


@router.post('/read-all')
async def mark_all_read(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db=db)
    count = await service.mark_all_read(user_id)
    return {'status': 'ok', 'count': count}


@router.delete('/{notification_id}')
async def delete_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = delete(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail='Notification not found')
    return {'status': 'deleted'}


# ── Send ───────────────────────────────────────────────────────────────────────


@router.post('/send')
async def send_notification(
    user_id: str = Query(...),
    channel: str = Query(...),
    category: str = Query('general'),
    title: str = Query(...),
    body: str | None = Query(None),
    priority: str = Query('normal'),
    source: str | None = Query(None),
    correlation_id: str | None = Query(None),
    scheduled_for: str | None = Query(None),
    expires_at: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        ch = NotificationChannel(channel)
        cat = NotificationCategory(category)
        pri = NotificationPriority(priority)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    scheduled_dt = datetime.fromisoformat(scheduled_for) if scheduled_for else None
    expires_dt = datetime.fromisoformat(expires_at) if expires_at else None

    service = NotificationService(db=db)
    notification = await service.send(
        user_id=user_id,
        channel=ch,
        category=cat,
        title=title,
        body=body,
        priority=pri,
        source=source,
        correlation_id=correlation_id,
        scheduled_for=scheduled_dt,
        expires_at=expires_dt,
    )
    await db.commit()

    if notification.status == NotificationStatus.SENT:
        await notification_manager.send_notification(user_id, notification)

    return _serialize(notification)


# ── Preferences ────────────────────────────────────────────────────────────────


@router.get('/preferences')
async def get_preferences(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    result = await db.execute(stmt)
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)
        await db.flush()
    return _serialize_prefs(prefs)


@router.put('/preferences')
async def update_preferences(
    user_id: str = Query(...),
    payload: dict[str, Any] = ...,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    result = await db.execute(stmt)
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)
        await db.flush()

    for key in ('channels_enabled', 'categories_enabled', 'digest_enabled', 'digest_frequency',
                'dnd_enabled', 'dnd_start_hour', 'dnd_end_hour', 'dnd_timezone',
                'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
                'push_token', 'push_token_type', 'slack_webhook_url', 'discord_webhook_url',
                'teams_webhook_url', 'webhook_url', 'email_address', 'phone_number',
                'locale', 'max_daily_notifications'):
        if key in payload:
            setattr(prefs, key, payload[key])
    prefs.updated_at = datetime.now(UTC)
    await db.commit()
    return _serialize_prefs(prefs)


# ── Webhook Endpoints ──────────────────────────────────────────────────────────


@router.get('/webhooks')
async def list_webhooks(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WebhookEndpoint).where(WebhookEndpoint.user_id == user_id)
    result = await db.execute(stmt)
    webhooks = result.scalars().all()
    return {'webhooks': [_serialize_webhook(w) for w in webhooks]}


@router.post('/webhooks')
async def create_webhook(
    user_id: str = Query(...),
    payload: dict[str, Any] = ...,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db=db)
    wh = await service.register_webhook(
        user_id=user_id,
        name=payload.get('name', 'Webhook'),
        url=payload.get('url', ''),
        events=payload.get('events'),
        channel_type=payload.get('channel_type', 'webhook'),
        secret=payload.get('secret'),
    )
    await db.commit()
    return _serialize_webhook(wh)


@router.delete('/webhooks/{webhook_id}')
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = delete(WebhookEndpoint).where(WebhookEndpoint.id == webhook_id)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail='Webhook not found')
    return {'status': 'deleted'}


@router.post('/webhooks/test')
async def test_webhook(
    url: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db=db)
    success = await service.test_webhook(url)
    return {'success': success}


# ── Digest ─────────────────────────────────────────────────────────────────────


@router.get('/digests')
async def list_digests(
    user_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NotificationDigest).where(
        NotificationDigest.user_id == user_id,
    ).order_by(desc(NotificationDigest.period_start)).limit(limit)
    result = await db.execute(stmt)
    digests = result.scalars().all()
    return {'digests': [_serialize_digest(d) for d in digests]}


# ── Stats ──────────────────────────────────────────────────────────────────────


@router.get('/stats')
async def notification_stats(
    user_id: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0) - __import__('datetime').timedelta(days=days)  # noqa: E501

    total_stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id, Notification.created_at >= since
    )
    total = (await db.execute(total_stmt)).scalar() or 0

    by_category = select(
        Notification.category, func.count(Notification.id)
    ).where(
        Notification.user_id == user_id, Notification.created_at >= since
    ).group_by(Notification.category)
    cat_result = await db.execute(by_category)

    by_channel = select(
        Notification.channel, func.count(Notification.id)
    ).where(
        Notification.user_id == user_id, Notification.created_at >= since
    ).group_by(Notification.channel)
    ch_result = await db.execute(by_channel)

    return {
        'total': total,
        'days': days,
        'by_category': {str(r[0].value if hasattr(r[0], 'value') else r[0]): r[1] for r in cat_result},
        'by_channel': {str(r[0].value if hasattr(r[0], 'value') else r[0]): r[1] for r in ch_result},
    }


# ── Admin ──────────────────────────────────────────────────────────────────────


@router.get('/admin/retry')
async def admin_retry_failed(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role('admin')),
):
    service = NotificationService(db=db)
    count = await service.retry_failed(db=db)
    return {'retried': count}


@router.post('/admin/process-digests')
async def admin_process_digests(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role('admin')),
):
    service = NotificationService(db=db)
    count = await service.process_digests(db=db)
    return {'digests_processed': count}


@router.post('/admin/cleanup')
async def admin_cleanup(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role('admin')),
):
    service = NotificationService(db=db)
    count = await service.cleanup_expired(db=db)
    return {'expired_cleaned': count}


# ── Analytics ──────────────────────────────────────────────────────────────────


@router.post('/{notification_id}/open')
async def track_notification_open(
    notification_id: UUID,
    user_id: str = Query(...),
    user_agent: str | None = Query(None),
    ip_address: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db=db)
    await service.track_open(str(notification_id), user_id, user_agent, ip_address)
    await db.commit()
    return {'status': 'ok'}


@router.post('/{notification_id}/click')
async def track_notification_click(
    notification_id: UUID,
    user_id: str = Query(...),
    utm_source: str | None = Query(None),
    utm_medium: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db=db)
    await service.track_click(str(notification_id), user_id, utm_source, utm_medium)
    await db.commit()
    return {'status': 'ok'}


# ── Offline Queue ──────────────────────────────────────────────────────────────


@router.post('/offline/enqueue')
async def enqueue_offline(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db=db)
    n = await service.enqueue_offline(
        user_id=payload.get('user_id', ''),
        notification_data=payload.get('notification', {}),
    )
    await db.commit()
    return {'id': str(n.id), 'status': 'queued'}


@router.post('/offline/process')
async def process_offline_queue(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db=db)
    count = await service.process_offline_queue(user_id)
    await db.commit()
    return {'processed': count}


# ── WebSocket ──────────────────────────────────────────────────────────────────


@router.websocket('/ws')
async def notification_websocket(websocket: WebSocket):
    user_id = websocket.query_params.get('user_id', 'anonymous')
    await notification_manager.handle_websocket(websocket, user_id)


# ── Serializers ────────────────────────────────────────────────────────────────


def _serialize(n: Notification) -> dict[str, Any]:
    return {
        'id': str(n.id),
        'user_id': n.user_id,
        'org_id': n.org_id,
        'channel': n.channel.value if n.channel else None,
        'category': n.category.value if n.category else None,
        'priority': n.priority.value if n.priority else 'normal',
        'status': n.status.value if n.status else None,
        'title': n.title,
        'body': n.body,
        'metadata': n.payload,
        'source': n.source,
        'correlation_id': n.correlation_id,
        'read_at': n.read_at.isoformat() if n.read_at else None,
        'delivered_at': n.delivered_at.isoformat() if n.delivered_at else None,
        'scheduled_for': n.scheduled_for.isoformat() if n.scheduled_for else None,
        'expires_at': n.expires_at.isoformat() if n.expires_at else None,
        'created_at': n.created_at.isoformat() if n.created_at else None,
        'updated_at': n.updated_at.isoformat() if n.updated_at else None,
    }


def _serialize_prefs(p: NotificationPreference) -> dict[str, Any]:
    return {
        'id': str(p.id),
        'user_id': p.user_id,
        'org_id': p.org_id,
        'channels_enabled': p.channels_enabled,
        'categories_enabled': p.categories_enabled,
        'digest_enabled': p.digest_enabled,
        'digest_frequency': p.digest_frequency,
        'dnd_enabled': p.dnd_enabled,
        'dnd_start_hour': p.dnd_start_hour,
        'dnd_end_hour': p.dnd_end_hour,
        'dnd_timezone': p.dnd_timezone,
        'quiet_hours_enabled': p.quiet_hours_enabled,
        'quiet_hours_start': p.quiet_hours_start,
        'quiet_hours_end': p.quiet_hours_end,
        'push_token': bool(p.push_token),
        'slack_webhook_url': bool(p.slack_webhook_url),
        'discord_webhook_url': bool(p.discord_webhook_url),
        'teams_webhook_url': bool(p.teams_webhook_url),
        'webhook_url': bool(p.webhook_url),
        'email_address': p.email_address,
        'phone_number': p.phone_number,
        'locale': p.locale,
        'max_daily_notifications': p.max_daily_notifications,
        'created_at': p.created_at.isoformat() if p.created_at else None,
        'updated_at': p.updated_at.isoformat() if p.updated_at else None,
    }


def _serialize_webhook(w: WebhookEndpoint) -> dict[str, Any]:
    return {
        'id': str(w.id),
        'user_id': w.user_id,
        'org_id': w.org_id,
        'name': w.name,
        'url': w.url,
        'events': w.events,
        'channel_type': w.channel_type,
        'is_active': w.is_active,
        'last_sent_at': w.last_sent_at.isoformat() if w.last_sent_at else None,
        'last_status': w.last_status,
        'failure_count': w.failure_count,
        'created_at': w.created_at.isoformat() if w.created_at else None,
    }


def _serialize_digest(d: NotificationDigest) -> dict[str, Any]:
    return {
        'id': str(d.id),
        'user_id': d.user_id,
        'period_start': d.period_start.isoformat() if d.period_start else None,
        'period_end': d.period_end.isoformat() if d.period_end else None,
        'total_count': d.total_count,
        'channels': d.channels,
        'sent_at': d.sent_at.isoformat() if d.sent_at else None,
        'created_at': d.created_at.isoformat() if d.created_at else None,
    }
