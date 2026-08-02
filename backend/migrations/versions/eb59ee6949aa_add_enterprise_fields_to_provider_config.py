"""add enterprise fields to provider config

Revision ID: eb59ee6949aa
Revises: 3cc9de31ca26
Create Date: 2026-06-30 07:48:23.920123

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'eb59ee6949aa'
down_revision = '3cc9de31ca26'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('user_provider_configs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=False),
    sa.Column('provider_name', sa.String(length=64), nullable=False),
    sa.Column('display_name', sa.String(length=128), nullable=False),
    sa.Column('api_key_encrypted', sa.Text(), nullable=True),
    sa.Column('base_url', sa.String(length=512), nullable=True),
    sa.Column('default_model', sa.String(length=128), nullable=True),
    sa.Column('extra_headers', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('is_custom', sa.Boolean(), nullable=False),
    sa.Column('is_local_model', sa.Boolean(), nullable=False),
    sa.Column('timeout_ms', sa.Integer(), nullable=True),
    sa.Column('circuit_breaker_failures', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_provider_configs_user_id'), 'user_provider_configs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_provider_configs_user_id'), table_name='user_provider_configs')
    op.drop_table('user_provider_configs')
