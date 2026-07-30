# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Create issue_reports and issue_timeline_events tables.

Revision ID: 10020
Revises: 10019
Create Date: 2026-07-28
"""

from __future__ import annotations

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '10020'
down_revision: str | None = '10019'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        'issue_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('org_id', sa.String(36), nullable=True, index=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('tracking_number', sa.String(32), nullable=False, unique=True, index=True),
        sa.Column('issue_type', sa.String(32), nullable=False, index=True),
        sa.Column('category', sa.String(32), nullable=False, index=True),
        sa.Column('severity', sa.String(16), nullable=False, server_default='medium'),
        sa.Column('priority', sa.String(16), nullable=False, server_default='normal'),
        sa.Column('status', sa.String(24), nullable=False, server_default='new', index=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('steps_to_reproduce', sa.Text(), nullable=True),
        sa.Column('expected_behavior', sa.Text(), nullable=True),
        sa.Column('actual_behavior', sa.Text(), nullable=True),
        sa.Column('environment', sa.Text(), nullable=True),
        sa.Column('browser_info', postgresql.JSONB(), nullable=True),
        sa.Column('device_info', postgresql.JSONB(), nullable=True),
        sa.Column('os_info', sa.String(128), nullable=True),
        sa.Column('app_version', sa.String(32), nullable=True),
        sa.Column('attachments', postgresql.JSONB(), nullable=True),
        sa.Column('screenshot_urls', postgresql.JSONB(), nullable=True),
        sa.Column('screen_recording_url', sa.Text(), nullable=True),
        sa.Column('logs', postgresql.JSONB(), nullable=True),
        sa.Column('system_info', postgresql.JSONB(), nullable=True),
        sa.Column('labels', postgresql.JSONB(), nullable=True),
        sa.Column('assignee', sa.String(128), nullable=True),
        sa.Column('milestone', sa.String(128), nullable=True),
        sa.Column('github_issue_url', sa.Text(), nullable=True),
        sa.Column('github_issue_number', sa.Integer(), nullable=True),
        sa.Column('github_discussion_url', sa.Text(), nullable=True),
        sa.Column('duplicate_of', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('duplicate_score', sa.Float(), nullable=True),
        sa.Column('is_spam', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('spam_reason', sa.String(128), nullable=True),
        sa.Column('ai_category', sa.String(64), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('ai_suggested_fix', sa.Text(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reporter_name', sa.String(128), nullable=True),
        sa.Column('reporter_email', sa.String(256), nullable=True),
        sa.Column(
            'location',
            geoalchemy2.Geometry(geometry_type='POINT', srid=4326, spatial_index=True),
            nullable=True,
        ),
        sa.Column('sla_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sla_resolution_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_issue_reports_tracking', 'issue_reports', ['tracking_number'])
    op.create_index('ix_issue_reports_created_at', 'issue_reports', ['created_at'])
    op.create_index('ix_issue_reports_status_severity', 'issue_reports', ['status', 'severity'])

    op.create_table(
        'issue_timeline_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('issue_uuid', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('event_type', sa.String(48), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('actor', sa.String(128), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_issue_timeline_issue', 'issue_timeline_events', ['issue_uuid', 'created_at'])


def downgrade() -> None:
    op.drop_table('issue_timeline_events')
    op.drop_table('issue_reports')
