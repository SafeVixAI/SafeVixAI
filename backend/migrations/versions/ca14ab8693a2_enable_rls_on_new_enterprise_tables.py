# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""enable rls on new enterprise tables

Revision ID: ca14ab8693a2
Revises: 10012_workflow_cols
Create Date: 2026-05-25 18:43:10.256618

"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'ca14ab8693a2'
down_revision = '10012_workflow_cols'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable Row-Level Security and add access policies for new enterprise tables."""
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
          IF to_regclass('public.wards') IS NOT NULL THEN
            ALTER TABLE public.wards ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read wards" ON public.wards;
            CREATE POLICY "Public can read wards"
              ON public.wards FOR SELECT
              TO anon, authenticated
              USING (true);
          END IF;

          IF to_regclass('public.officers') IS NOT NULL THEN
            ALTER TABLE public.officers ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read officers" ON public.officers;
            CREATE POLICY "Public can read officers"
              ON public.officers FOR SELECT
              TO anon, authenticated
              USING (true);
          END IF;

          IF to_regclass('public.complaint_events') IS NOT NULL THEN
            ALTER TABLE public.complaint_events ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read complaint events" ON public.complaint_events;
            CREATE POLICY "Public can read complaint events"
              ON public.complaint_events FOR SELECT
              TO anon, authenticated
              USING (true);
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Disable RLS and clean up policies on new enterprise tables."""
    op.execute(
        """
        DO $$
        BEGIN
          IF to_regclass('public.wards') IS NOT NULL THEN
            ALTER TABLE public.wards DISABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read wards" ON public.wards;
          END IF;

          IF to_regclass('public.officers') IS NOT NULL THEN
            ALTER TABLE public.officers DISABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read officers" ON public.officers;
          END IF;

          IF to_regclass('public.complaint_events') IS NOT NULL THEN
            ALTER TABLE public.complaint_events DISABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read complaint events" ON public.complaint_events;
          END IF;
        END $$;
        """
    )
