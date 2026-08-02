"""BRIN index on road_issues.created_at for time-series range scans.

BRIN (Block Range INdex) is dramatically more space-efficient than B-tree
for append-heavy time-series columns. The existing B-tree DESC index is
retained for ORDER BY + LIMIT queries; BRIN adds fast range-scan support
for analytics / SLA queries over date ranges.

Revision ID: 10015_brin_index_created_at
Revises: eb59ee6949aa
Create Date: 2026-07-04 12:00:00.000000
"""
from __future__ import annotations

from alembic import op

revision = '10015_brin_index_created_at'
down_revision = 'eb59ee6949aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        'CREATE INDEX IF NOT EXISTS idx_road_issues_created_at_brin '
        'ON road_issues USING brin (created_at) '
        'WITH (pages_per_range=2)'
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_road_issues_created_at_brin')
