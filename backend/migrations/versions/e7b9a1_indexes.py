"""GiST and covering indexes for enterprise smart city queries.

Revision ID: e7b9a1
Revises: 
Create Date: 2026-06-29 18:45:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e7b9a1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use execute to add GiST index for PostGIS geometry column safely
    op.execute("CREATE INDEX IF NOT EXISTS idx_road_issues_location_gist ON road_issues USING GIST (location)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_road_issues_status_category ON road_issues (status, category)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_road_issues_created_at ON road_issues (created_at DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_road_issues_created_at")
    op.execute("DROP INDEX IF EXISTS idx_road_issues_status_category")
    op.execute("DROP INDEX IF EXISTS idx_road_issues_location_gist")
