# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""enable rls policies

Revision ID: 9999_enable_rls
Revises: 
Create Date: 2026-04-23 17:00:00.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '9999_enable_rls'
down_revision = '46c1f12f346e'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Check if 'authenticated' role exists (Supabase-specific)
    # Skip RLS policies if role doesn't exist (e.g., in CI/test environments)
    conn = op.get_bind()
    result = conn.execute(
        text("SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'")
    )
    if not result.fetchone():
        return  # Skip RLS setup in non-Supabase environments

    # Enable RLS on all tables
    tables = [
        'user_profiles',
        'road_issues',
        'road_infrastructure',
        'emergency_services',
    ]

    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

        # Policy: Authenticated users can read all rows (for public datasets like infrastructure/emergency)
        # Note: In Supabase, auth.uid() is used for checking the logged-in user.
        # But since FastAPI accesses the DB with a service role, the service role bypasses RLS anyway.
        # RLS is primarily to protect direct Data API access if exposed.
        op.execute(f"""
            CREATE POLICY "Enable read access for authenticated users on {table}" 
            ON {table} FOR SELECT 
            TO authenticated 
            USING (true);
        """)

    # Specific policies for User Profiles (users can only read/update their own profile)
    op.execute("""
        CREATE POLICY "Users can insert their own profile" 
        ON user_profiles FOR INSERT 
        TO authenticated 
        WITH CHECK (id = auth.uid());
    """)
    op.execute("""
        CREATE POLICY "Users can update their own profile" 
        ON user_profiles FOR UPDATE 
        TO authenticated 
        USING (id = auth.uid())
        WITH CHECK (id = auth.uid());
    """)

    # Specific policies for Road Issues (reporters can insert/update their own issues)
    op.execute("""
        CREATE POLICY "Users can insert road issues" 
        ON road_issues FOR INSERT 
        TO authenticated 
        WITH CHECK (reporter_id = auth.uid());
    """)
    op.execute("""
        CREATE POLICY "Users can update their own road issues" 
        ON road_issues FOR UPDATE 
        TO authenticated 
        USING (reporter_id = auth.uid())
        WITH CHECK (reporter_id = auth.uid());
    """)

def downgrade() -> None:
    tables = [
        'user_profiles',
        'road_issues',
        'road_infrastructure',
        'emergency_services',
    ]

    op.execute('DROP POLICY IF EXISTS "Users can insert their own profile" ON user_profiles;')
    op.execute('DROP POLICY IF EXISTS "Users can update their own profile" ON user_profiles;')
    op.execute('DROP POLICY IF EXISTS "Users can insert road issues" ON road_issues;')
    op.execute('DROP POLICY IF EXISTS "Users can update their own road issues" ON road_issues;')

    for table in tables:
        op.execute(f'DROP POLICY IF EXISTS "Enable read access for authenticated users on {table}" ON {table};')
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
