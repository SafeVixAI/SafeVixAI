# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""add sos incidents RLS policies

Revision ID: 10006_sos_rls
Revises: 10005_data_retention
Create Date: 2026-05-18 00:00:00.000000
"""

from alembic import op
from sqlalchemy import text

revision = '10006_sos_rls'
down_revision = '10005_data_retention'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """P0-10: Add RLS policies for sos_incidents to prevent data leakage (audit C10)."""
    # Check if 'authenticated' role exists (Supabase-specific)
    # Skip RLS policies if role doesn't exist (e.g., in CI/test environments)
    conn = op.get_bind()
    result = conn.execute(
        text("SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'")
    )
    if not result.fetchone():
        return  # Skip RLS setup in non-Supabase environments

    op.execute(
        """
        DO $$
        BEGIN
          IF to_regclass('public.sos_incidents') IS NOT NULL THEN
            ALTER TABLE public.sos_incidents ENABLE ROW LEVEL SECURITY;
            
            DROP POLICY IF EXISTS "Public can insert sos incidents" ON public.sos_incidents;
            DROP POLICY IF EXISTS "Users can read own sos incidents" ON public.sos_incidents;

            -- P0-10: Anyone can insert SOS (anon or auth), but auth users must use their own ID
            CREATE POLICY "Public can insert sos incidents"
              ON public.sos_incidents FOR INSERT
              TO anon, authenticated
              WITH CHECK (user_id IS NULL OR user_id::text = auth.uid()::text);
              
            -- P0-10: Users can only read their own SOS incidents
            CREATE POLICY "Users can read own sos incidents"
              ON public.sos_incidents FOR SELECT
              TO authenticated
              USING (user_id::text = auth.uid()::text);
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF to_regclass('public.sos_incidents') IS NOT NULL THEN
            DROP POLICY IF EXISTS "Public can insert sos incidents" ON public.sos_incidents;
            DROP POLICY IF EXISTS "Users can read own sos incidents" ON public.sos_incidents;
          END IF;
        END $$;
        """
    )
