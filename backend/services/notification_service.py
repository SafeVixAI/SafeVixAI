# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Enterprise notification service with multi-channel delivery, retry, digest, and DND support."""

from __future__ import annotations

import logging
import os
import smtplib
import string
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from typing import Any

import httpx
from prometheus_client import Counter, Histogram
from sqlalchemy import Boolean as SABoolean
from sqlalchemy import cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
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

logger = logging.getLogger(__name__)


class NotificationSendError(Exception):
    pass


class DNDActiveError(NotificationSendError):
    pass


PRIORITY_LEVEL = {
    NotificationPriority.LOW: 0,
    NotificationPriority.NORMAL: 1,
    NotificationPriority.HIGH: 2,
    NotificationPriority.CRITICAL: 3,
}

# Prometheus metrics
notification_sent_total = Counter('notification_sent_total', 'Total notifications sent', ['channel', 'category', 'status'])
notification_delivery_seconds = Histogram('notification_delivery_seconds', 'Notification delivery latency', ['channel'], buckets=[0.01, 0.05, 0.1, 0.5, 1, 2.5, 5, 10, 30])
notification_failed_total = Counter('notification_failed_total', 'Total failed notifications', ['channel', 'error_type'])
notification_queue_depth = Counter('notification_queue_depth', 'Current notification queue depth')
notification_retry_total = Counter('notification_retry_total', 'Total retry attempts', ['status'])

# Locale support
LOCALE_TEMPLATES: dict[str, dict[str, str]] = {
    'en': {
        'dnd_queued': 'Queued during Do Not Disturb hours',
        'quiet_hours_queued': 'Queued during quiet hours',
        'digest_title': 'Digest: {count} notifications',
        'digest_body': 'You have {count} pending notifications',
        'expired': 'Notification expired',
        'channel_disabled': 'Channel disabled in preferences',
        'category_disabled': 'Category disabled in preferences',
        'digest_period': 'Period: {start} — {end}',
    },
    'hi': {
        'dnd_queued': 'डू नॉट डिस्टर्ब घंटों के दौरान कतारबद्ध',
        'quiet_hours_queued': 'शांत घंटों के दौरान कतारबद्ध',
        'digest_title': 'डाइजेस्ट: {count} सूचनाएं',
        'digest_body': 'आपके पास {count} लंबित सूचनाएं हैं',
        'expired': 'सूचना समाप्त हो गई',
        'channel_disabled': 'प्राथमिकताओं में चैनल अक्षम',
        'category_disabled': 'प्राथमिकताओं में श्रेणी अक्षम',
        'digest_period': 'अवधि: {start} — {end}',
    },
    'ta': {
        'dnd_queued': 'தயவுசெய்து தொந்தரவு செய்யாத நேரங்களில் வரிசையில் வைக்கப்பட்டது',
        'quiet_hours_queued': 'அமைதியான நேரங்களில் வரிசையில் வைக்கப்பட்டது',
        'digest_title': 'சுருக்கம்: {count} அறிவிப்புகள்',
        'digest_body': 'உங்களிடம் {count} நிலுவையில் உள்ள அறிவிப்புகள் உள்ளன',
        'expired': 'அறிவிப்பு காலாவதியானது',
        'channel_disabled': 'விருப்பங்களில் சேனல் முடக்கப்பட்டது',
        'category_disabled': 'விருப்பங்களில் வகை முடக்கப்பட்டது',
        'digest_period': 'காலம்: {start} — {end}',
    },
}


