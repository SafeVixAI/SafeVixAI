"""Add retry_on_failure column to update_settings.

Revision ID: 10019_add_retry_on_failure
Revises: 10018_add_gpg_public_key
Create Date: 2026-07-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "10019_add_retry_on_failure"
down_revision = "10018_add_gpg_public_key"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("update_settings", sa.Column("retry_on_failure", sa.Boolean(), nullable=False, server_default=sa.text("true")))


def downgrade() -> None:
    op.drop_column("update_settings", "retry_on_failure")
