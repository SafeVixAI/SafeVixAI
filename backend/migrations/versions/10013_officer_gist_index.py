# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""add officer spatial index

Revision ID: 10013_officer_gist_index
Revises: 3947cb9fa679
Create Date: 2026-05-26 08:45:00.000000

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '10013_officer_gist_index'
down_revision = '3947cb9fa679'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create GIST index on officers.last_location geometry column."""
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_officers_last_location_gist '
        'ON officers USING gist (last_location)'
    )


def downgrade() -> None:
    """Drop GIST index on officers.last_location."""
    op.execute('DROP INDEX IF EXISTS ix_officers_last_location_gist')