class NotificationService:
    """Central notification service dispatching to all channels."""

    def __init__(self, db: AsyncSession | None = None, redis_client=None):
        self._db = db
        self._redis = redis_client
        self._settings = get_settings()
        self._http_client: httpx.AsyncClient | None = None
        self._template_cache: dict[str, str] = {}

    async def get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=15.0)
        return self._http_client

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    # ── Send ──────────────────────────────────────────────────────────────────

    async def send(
        self,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        channel: NotificationChannel,
        category: NotificationCategory,
        title: str,
        body: str | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
        source: str | None = None,
        correlation_id: str | None = None,
        scheduled_for: datetime | None = None,
        expires_at: datetime | None = None,
        template_name: str | None = None,
        template_vars: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> Notification:
        session = db or self._db

        if template_name:
            resolved = await self._resolve_template(template_name, channel, category, template_vars or {})
            title = resolved.get('title', title)
            body = resolved.get('body', body)

        notification = Notification(
            user_id=user_id,
            org_id=org_id,
            channel=channel,
            category=category,
            payload=metadata,
            priority=priority,
            title=title,
            body=body,
            metadata=metadata,
            source=source,
            correlation_id=correlation_id,
            scheduled_for=scheduled_for,
            expires_at=expires_at,
            status=NotificationStatus.PENDING,
        )
        session.add(notification)
        await session.flush()

        if scheduled_for and scheduled_for > datetime.now(UTC):
            return notification

        prefs = await self._load_preferences(user_id, session)
        if prefs and not self._is_channel_allowed(prefs, channel):
            notification.status = NotificationStatus.CANCELLED
            notification.last_error = 'Channel disabled in preferences'
            await session.flush()
            return notification
        if prefs and not self._is_category_allowed(prefs, category):
            notification.status = NotificationStatus.CANCELLED
            notification.last_error = 'Category disabled in preferences'
            await session.flush()
            return notification
        if prefs and self._is_dnd_active(prefs):
            if PRIORITY_LEVEL[priority] < PRIORITY_LEVEL[NotificationPriority.CRITICAL]:
                notification.status = NotificationStatus.PENDING
                notification.payload = dict(notification.payload or {})
                notification.payload['dnd_queued'] = True
                await session.flush()
                return notification

        if prefs and self._is_quiet_hours(prefs):
            if PRIORITY_LEVEL[priority] < PRIORITY_LEVEL[NotificationPriority.HIGH]:
                notification.status = NotificationStatus.PENDING
                notification.payload = dict(notification.payload or {})
                notification.payload['quiet_hours_queued'] = True
                await session.flush()
                return notification

        if prefs and prefs.digest_enabled and PRIORITY_LEVEL[priority] < PRIORITY_LEVEL[NotificationPriority.HIGH]:
            await self._enqueue_for_digest(notification, prefs, session)
            return notification

        await self._dispatch(notification, prefs, session)
        await session.flush()
        return notification

    async def send_broadcast(
        self,
        *,
        channel: NotificationChannel,
        category: NotificationCategory,
        title: str,
        body: str | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
        source: str | None = None,
        correlation_id: str | None = None,
        user_ids: list[str] | None = None,
        org_ids: list[str] | None = None,
        db: AsyncSession | None = None,
    ) -> list[Notification]:
        session = db or self._db
        results: list[Notification] = []
        targets: list[str] = []

        if org_ids:
            stmt = select(NotificationPreference.user_id).where(
                NotificationPreference.org_id.in_(org_ids),
                cast(NotificationPreference.categories_enabled[category.value], SABoolean).is_(True),
            )
            rows = await session.execute(stmt)
            targets.extend(row[0] for row in rows if row[0])

        if user_ids:
            targets.extend(user_ids)

        for uid in set(targets):
            n = await self.send(
                user_id=uid,
                channel=channel,
                category=category,
                title=title,
                body=body,
                priority=priority,
                metadata=metadata,
                source=source,
                correlation_id=correlation_id,
                db=session,
            )
            results.append(n)
        return results

    # ── Dispatch ──────────────────────────────────────────────────────────────

    async def _dispatch(
        self,
        notification: Notification,
        prefs: NotificationPreference | None,
        session: AsyncSession,
    ) -> None:
        channel = notification.channel
        dispatchers = {
            NotificationChannel.IN_APP: self._dispatch_in_app,
            NotificationChannel.DESKTOP: self._dispatch_desktop,
            NotificationChannel.EMAIL: self._dispatch_email,
            NotificationChannel.SMS: self._dispatch_sms,
            NotificationChannel.PUSH: self._dispatch_push,
            NotificationChannel.SLACK: self._dispatch_slack,
            NotificationChannel.DISCORD: self._dispatch_discord,
            NotificationChannel.TEAMS: self._dispatch_teams,
            NotificationChannel.WEBHOOK: self._dispatch_webhook,
        }
        dispatcher = dispatchers.get(channel)
        if not dispatcher:
            notification.status = NotificationStatus.FAILED
            notification.last_error = f'Unknown channel: {channel}'
            return

        start = datetime.now(UTC)
        try:
            await dispatcher(notification, prefs)
            notification.status = NotificationStatus.SENT
            notification.delivered_at = datetime.now(UTC)
            notification_sent_total.labels(channel=channel.value, category=notification.category.value, status='sent').inc()
            notification_delivery_seconds.labels(channel=channel.value).observe(
                (datetime.now(UTC) - start).total_seconds()
            )
        except DNDActiveError:
            notification.status = NotificationStatus.PENDING
            notification.payload = dict(notification.payload or {})
            notification.payload['dnd_queued'] = True
            notification_sent_total.labels(channel=channel.value, category=notification.category.value, status='dnd_queued').inc()
        except Exception as exc:
            notification.status = NotificationStatus.FAILED
            notification.last_error = str(exc)
            notification_failed_total.labels(channel=channel.value, error_type=type(exc).__name__).inc()
            logger.warning('Notification %s failed on %s: %s', notification.id, channel.value, exc)
        finally:
            elapsed = (datetime.now(UTC) - start).total_seconds() * 1000
            await self._record_event(notification, 'dispatch', channel, notification.status, str(elapsed) if isinstance(elapsed, (int, float)) else None, session)

    def _localize(self, key: str, locale: str = 'en', **kwargs: Any) -> str:
        """Resolve a localized string from the locale templates."""
        templates = LOCALE_TEMPLATES.get(locale, LOCALE_TEMPLATES['en'])
        tmpl = templates.get(key, key)
        try:
            return string.Template(tmpl).safe_substitute(**kwargs)
        except Exception:
            return tmpl

    async def _dispatch_in_app(
        self, notification: Notification, prefs: NotificationPreference | None
    ) -> None:
        pass

    async def _dispatch_desktop(
        self, notification: Notification, prefs: NotificationPreference | None
    ) -> None:
        """Dispatch a desktop notification via WebSocket (Service Worker sends Browser Notification)."""
        # Desktop notifications are delivered via the WebSocket — the client-side
        # Service Worker receives the WS message and fires a Browser Notification.
        # No blocking call needed here; the WS manager already broadcasts to connected clients.
        # If the user is offline, the offline queue handles it.

    async def _dispatch_email(
        self, notification: Notification, prefs: NotificationPreference | None
    ) -> None:
        to = prefs.email_address if prefs else None
        if prefs and not to:
            to = notification.payload.get('email') if notification.payload else None
        if not to:
            raise NotificationSendError('No email address configured')
        subject = notification.title
        body = notification.body or ''
        try:
            await self._send_smtp(to, subject, body)
        except Exception as exc:
            raise NotificationSendError(f'SMTP failed: {exc}') from exc

    async def _dispatch_sms(
        self, notification: Notification, prefs: NotificationPreference | None
    ) -> None:
        phone = prefs.phone_number if prefs else None
        if not phone:
            raise NotificationSendError('No phone number configured')
        body = notification.body or notification.title
        await self._send_sms_via_provider(phone, body)

    async def _dispatch_push(
        self, notification: Notification, prefs: NotificationPreference | None
    ) -> None:
        token = prefs.push_token if prefs else None
        if not token:
            raise NotificationSendError('No push token configured')
        await self._send_push_notification(token, notification.title, notification.body or '', notification.payload)

    async def _dispatch_slack(
        self, notification: Notification, prefs: NotificationPreference | None
    ) -> None:
        url = prefs.slack_webhook_url if prefs else self._settings.slack_webhook_url
        if not url:
            raise NotificationSendError('No Slack webhook URL')
        color_map = {
            NotificationPriority.CRITICAL: 'danger',
            NotificationPriority.HIGH: 'warning',
            NotificationPriority.NORMAL: 'good',
            NotificationPriority.LOW: '#808080',
        }
        blocks = [
            {
                'type': 'header',
                'text': {'type': 'plain_text', 'text': notification.title[:150]},
            },
        ]
        if notification.body:
            blocks.append({
                'type': 'section',
                'text': {'type': 'mrkdwn', 'text': notification.body[:3000]},
            })
        blocks.append({
            'type': 'context',
            'elements': [
                {'type': 'mrkdwn', 'text': f'*Category:* {notification.category.value} | *Priority:* {notification.priority.value}'},
            ],
        })
        payload = {
            'text': notification.title,
            'blocks': blocks,
            'attachments': [{'color': color_map.get(notification.priority, '#808080')}],
        }
        client = await self.get_http_client()
        resp = await client.post(url, json=payload)
        if resp.status_code >= 300:
            raise NotificationSendError(f'Slack returned {resp.status_code}: {resp.text[:200]}')

    async def _dispatch_discord(
        self, notification: Notification, prefs: NotificationPreference | None
    ) -> None:
        url = prefs.discord_webhook_url if prefs else self._settings.discord_webhook_url
        if not url:
            raise NotificationSendError('No Discord webhook URL')
        color_map = {
            NotificationPriority.CRITICAL: 0xDC143C,
            NotificationPriority.HIGH: 0xFF4500,
            NotificationPriority.NORMAL: 0x5865F2,
            NotificationPriority.LOW: 0x808080,
        }
        embed = {
            'title': notification.title[:256],
            'color': color_map.get(notification.priority, 0x808080),
            'fields': [
                {'name': 'Category', 'value': notification.category.value, 'inline': True},
                {'name': 'Priority', 'value': notification.priority.value, 'inline': True},
            ],
            'footer': {'text': 'SafeVixAI Notification System'},
            'timestamp': datetime.now(UTC).isoformat(),
        }
        if notification.body:
            embed['description'] = notification.body[:2048]
        payload = {'embeds': [embed]}
        client = await self.get_http_client()
        resp = await client.post(url, json=payload)
        if resp.status_code >= 300:
            raise NotificationSendError(f'Discord returned {resp.status_code}: {resp.text[:200]}')

    async def _dispatch_teams(
        self, notification: Notification, prefs: NotificationPreference | None
    ) -> None:
        url = prefs.teams_webhook_url if prefs else None
        if not url:
            raise NotificationSendError('No Teams webhook URL')
        theme_colors = {
            NotificationPriority.CRITICAL: 'FF0000',
            NotificationPriority.HIGH: 'FF8C00',
            NotificationPriority.NORMAL: '0078D4',
            NotificationPriority.LOW: '808080',
        }
        sections = [
            {
                'activityTitle': notification.title,
                'activitySubtitle': f'{notification.category.value} — {notification.priority.value}',
                'text': notification.body or '',
                'markdown': True,
            }
        ]
        payload = {
            '@type': 'MessageCard',
            '@context': 'http://schema.org/extensions',
            'themeColor': theme_colors.get(notification.priority, '0078D4'),
            'summary': notification.title,
            'title': notification.title,
            'sections': sections,
        }
        client = await self.get_http_client()
        resp = await client.post(url, json=payload)
        if resp.status_code >= 300:
            raise NotificationSendError(f'Teams returned {resp.status_code}: {resp.text[:200]}')

    async def _dispatch_webhook(
        self, notification: Notification, prefs: NotificationPreference | None
    ) -> None:
        url = prefs.webhook_url if prefs else None
        if not url:
            raise NotificationSendError('No webhook URL configured')
        payload = {
            'event': 'notification',
            'id': str(notification.id),
            'channel': notification.channel.value,
            'category': notification.category.value,
            'priority': notification.priority.value,
            'title': notification.title,
            'body': notification.body,
            'metadata': notification.payload,
            'source': notification.source,
            'correlation_id': notification.correlation_id,
            'timestamp': datetime.now(UTC).isoformat(),
        }
        client = await self.get_http_client()
        resp = await client.post(url, json=payload)
        if resp.status_code >= 300:
            raise NotificationSendError(f'Webhook returned {resp.status_code}: {resp.text[:200]}')

    # ── Channel Implementations ───────────────────────────────────────────────

    async def _send_smtp(self, to: str, subject: str, body: str) -> None:
        settings = self._settings
        smtp_host = getattr(settings, 'smtp_host', os.getenv('SMTP_HOST', 'smtp.gmail.com'))
        smtp_port = getattr(settings, 'smtp_port', int(os.getenv('SMTP_PORT', '587')))
        smtp_user = getattr(settings, 'smtp_user', os.getenv('SMTP_USER', ''))
        smtp_password = getattr(settings, 'smtp_password', os.getenv('SMTP_PASSWORD', ''))

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = smtp_user or 'noreply@safevixai.gov.in'
        msg['To'] = to
        msg.set_content(body)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

    async def _send_sms_via_provider(self, phone: str, message: str) -> None:
        logger.info('SMS sending to %s: %s', phone[:5] + '***', message[:60])

    async def _send_push_notification(
        self, token: str, title: str, body: str, metadata: dict[str, Any] | None
    ) -> None:
        logger.info('Push notification to token %s: %s', token[:8] + '***', title)

    # ── Preferences ───────────────────────────────────────────────────────────

    async def _load_preferences(
        self, user_id: str | None, session: AsyncSession
    ) -> NotificationPreference | None:
        if not user_id:
            return None
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def _is_channel_allowed(self, prefs: NotificationPreference, channel: NotificationChannel) -> bool:
        channels = prefs.channels_enabled or {}
        return channels.get(channel.value, True)

    def _is_category_allowed(self, prefs: NotificationPreference, category: NotificationCategory) -> bool:
        cats = prefs.categories_enabled or {}
        return cats.get(category.value, True)

    def _is_dnd_active(self, prefs: NotificationPreference) -> bool:
        if not prefs.dnd_enabled:
            return False
        now = datetime.now(UTC)
        if prefs.dnd_start_hour is not None and prefs.dnd_end_hour is not None:
            hour = now.hour
            if prefs.dnd_start_hour <= prefs.dnd_end_hour:
                return prefs.dnd_start_hour <= hour < prefs.dnd_end_hour
            else:
                return hour >= prefs.dnd_start_hour or hour < prefs.dnd_end_hour
        return False

    def _is_quiet_hours(self, prefs: NotificationPreference) -> bool:
        if not prefs.quiet_hours_enabled or not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False
        try:
            start_h, start_m = map(int, prefs.quiet_hours_start.split(':'))
            end_h, end_m = map(int, prefs.quiet_hours_end.split(':'))
            now = datetime.now(UTC)
            current_minutes = now.hour * 60 + now.minute
            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            if start_minutes <= end_minutes:
                return start_minutes <= current_minutes < end_minutes
            return current_minutes >= start_minutes or current_minutes < end_minutes
        except (ValueError, TypeError):
            return False

    async def _enqueue_for_digest(
        self,
        notification: Notification,
        prefs: NotificationPreference,
        session: AsyncSession,
    ) -> None:
        now = datetime.now(UTC)
        freq = prefs.digest_frequency
        if freq == 'hourly':
            period_start = now.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)
        elif freq == 'daily':
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif freq == 'weekly':
            period_start = now - timedelta(days=now.weekday())
            period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=7)
        else:
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)

        stmt = select(NotificationDigest).where(
            NotificationDigest.user_id == prefs.user_id,
            NotificationDigest.period_start == period_start,
            NotificationDigest.period_end == period_end,
            NotificationDigest.sent_at.is_(None),
        )
        digest = (await session.execute(stmt)).scalar_one_or_none()
        if digest:
            nids = list(digest.notification_ids or [])
            nids.append(str(notification.id))
            digest.notification_ids = nids
            digest.total_count = len(nids)
        else:
            digest = NotificationDigest(
                user_id=prefs.user_id,
                org_id=prefs.org_id,
                period_start=period_start,
                period_end=period_end,
                notification_ids=[str(notification.id)],
                total_count=1,
                channels=NotificationChannel.list() if hasattr(NotificationChannel, 'list') else [],
            )
            session.add(digest)

    # ── Templates ─────────────────────────────────────────────────────────────

    async def _resolve_template(
        self,
        name: str,
        channel: NotificationChannel,
        category: NotificationCategory,
        vars: dict[str, Any],
    ) -> dict[str, str]:
        cache_key = f'{name}:{channel.value}:{category.value}'
        if cache_key in self._template_cache:
            tmpl = self._template_cache[cache_key]
        else:
            tmpl = None

        if tmpl is None:
            stmt = select(NotificationTemplate).where(
                NotificationTemplate.name == name,
                NotificationTemplate.channel == channel,
                NotificationTemplate.category == category,
            )
            async with get_db() as session:
                result = await session.execute(stmt)
                template = result.scalar_one_or_none()
                if template:
                    self._template_cache[cache_key] = template
                    tmpl = template

        if not tmpl:
            return {}

        def _render(text: str | None) -> str:
            if not text:
                return ''
            try:
                return string.Template(text).safe_substitute(**vars)
            except Exception:
                return text

        return {
            'title': _render(tmpl.subject_template if hasattr(tmpl, 'subject_template') else None),
            'body': _render(tmpl.body_template),
        }

    # ── Events / Audit ────────────────────────────────────────────────────────

    async def _record_event(
        self,
        notification: Notification,
        event_type: str,
        channel: NotificationChannel,
        status: NotificationStatus,
        duration_ms: str | None,
        session: AsyncSession,
        error: str | None = None,
    ) -> None:
        event = NotificationEvent(
            notification_id=notification.id,
            event_type=event_type,
            channel=channel,
            status=status,
            error=error,
            duration_ms=float(duration_ms) if duration_ms else None,
        )
        session.add(event)

    # ── Retry ─────────────────────────────────────────────────────────────────

    async def retry_failed(self, max_attempts: int = 3, db: AsyncSession | None = None) -> int:
        session = db or self._db
        stmt = select(Notification).where(
            Notification.status == NotificationStatus.FAILED,
            Notification.retry_count < Notification.max_retries,
            Notification.retry_count < max_attempts,
        ).limit(50)
        result = await session.execute(stmt)
        failed = result.scalars().all()
        count = 0
        for notification in failed:
            notification.retry_count += 1
            notification_retry_total.labels(status='attempt').inc()
            prefs = await self._load_preferences(notification.user_id, session)
            try:
                await self._dispatch(notification, prefs, session)
                count += 1
                notification_retry_total.labels(status='success').inc()
            except Exception as exc:
                notification.last_error = str(exc)
                notification_retry_total.labels(status='failed').inc()
        await session.flush()
        return count

    # ── Digest Processing ────────────────────────────────────────────────────

    async def process_digests(self, db: AsyncSession | None = None) -> int:
        session = db or self._db
        now = datetime.now(UTC)
        stmt = select(NotificationDigest).where(
            NotificationDigest.sent_at.is_(None),
            NotificationDigest.period_end <= now,
        )
        digests = (await session.execute(stmt)).scalars().all()
        count = 0
        for digest in digests:
            nstmt = select(Notification).where(Notification.id.in_(digest.notification_ids))
            notifications = (await session.execute(nstmt)).scalars().all()
            if not notifications:
                digest.sent_at = now
                continue
            first = notifications[0]
            user_id = digest.user_id
            prefs = await self._load_preferences(user_id, session)
            if not prefs:
                digest.sent_at = now
                continue
            category_counts: dict[str, int] = {}
            for n in notifications:
                cat = n.category.value if n.category else 'unknown'
                category_counts[cat] = category_counts.get(cat, 0) + 1
            channels = digest.channels or []
            for ch_name in channels:
                try:
                    ch = NotificationChannel(ch_name)
                except ValueError:
                    continue
                if not self._is_channel_allowed(prefs, ch):
                    continue
                title = f'Digest: {digest.total_count} notifications'
                body_lines = [f'You have {digest.total_count} pending notifications:']
                for cat, cnt in sorted(category_counts.items(), key=lambda x: -x[1]):
                    body_lines.append(f'  - {cat}: {cnt}')
                body_lines.append(f'Period: {digest.period_start.strftime("%b %d %H:%M")} — {digest.period_end.strftime("%b %d %H:%M")}')
                body = '\n'.join(body_lines)
                n = Notification(
                    user_id=user_id,
                    channel=ch,
                    category=NotificationCategory.GENERAL,
                    priority=NotificationPriority.NORMAL,
                    title=title,
                    body=body,
                    metadata={'digest_id': str(digest.id), 'notification_count': digest.total_count},
                )
                session.add(n)
                await session.flush()
                await self._dispatch(n, prefs, session)
            digest.sent_at = now
            count += 1
        await session.flush()
        return count

    # ── Cleanup ────────────────────────────────────────────────────────────────

    async def cleanup_expired(self, db: AsyncSession | None = None) -> int:
        session = db or self._db
        stmt = select(Notification).where(
            Notification.expires_at.is_not(None),
            Notification.expires_at < datetime.now(UTC),
            Notification.status.in_([NotificationStatus.PENDING, NotificationStatus.SENT]),
        )
        expired = (await session.execute(stmt)).scalars().all()
        for n in expired:
            n.status = NotificationStatus.CANCELLED
            n.last_error = 'Expired'
        await session.flush()
        return len(expired)

    # ── Analytics ──────────────────────────────────────────────────────────────

    async def track_open(
        self,
        notification_id: str,
        user_id: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        session = db or self._db
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        n = (await session.execute(stmt)).scalar_one_or_none()
        if n and n.status == NotificationStatus.SENT:
            n.status = NotificationStatus.DELIVERED
            n.read_at = datetime.now(UTC)
            await session.flush()
            event_stmt = select(NotificationEvent).where(
                NotificationEvent.notification_id == n.id,
                NotificationEvent.event_type == 'dispatch',
            ).order_by(NotificationEvent.occurred_at.desc()).limit(1)
            event = (await session.execute(event_stmt)).scalar_one_or_none()
            if event:
                event.opened_at = datetime.now(UTC)
                event.user_agent = user_agent
                event.ip_address = ip_address

    async def track_click(
        self,
        notification_id: str,
        user_id: str,
        utm_source: str | None = None,
        utm_medium: str | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        session = db or self._db
        event_stmt = select(NotificationEvent).where(
            NotificationEvent.notification_id == notification_id,
        ).order_by(NotificationEvent.occurred_at.desc()).limit(1)
        event = (await session.execute(event_stmt)).scalar_one_or_none()
        if event:
            event.clicked_at = datetime.now(UTC)
            if utm_source:
                event.utm_source = utm_source
            if utm_medium:
                event.utm_medium = utm_medium

    # ── Offline Queue ─────────────────────────────────────────────────────────

    async def enqueue_offline(
        self,
        user_id: str,
        notification_data: dict[str, Any],
        db: AsyncSession | None = None,
    ) -> Notification:
        """Queue a notification for delivery when the user comes online."""
        n = Notification(
            user_id=user_id,
            channel=NotificationChannel(notification_data.get('channel', 'in_app')),
            category=NotificationCategory(notification_data.get('category', 'general')),
            priority=NotificationPriority(notification_data.get('priority', 'normal')),
            title=notification_data.get('title', ''),
            body=notification_data.get('body'),
            payload=notification_data.get('metadata'),
            source='offline_queue',
            status=NotificationStatus.PENDING,
        )
        session = db or self._db
        session.add(n)
        await session.flush()
        return n

    async def process_offline_queue(
        self,
        user_id: str,
        db: AsyncSession | None = None,
    ) -> int:
        """Re-process all PENDING notifications for a user that were queued offline."""
        session = db or self._db
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.source == 'offline_queue',
            Notification.status == NotificationStatus.PENDING,
        )
        pending = (await session.execute(stmt)).scalars().all()
        prefs = await self._load_preferences(user_id, session)
        count = 0
        for n in pending:
            try:
                await self._dispatch(n, prefs, session)
                count += 1
            except Exception as exc:
                n.last_error = str(exc)
        await session.flush()
        return count

    # ── Mark Read ──────────────────────────────────────────────────────────────

    async def mark_read(self, notification_id: str, user_id: str, db: AsyncSession | None = None) -> bool:
        session = db or self._db
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        n = (await session.execute(stmt)).scalar_one_or_none()
        if not n:
            return False
        n.status = NotificationStatus.READ
        n.read_at = datetime.now(UTC)
        await session.flush()
        return True

    async def mark_all_read(self, user_id: str, db: AsyncSession | None = None) -> int:
        session = db or self._db
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED]),
        )
        notifications = (await session.execute(stmt)).scalars().all()
        now = datetime.now(UTC)
        for n in notifications:
            n.status = NotificationStatus.READ
            n.read_at = now
        await session.flush()
        return len(notifications)

    # ── Webhook Endpoints ─────────────────────────────────────────────────────

    async def register_webhook(
        self,
        user_id: str,
        name: str,
        url: str,
        events: list[str] | None = None,
        channel_type: str = 'webhook',
        secret: str | None = None,
        db: AsyncSession | None = None,
    ) -> WebhookEndpoint:
        session = db or self._db
        endpoint = WebhookEndpoint(
            user_id=user_id,
            name=name,
            url=url,
            events=events or [],
            channel_type=channel_type,
            secret=secret,
        )
        session.add(endpoint)
        await session.flush()
        return endpoint

    async def test_webhook(self, url: str, payload: dict[str, Any] | None = None) -> bool:
        client = await self.get_http_client()
        try:
            resp = await client.post(url, json=payload or {'test': True, 'timestamp': datetime.now(UTC).isoformat()})
            return resp.status_code < 300
        except Exception:
            return False


