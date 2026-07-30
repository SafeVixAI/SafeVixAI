# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class NotificationChannel(str, PyEnum):
    IN_APP = 'in_app'
    DESKTOP = 'desktop'
    EMAIL = 'email'
    SMS = 'sms'
    PUSH = 'push'
    SLACK = 'slack'
    DISCORD = 'discord'
    WEBHOOK = 'webhook'
    TEAMS = 'teams'


class NotificationPriority(str, PyEnum):
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    CRITICAL = 'critical'


class NotificationCategory(str, PyEnum):
    SYSTEM_HEALTH = 'system_health'
    AI = 'ai'
    SECURITY = 'security'
    PERFORMANCE = 'performance'
    UPDATE = 'update'
    MAINTENANCE = 'maintenance'
    INCIDENT = 'incident'
    DEPLOYMENT = 'deployment'
    USAGE = 'usage'
    BILLING = 'billing'
    ISSUE = 'issue'
    SOS = 'sos'
    EMERGENCY = 'emergency'
    CHALLAN = 'challan'
    GENERAL = 'general'


class NotificationStatus(str, PyEnum):
    PENDING = 'pending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    org_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    category: Mapped[NotificationCategory] = mapped_column(Enum(NotificationCategory), nullable=False)
    priority: Mapped[NotificationPriority] = mapped_column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column('metadata', JSON, nullable=True)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class NotificationPreference(Base):
    __tablename__ = 'notification_preferences'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True, unique=True)
    org_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    channels_enabled: Mapped[dict[str, bool]] = mapped_column(JSON, nullable=False, default=lambda: {
        'in_app': True, 'email': True, 'sms': False, 'push': True,
        'slack': False, 'discord': False, 'webhook': False, 'teams': False,
    })
    categories_enabled: Mapped[dict[str, bool]] = mapped_column(JSON, nullable=False, default=lambda: {
        'system_health': True, 'ai': True, 'security': True, 'performance': True,
        'update': True, 'maintenance': True, 'incident': True, 'deployment': True,
        'usage': True, 'billing': True, 'issue': True, 'sos': True,
        'emergency': True, 'challan': True, 'general': True,
    })
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    digest_frequency: Mapped[str] = mapped_column(String(32), default='daily')
    dnd_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dnd_start_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dnd_end_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dnd_timezone: Mapped[str] = mapped_column(String(64), default='UTC')
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5), nullable=True)
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5), nullable=True)
    push_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    push_token_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    slack_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    discord_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    teams_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), default='en')
    max_daily_notifications: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class NotificationTemplate(Base):
    __tablename__ = 'notification_templates'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    category: Mapped[NotificationCategory] = mapped_column(Enum(NotificationCategory), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default='en')
    subject_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    html_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    variables: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class NotificationDigest(Base):
    __tablename__ = 'notification_digests'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    org_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notification_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    channels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class WebhookEndpoint(Base):
    __tablename__ = 'webhook_endpoints'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    org_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    events: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    channel_type: Mapped[str] = mapped_column(String(32), default='webhook')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class NotificationEvent(Base):
    __tablename__ = 'notification_events'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column('metadata', JSON, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(128), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
