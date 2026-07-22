# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""create operator users table

Revision ID: 3947cb9fa679
Revises: ca14ab8693a2
Create Date: 2026-05-25 18:50:47.843364

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3947cb9fa679'
down_revision = 'ca14ab8693a2'
branch_labels = None
depends_on = None


def _table_exists(conn, table_name: str) -> bool:
    """Check if a table exists in the public schema."""
    result = conn.execute(
        sa.text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = :table_name
        """),
        {"table_name": table_name}
    )
    return result.fetchone() is not None


def upgrade() -> None:
    """Create operator_users table and configure its RLS security."""
    conn = op.get_bind()

    if not _table_exists(conn, 'operator_users'):
        op.create_table(
            'operator_users',
            sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('role', sa.String(32), server_default='operator', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )
        op.create_index('ix_operator_users_email', 'operator_users', ['email'], unique=True)

    # Enable RLS policies on the table
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'")
    )
    if result.fetchone():
        op.execute(
            """
            DO $$
            BEGIN
              IF to_regclass('public.operator_users') IS NOT NULL THEN
                ALTER TABLE public.operator_users ENABLE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS "Operators can read operator users" ON public.operator_users;
                CREATE POLICY "Operators can read operator users"
                  ON public.operator_users FOR SELECT
                  TO authenticated
                  USING (true);
              END IF;
            END $$;
            """
        )


def downgrade() -> None:
    """Clean up operator_users table and policies."""
    conn = op.get_bind()

    if _table_exists(conn, 'operator_users'):
        op.execute(
            """
            DO $$
            BEGIN
              IF to_regclass('public.operator_users') IS NOT NULL THEN
                ALTER TABLE public.operator_users DISABLE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS "Operators can read operator users" ON public.operator_users;
              END IF;
            END $$;
            """
        )
        op.drop_table('operator_users')
