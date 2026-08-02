# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Add enterprise workflow tracking columns to road_issues table.

Revision ID: 10012_workflow_cols
Revises: 10011_civic_intel_tables
Create Date: 2026-05-25 15:50:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = '10012_workflow_cols'
down_revision = '10011_civic_intel_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adding new columns to road_issues
    op.add_column('road_issues', sa.Column('escalation_tier', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('road_issues', sa.Column('accepted_at', sa.DateTime(), nullable=True))
    op.add_column('road_issues', sa.Column('accepted_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('road_issues', sa.Column('work_started_at', sa.DateTime(), nullable=True))
    op.add_column('road_issues', sa.Column('citizen_confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('road_issues', sa.Column('citizen_rating', sa.Integer(), nullable=True))
    op.add_column('road_issues', sa.Column('department', sa.String(length=64), nullable=True))
    op.add_column('road_issues', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('road_issues', sa.Column('reopen_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Drop added columns
    op.drop_column('road_issues', 'reopen_count')
    op.drop_column('road_issues', 'rejection_reason')
    op.drop_column('road_issues', 'department')
    op.drop_column('road_issues', 'citizen_rating')
    op.drop_column('road_issues', 'citizen_confirmed_at')
    op.drop_column('road_issues', 'work_started_at')
    op.drop_column('road_issues', 'accepted_by')
    op.drop_column('road_issues', 'accepted_at')
    op.drop_column('road_issues', 'escalation_tier')
