# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""create live_tracking table for family tracking

Revision ID: 10000_live_tracking
Revises: 9999_enable_rls
Create Date: 2026-04-27 00:00:00.000000
"""
from alembic import op
from sqlalchemy import text

revision = '10000_live_tracking'
down_revision = '9999_enable_rls'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS live_tracking (
            session_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id TEXT,
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            accuracy FLOAT,
            speed_kmh FLOAT,
            battery_percent INT,
            is_active BOOLEAN DEFAULT TRUE,
            started_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '4 hours',
            user_name TEXT,
            blood_group TEXT,
            vehicle_number TEXT,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # Check if 'authenticated' role exists (Supabase-specific)
    # Skip RLS policies if role doesn't exist (e.g., in CI/test environments)
    conn = op.get_bind()
    result = conn.execute(
        text("SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'")
    )
    if not result.fetchone():
        return  # Skip RLS setup in non-Supabase environments

    # Enable RLS
    op.execute("ALTER TABLE live_tracking ENABLE ROW LEVEL SECURITY;")

    # Direct Supabase reads are restricted; family access goes through the signed API link.
    op.execute("""
        CREATE POLICY "Authenticated users can read active tracking sessions"
        ON live_tracking FOR SELECT
        TO authenticated
        USING (is_active = true AND expires_at > NOW());
    """)

    # Only authenticated users (or service role) can insert/update
    op.execute("""
        CREATE POLICY "Authenticated users can create tracking sessions"
        ON live_tracking FOR INSERT
        TO authenticated
        WITH CHECK (true);
    """)

    op.execute("""
        CREATE POLICY "Users can update their own tracking sessions"
        ON live_tracking FOR UPDATE
        TO authenticated
        USING (user_id = auth.uid()::text);
    """)

    # Enable Realtime on this table (Supabase specific)
    # Check if the supabase_realtime publication exists before altering it
    pub_result = conn.execute(
        text("SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime'")
    )
    if pub_result.fetchone():
        op.execute("ALTER PUBLICATION supabase_realtime ADD TABLE live_tracking;")


def downgrade() -> None:
    op.execute('DROP POLICY IF EXISTS "Authenticated users can read active tracking sessions" ON live_tracking;')
    op.execute('DROP POLICY IF EXISTS "Authenticated users can create tracking sessions" ON live_tracking;')
    op.execute('DROP POLICY IF EXISTS "Users can update their own tracking sessions" ON live_tracking;')
    op.execute("DROP TABLE IF EXISTS live_tracking;")
