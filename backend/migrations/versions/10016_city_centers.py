"""create city_centers table (B-P2.5 — extract CITY_CENTERS from hardcoded dict)

Revision ID: 10016_city_centers
Revises: eb59ee6949aa
Create Date: 2026-07-04 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '10016_city_centers'
down_revision = 'eb59ee6949aa'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'city_centers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('city_slug', sa.String(64), nullable=False, comment='Lowercase ASCII slug — chennai, bengaluru, …'),
        sa.Column('display_name', sa.String(128), nullable=False, comment='Human-readable city name'),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('is_offline_bundle', sa.Boolean(), nullable=False, server_default=sa.text('false'),
                  comment='True if included in PWA offline emergency bundles'),
        sa.Column('state', sa.String(64), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_city_centers_city_slug', 'city_centers', ['city_slug'], unique=True)


def downgrade():
    op.drop_index('ix_city_centers_city_slug', table_name='city_centers')
    op.drop_table('city_centers')
