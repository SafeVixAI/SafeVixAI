"""Add gpg_public_key column to update_settings table.

Revision ID: 10018_add_gpg_public_key
Revises: 10017_update_management
Create Date: 2026-07-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "10018_add_gpg_public_key"
down_revision: str | None = "10017_update_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("update_settings", sa.Column("gpg_public_key", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("update_settings", "gpg_public_key")
