# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""align Supabase RLS policies with backend ownership model

Revision ID: 10003_rls_alignment
Revises: 10002_challan_tables
Create Date: 2026-05-07 00:00:00.000000
"""

from alembic import op
from sqlalchemy import text

revision = '10003_rls_alignment'
down_revision = '10002_challan_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply direct Supabase Data API RLS policies.

    FastAPI should continue to access the database with its server-side
    credentials. These policies protect any direct anon/authenticated Supabase
    client access and align ownership checks with `user_id = auth.uid()::text`.
    """
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
          IF to_regclass('public.user_profiles') IS NOT NULL THEN
            ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Enable read access for authenticated users on user_profiles" ON public.user_profiles;
            DROP POLICY IF EXISTS "Users can insert their own profile" ON public.user_profiles;
            DROP POLICY IF EXISTS "Users can update their own profile" ON public.user_profiles;
            DROP POLICY IF EXISTS "Users can read own profile" ON public.user_profiles;
            DROP POLICY IF EXISTS "Users can insert own profile" ON public.user_profiles;
            DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;
            DROP POLICY IF EXISTS "Users can delete own profile" ON public.user_profiles;
            CREATE POLICY "Users can read own profile"
              ON public.user_profiles FOR SELECT
              TO authenticated
              USING (user_id = auth.uid()::text);
            CREATE POLICY "Users can insert own profile"
              ON public.user_profiles FOR INSERT
              TO authenticated
              WITH CHECK (user_id = auth.uid()::text);
            CREATE POLICY "Users can update own profile"
              ON public.user_profiles FOR UPDATE
              TO authenticated
              USING (user_id = auth.uid()::text)
              WITH CHECK (user_id = auth.uid()::text);
            CREATE POLICY "Users can delete own profile"
              ON public.user_profiles FOR DELETE
              TO authenticated
              USING (user_id = auth.uid()::text);
          END IF;

          IF to_regclass('public.road_issues') IS NOT NULL THEN
            ALTER TABLE public.road_issues ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Enable read access for authenticated users on road_issues" ON public.road_issues;
            DROP POLICY IF EXISTS "Users can insert road issues" ON public.road_issues;
            DROP POLICY IF EXISTS "Users can update their own road issues" ON public.road_issues;
            DROP POLICY IF EXISTS "Public can read road issues" ON public.road_issues;
            DROP POLICY IF EXISTS "Public can insert road issues" ON public.road_issues;
            DROP POLICY IF EXISTS "Users can update own road issues" ON public.road_issues;
            CREATE POLICY "Public can read road issues"
              ON public.road_issues FOR SELECT
              TO anon, authenticated
              USING (true);
            IF EXISTS (
              SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = 'road_issues' AND column_name = 'reporter_id'
            ) THEN
              CREATE POLICY "Public can insert road issues"
                ON public.road_issues FOR INSERT
                TO anon, authenticated
                WITH CHECK (reporter_id IS NULL OR reporter_id::text = auth.uid()::text);
              CREATE POLICY "Users can update own road issues"
                ON public.road_issues FOR UPDATE
                TO authenticated
                USING (reporter_id::text = auth.uid()::text)
                WITH CHECK (reporter_id::text = auth.uid()::text);
            ELSE
              CREATE POLICY "Public can insert road issues"
                ON public.road_issues FOR INSERT
                TO anon, authenticated
                WITH CHECK (true);
            END IF;
          END IF;

          IF to_regclass('public.sos_incidents') IS NOT NULL THEN
            ALTER TABLE public.sos_incidents ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read sos incidents" ON public.sos_incidents;
            DROP POLICY IF EXISTS "Public can insert sos incidents" ON public.sos_incidents;
            DROP POLICY IF EXISTS "Users can read own sos incidents" ON public.sos_incidents;
            DROP POLICY IF EXISTS "Users can insert own sos incidents" ON public.sos_incidents;
          END IF;

          IF to_regclass('public.live_tracking') IS NOT NULL THEN
            ALTER TABLE public.live_tracking ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Authenticated users can read active tracking sessions" ON public.live_tracking;
            DROP POLICY IF EXISTS "Authenticated users can create tracking sessions" ON public.live_tracking;
            DROP POLICY IF EXISTS "Users can update their own tracking sessions" ON public.live_tracking;
            DROP POLICY IF EXISTS "Users can read own tracking sessions" ON public.live_tracking;
            DROP POLICY IF EXISTS "Users can create own tracking sessions" ON public.live_tracking;
            DROP POLICY IF EXISTS "Users can update own tracking sessions" ON public.live_tracking;
            DROP POLICY IF EXISTS "Users can stop own tracking sessions" ON public.live_tracking;
            CREATE POLICY "Users can read own tracking sessions"
              ON public.live_tracking FOR SELECT
              TO authenticated
              USING (user_id = auth.uid()::text);
            CREATE POLICY "Users can create own tracking sessions"
              ON public.live_tracking FOR INSERT
              TO authenticated
              WITH CHECK (user_id = auth.uid()::text);
            CREATE POLICY "Users can update own tracking sessions"
              ON public.live_tracking FOR UPDATE
              TO authenticated
              USING (user_id = auth.uid()::text)
              WITH CHECK (user_id = auth.uid()::text);
            CREATE POLICY "Users can stop own tracking sessions"
              ON public.live_tracking FOR DELETE
              TO authenticated
              USING (user_id = auth.uid()::text);
          END IF;

          IF to_regclass('public.chat_logs') IS NOT NULL
            AND EXISTS (
              SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = 'chat_logs' AND column_name = 'user_id'
            )
          THEN
            ALTER TABLE public.chat_logs ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Users can read own chat logs" ON public.chat_logs;
            DROP POLICY IF EXISTS "Users can insert own chat logs" ON public.chat_logs;
            DROP POLICY IF EXISTS "Users can update own chat logs" ON public.chat_logs;
            CREATE POLICY "Users can read own chat logs"
              ON public.chat_logs FOR SELECT
              TO authenticated
              USING (user_id = auth.uid()::text);
            CREATE POLICY "Users can insert own chat logs"
              ON public.chat_logs FOR INSERT
              TO authenticated
              WITH CHECK (user_id = auth.uid()::text);
            CREATE POLICY "Users can update own chat logs"
              ON public.chat_logs FOR UPDATE
              TO authenticated
              USING (user_id = auth.uid()::text)
              WITH CHECK (user_id = auth.uid()::text);
          END IF;

          IF to_regclass('public.first_aid_articles') IS NOT NULL THEN
            ALTER TABLE public.first_aid_articles ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read first aid articles" ON public.first_aid_articles;
            CREATE POLICY "Public can read first aid articles"
              ON public.first_aid_articles FOR SELECT
              TO anon, authenticated
              USING (true);
          END IF;

          IF to_regclass('public.traffic_violations') IS NOT NULL THEN
            ALTER TABLE public.traffic_violations ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read traffic violations" ON public.traffic_violations;
            CREATE POLICY "Public can read traffic violations"
              ON public.traffic_violations FOR SELECT
              TO anon, authenticated
              USING (true);
          END IF;

          IF to_regclass('public.state_fine_overrides') IS NOT NULL THEN
            ALTER TABLE public.state_fine_overrides ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read state fine overrides" ON public.state_fine_overrides;
            CREATE POLICY "Public can read state fine overrides"
              ON public.state_fine_overrides FOR SELECT
              TO anon, authenticated
              USING (true);
          END IF;

          IF to_regclass('public.emergency_services') IS NOT NULL THEN
            ALTER TABLE public.emergency_services ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Enable read access for authenticated users on emergency_services" ON public.emergency_services;
            DROP POLICY IF EXISTS "Public can read emergency services" ON public.emergency_services;
            CREATE POLICY "Public can read emergency services"
              ON public.emergency_services FOR SELECT
              TO anon, authenticated
              USING (true);
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF to_regclass('public.user_profiles') IS NOT NULL THEN
            DROP POLICY IF EXISTS "Users can read own profile" ON public.user_profiles;
            DROP POLICY IF EXISTS "Users can insert own profile" ON public.user_profiles;
            DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;
            DROP POLICY IF EXISTS "Users can delete own profile" ON public.user_profiles;
          END IF;
          IF to_regclass('public.road_issues') IS NOT NULL THEN
            DROP POLICY IF EXISTS "Public can read road issues" ON public.road_issues;
            DROP POLICY IF EXISTS "Public can insert road issues" ON public.road_issues;
            DROP POLICY IF EXISTS "Users can update own road issues" ON public.road_issues;
          END IF;
          IF to_regclass('public.sos_incidents') IS NOT NULL THEN
            ALTER TABLE public.sos_incidents DISABLE ROW LEVEL SECURITY;
          END IF;
          IF to_regclass('public.live_tracking') IS NOT NULL THEN
            DROP POLICY IF EXISTS "Users can read own tracking sessions" ON public.live_tracking;
            DROP POLICY IF EXISTS "Users can create own tracking sessions" ON public.live_tracking;
            DROP POLICY IF EXISTS "Users can update own tracking sessions" ON public.live_tracking;
            DROP POLICY IF EXISTS "Users can stop own tracking sessions" ON public.live_tracking;
          END IF;
          IF to_regclass('public.chat_logs') IS NOT NULL THEN
            DROP POLICY IF EXISTS "Users can read own chat logs" ON public.chat_logs;
            DROP POLICY IF EXISTS "Users can insert own chat logs" ON public.chat_logs;
            DROP POLICY IF EXISTS "Users can update own chat logs" ON public.chat_logs;
          END IF;
          IF to_regclass('public.first_aid_articles') IS NOT NULL THEN
            DROP POLICY IF EXISTS "Public can read first aid articles" ON public.first_aid_articles;
          END IF;
          IF to_regclass('public.traffic_violations') IS NOT NULL THEN
            DROP POLICY IF EXISTS "Public can read traffic violations" ON public.traffic_violations;
          END IF;
          IF to_regclass('public.state_fine_overrides') IS NOT NULL THEN
            DROP POLICY IF EXISTS "Public can read state fine overrides" ON public.state_fine_overrides;
          END IF;
          IF to_regclass('public.emergency_services') IS NOT NULL THEN
            DROP POLICY IF EXISTS "Public can read emergency services" ON public.emergency_services;
          END IF;
        END $$;
        """
    )