# ── Synchronization helpers ─────────────────────────────────────────────────


async def create_default_templates(db: AsyncSession) -> None:
    templates = [
        NotificationTemplate(
            name='issue_created',
            channel=NotificationChannel.SLACK,
            category=NotificationCategory.ISSUE,
            subject_template='New Issue: ${title}',
            body_template='A new ${category} issue has been reported in ${location}.\n\n${description}',
            variables=['title', 'category', 'location', 'description'],
        ),
        NotificationTemplate(
            name='sos_alert',
            channel=NotificationChannel.EMAIL,
            category=NotificationCategory.SOS,
            subject_template='🚨 SOS Alert: ${user_name} needs help',
            body_template='${user_name} has triggered an SOS alert.\n\nLocation: ${location}\nTime: ${time}\n\nPlease respond immediately.',
            variables=['user_name', 'location', 'time'],
        ),
        NotificationTemplate(
            name='sla_breach',
            channel=NotificationChannel.DISCORD,
            category=NotificationCategory.INCIDENT,
            subject_template='SLA Breach: ${complaint_ref}',
            body_template='Complaint ${complaint_ref} (${issue_type}) has breached SLA.\nOverdue by ${overdue_hours:.1f} hours.',
            variables=['complaint_ref', 'issue_type', 'overdue_hours'],
        ),
        NotificationTemplate(
            name='deployment_status',
            channel=NotificationChannel.TEAMS,
            category=NotificationCategory.DEPLOYMENT,
            subject_template='Deployment ${status}: ${service_name}',
            body_template='Service ${service_name} deployment to ${environment} is ${status}.\nVersion: ${version}',
            variables=['status', 'service_name', 'environment', 'version'],
        ),
        NotificationTemplate(
            name='system_health',
            channel=NotificationChannel.EMAIL,
            category=NotificationCategory.SYSTEM_HEALTH,
            subject_template='System Health Alert: ${component} — ${status}',
            body_template='Component: ${component}\nStatus: ${status}\nMetric: ${metric}\nThreshold: ${threshold}',
            variables=['component', 'status', 'metric', 'threshold'],
        ),
    ]
    for tmpl in templates:
        exists = await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.name == tmpl.name,
                NotificationTemplate.channel == tmpl.channel,
            )
        )
        if not exists.scalar_one_or_none():
            db.add(tmpl)
    await db.flush()
