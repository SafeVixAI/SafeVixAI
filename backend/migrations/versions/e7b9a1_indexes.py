"""DESC index on created_at for road_issues.

Revision ID: e7b9a1
Revises: 001_initial_schema
Create Date: 2026-06-29 18:45:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e7b9a1'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS idx_road_issues_created_at ON road_issues (created_at DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_road_issues_created_at")
