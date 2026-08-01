# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Create notification system tables (notifications, preferences, templates, digests, webhooks, events).

Revision ID: 10021
Revises: 10020
Create Date: 2026-07-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '10021'
down_revision: str | None = '10020'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ── safely create enums ──
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notificationchannel AS ENUM ('in_app', 'email', 'sms', 'push', 'slack', 'discord', 'webhook', 'teams');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notificationpriority AS ENUM ('low', 'normal', 'high', 'critical');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notificationcategory AS ENUM ('system_health', 'ai', 'security', 'performance', 'update', 'maintenance', 'incident', 'deployment', 'usage', 'billing', 'issue', 'sos', 'emergency', 'challan', 'general');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notificationstatus AS ENUM ('pending', 'sent', 'delivered', 'read', 'failed', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    chan_enum = postgresql.ENUM('in_app', 'email', 'sms', 'push', 'slack', 'discord', 'webhook', 'teams', name='notificationchannel', create_type=False)
    cat_enum = postgresql.ENUM('system_health', 'ai', 'security', 'performance', 'update', 'maintenance', 'incident', 'deployment', 'usage', 'billing', 'issue', 'sos', 'emergency', 'challan', 'general', name='notificationcategory', create_type=False)
    prio_enum = postgresql.ENUM('low', 'normal', 'high', 'critical', name='notificationpriority', create_type=False)
    stat_enum = postgresql.ENUM('pending', 'sent', 'delivered', 'read', 'failed', 'cancelled', name='notificationstatus', create_type=False)

    # ── notifications ──
    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=True, index=True),
        sa.Column('org_id', sa.String(36), nullable=True, index=True),
        sa.Column('channel', chan_enum, nullable=False),
        sa.Column('category', cat_enum, nullable=False),
        sa.Column('priority', prio_enum, nullable=False, server_default='normal'),
        sa.Column('status', stat_enum, nullable=False, server_default='pending'),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('source', sa.String(128), nullable=True),
        sa.Column('correlation_id', sa.String(128), nullable=True, index=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default=sa.text('3')),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user_status', 'notifications', ['user_id', 'status'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_category', 'notifications', ['category'])
    op.create_index('ix_notifications_correlation_user', 'notifications', ['correlation_id', 'user_id'])

    # ── notification_preferences ──
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False, index=True, unique=True),
        sa.Column('org_id', sa.String(36), nullable=True, index=True),
        sa.Column('channels_enabled', postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('categories_enabled', postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('digest_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('digest_frequency', sa.String(32), nullable=False, server_default=sa.text("'daily'")),
        sa.Column('dnd_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('dnd_start_hour', sa.Integer(), nullable=True),
        sa.Column('dnd_end_hour', sa.Integer(), nullable=True),
        sa.Column('dnd_timezone', sa.String(64), nullable=False, server_default=sa.text("'UTC'")),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('quiet_hours_start', sa.String(5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(5), nullable=True),
        sa.Column('push_token', sa.Text(), nullable=True),
        sa.Column('push_token_type', sa.String(32), nullable=True),
        sa.Column('slack_webhook_url', sa.Text(), nullable=True),
        sa.Column('discord_webhook_url', sa.Text(), nullable=True),
        sa.Column('teams_webhook_url', sa.Text(), nullable=True),
        sa.Column('webhook_url', sa.Text(), nullable=True),
        sa.Column('email_address', sa.String(512), nullable=True),
        sa.Column('phone_number', sa.String(32), nullable=True),
        sa.Column('locale', sa.String(10), nullable=False, server_default=sa.text("'en'")),
        sa.Column('max_daily_notifications', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── notification_templates ──
    op.create_table(
        'notification_templates',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(128), nullable=False, index=True, unique=True),
        sa.Column('channel', chan_enum, nullable=False),
        sa.Column('category', cat_enum, nullable=False),
        sa.Column('locale', sa.String(10), nullable=False, server_default=sa.text("'en'")),
        sa.Column('subject_template', sa.Text(), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('html_template', sa.Text(), nullable=True),
        sa.Column('variables', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── notification_digests ──
    op.create_table(
        'notification_digests',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('org_id', sa.String(36), nullable=True, index=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notification_ids', postgresql.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column('total_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('channels', postgresql.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── webhook_endpoints ──
    op.create_table(
        'webhook_endpoints',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=True, index=True),
        sa.Column('org_id', sa.String(36), nullable=True, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('secret', sa.Text(), nullable=True),
        sa.Column('events', postgresql.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column('channel_type', sa.String(32), nullable=False, server_default=sa.text("'webhook'")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_status', sa.String(32), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── notification_events (audit log) ──
    op.create_table(
        'notification_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('notification_id', sa.Uuid(), nullable=False, index=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('channel', chan_enum, nullable=False),
        sa.Column('status', stat_enum, nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_notification_events_occurred_at', 'notification_events', ['occurred_at'])


def downgrade() -> None:
    op.drop_table('notification_events')
    op.drop_table('webhook_endpoints')
    op.drop_table('notification_digests')
    op.drop_table('notification_templates')
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
    sa.Enum(name='notificationstatus').drop(op.get_bind(), if_exists=True)
    sa.Enum(name='notificationcategory').drop(op.get_bind(), if_exists=True)
    sa.Enum(name='notificationpriority').drop(op.get_bind(), if_exists=True)
    sa.Enum(name='notificationchannel').drop(op.get_bind(), if_exists=True)
