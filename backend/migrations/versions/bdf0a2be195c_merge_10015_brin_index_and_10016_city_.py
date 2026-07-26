"""merge 10015_brin_index and 10016_city_centers

Revision ID: bdf0a2be195c
Revises: 10015_brin_index_created_at, 10016_city_centers
Create Date: 2026-07-26 21:36:59.686584

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bdf0a2be195c'
down_revision = ('10015_brin_index_created_at', '10016_city_centers')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
