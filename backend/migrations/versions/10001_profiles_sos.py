# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""secure user profiles and create sos incidents

Revision ID: 10001_profiles_sos
Revises: 10000_live_tracking
Create Date: 2026-05-06 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = '10001_profiles_sos'
down_revision = '10000_live_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if user_id column exists before adding
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'user_profiles' AND column_name = 'user_id'
        """)
    )

    if not result.fetchone():
        # Column doesn't exist, add it
        op.add_column('user_profiles', sa.Column('user_id', sa.String(length=255), nullable=True))

    # Update user_id from id if NULL (UUID to string conversion)
    op.execute(sa.text("UPDATE user_profiles SET user_id = id::text WHERE user_id IS NULL"))

    # Make column NOT NULL after populating
    op.alter_column('user_profiles', 'user_id', nullable=False)

    # Create index if it doesn't exist
    op.create_index('ix_user_profiles_user_id', 'user_profiles', ['user_id'], if_not_exists=True)

    op.execute("""
        CREATE TABLE IF NOT EXISTS sos_incidents (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id TEXT,
            lat DOUBLE PRECISION NOT NULL,
            lon DOUBLE PRECISION NOT NULL,
            user_agent TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.create_index('ix_sos_incidents_created_at', 'sos_incidents', ['created_at'], if_not_exists=True)
    op.create_index('ix_sos_incidents_user_id', 'sos_incidents', ['user_id'], if_not_exists=True)


def downgrade() -> None:
    op.drop_index('ix_sos_incidents_user_id', table_name='sos_incidents')
    op.drop_index('ix_sos_incidents_created_at', table_name='sos_incidents')
    op.execute("DROP TABLE IF EXISTS sos_incidents")
    op.drop_index('ix_user_profiles_user_id', table_name='user_profiles')
    op.drop_column('user_profiles', 'user_id')
