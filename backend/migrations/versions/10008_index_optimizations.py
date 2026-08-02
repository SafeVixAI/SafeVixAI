# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Add query performance indexes for Phase 3.

Adds:
- Index on road_issues.issue_type (B-tree)
- Index on road_issues.severity (B-tree)
- Index on road_issues.created_at (B-tree, DESC)
- Composite index on road_issues (status, issue_type) for filtered queries
- Composite index on road_issues (status, created_at DESC) for "recent open issues" queries
- Composite GIST index on road_issues (location, status) for spatial+status filtering

Revision ID: 10008_index_optimizations
Revises: 10007
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = '10008_index_optimizations'
down_revision = '10007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # B-tree indexes for filtered lookups and sorting
    op.create_index('ix_road_issues_issue_type', 'road_issues', ['issue_type'], postgresql_using='btree')
    op.create_index('ix_road_issues_severity', 'road_issues', ['severity'], postgresql_using='btree')
    op.create_index('ix_road_issues_created_at_desc', 'road_issues', [sa.text('created_at DESC')], postgresql_using='btree')

    # Composite indexes for common query patterns
    op.create_index(
        'ix_road_issues_status_issue_type',
        'road_issues',
        ['status', 'issue_type'],
        postgresql_using='btree',
    )
    op.create_index(
        'ix_road_issues_status_created_at',
        'road_issues',
        [sa.text('status, created_at DESC')],
        postgresql_using='btree',
    )

    # Enable btree_gist extension to allow composite index on location (geometry) and status (varchar)
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')

    # Spatial composite: GIST index on (location, status) for queries like
    # "find all open issues within this radius"
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_road_issues_location_status_gist '
        'ON road_issues USING gist (location, status)'
    )

    # Index for live tracking group_id lookups (only if table exists)
    conn = op.get_bind()
    has_live_tracking_groups = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'live_tracking_groups')")
    ).scalar()
    if has_live_tracking_groups:
        op.create_index('ix_live_tracking_groups_group_id', 'live_tracking_groups', ['group_id'], postgresql_using='btree')


def downgrade() -> None:
    op.drop_index('ix_road_issues_issue_type', table_name='road_issues')
    op.drop_index('ix_road_issues_severity', table_name='road_issues')
    op.drop_index('ix_road_issues_created_at_desc', table_name='road_issues')
    op.drop_index('ix_road_issues_status_issue_type', table_name='road_issues')
    op.drop_index('ix_road_issues_status_created_at', table_name='road_issues')
    op.execute('DROP INDEX IF EXISTS ix_road_issues_location_status_gist')

    conn = op.get_bind()
    has_live_tracking_groups = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'live_tracking_groups')")
    ).scalar()
    if has_live_tracking_groups:
        op.drop_index('ix_live_tracking_groups_group_id', table_name='live_tracking_groups')
