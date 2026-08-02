# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""create challan reference tables

Revision ID: 10002_challan_tables
Revises: 10001_profiles_sos
Create Date: 2026-05-06 00:10:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = '10002_challan_tables'
down_revision = '10001_profiles_sos'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'traffic_violations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('violation_code', sa.String(length=32), nullable=False),
        sa.Column('vehicle_class', sa.String(length=32), nullable=False, server_default='default'),
        sa.Column('section', sa.String(length=80), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('base_fine', sa.Integer(), nullable=False),
        sa.Column('repeat_fine', sa.Integer(), nullable=True),
        sa.Column('aliases', sa.ARRAY(sa.String(length=64)), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('violation_code', 'vehicle_class', name='uq_traffic_violations_code_vehicle'),
    )
    op.create_index('ix_traffic_violations_code', 'traffic_violations', ['violation_code'])
    op.create_index('ix_traffic_violations_vehicle_class', 'traffic_violations', ['vehicle_class'])

    op.create_table(
        'state_fine_overrides',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('state_code', sa.String(length=2), nullable=False),
        sa.Column('violation_code', sa.String(length=32), nullable=False),
        sa.Column('vehicle_class', sa.String(length=32), nullable=True),
        sa.Column('base_fine', sa.Integer(), nullable=False),
        sa.Column('repeat_fine', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(length=80), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('state_code', 'violation_code', 'vehicle_class', name='uq_state_fine_override'),
    )
    op.create_index('ix_state_fine_overrides_state_code', 'state_fine_overrides', ['state_code'])
    op.create_index('ix_state_fine_overrides_violation_code', 'state_fine_overrides', ['violation_code'])

    op.execute("""
        INSERT INTO traffic_violations
            (violation_code, vehicle_class, section, description, base_fine, repeat_fine, aliases)
        VALUES
            ('183', 'two_wheeler', 'Section 183', 'Speeding beyond the notified limit.', 1000, 2000, ARRAY['112/183']),
            ('183', 'light_motor_vehicle', 'Section 183', 'Speeding beyond the notified limit.', 2000, 4000, ARRAY['112/183']),
            ('183', 'heavy_vehicle', 'Section 183', 'Speeding beyond the notified limit.', 4000, 8000, ARRAY['112/183']),
            ('183', 'bus', 'Section 183', 'Speeding beyond the notified limit.', 4000, 8000, ARRAY['112/183']),
            ('183', 'default', 'Section 183', 'Speeding beyond the notified limit.', 2000, 4000, ARRAY['112/183']),
            ('185', 'default', 'Section 185', 'Driving under the influence of alcohol or drugs.', 10000, 15000, ARRAY['DUI','DRUNK']),
            ('181', 'default', 'Section 181', 'Driving without a valid driving licence.', 5000, 10000, ARRAY['3/181']),
            ('194D', 'default', 'Sections 3/181', 'Failure to wear a helmet or seat belt as required.', 1000, 2000, ARRAY['194D-HELMET','194D-SEATBELT']),
            ('194B', 'two_wheeler', 'Section 194B', 'Safety gear non-compliance on a two-wheeler or while carrying a child.', 1000, 2000, ARRAY[]::text[]),
            ('194B', 'light_motor_vehicle', 'Section 194B', 'Safety gear non-compliance on a two-wheeler or while carrying a child.', 1000, 2000, ARRAY[]::text[]),
            ('194B', 'default', 'Section 194B', 'Safety gear non-compliance on a two-wheeler or while carrying a child.', 1000, 2000, ARRAY[]::text[]),
            ('179', 'default', 'Section 179', 'Disobedience, obstruction, or refusal to comply with lawful directions.', 2000, 4000, ARRAY[]::text[])
        ON CONFLICT (violation_code, vehicle_class) DO UPDATE
        SET section = EXCLUDED.section,
            description = EXCLUDED.description,
            base_fine = EXCLUDED.base_fine,
            repeat_fine = EXCLUDED.repeat_fine,
            aliases = EXCLUDED.aliases,
            updated_at = NOW();
    """)

    # Check if 'authenticated' role exists (Supabase-specific)
    # Skip RLS policies if role doesn't exist (e.g., in CI/test environments)
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'")
    )
    if result.fetchone():
        op.execute("ALTER TABLE traffic_violations ENABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE state_fine_overrides ENABLE ROW LEVEL SECURITY;")
        op.execute('DROP POLICY IF EXISTS "Public can read traffic violations" ON traffic_violations;')
        op.execute('DROP POLICY IF EXISTS "Public can read state fine overrides" ON state_fine_overrides;')
        op.execute("""
            CREATE POLICY "Public can read traffic violations"
            ON traffic_violations FOR SELECT
            TO anon, authenticated
            USING (true);
        """)
        op.execute("""
            CREATE POLICY "Public can read state fine overrides"
            ON state_fine_overrides FOR SELECT
            TO anon, authenticated
            USING (true);
        """)
    else:
        # Standard PostgreSQL: create policies without role restriction
        op.execute("ALTER TABLE traffic_violations ENABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE state_fine_overrides ENABLE ROW LEVEL SECURITY;")
        op.execute('DROP POLICY IF EXISTS "Public can read traffic violations" ON traffic_violations;')
        op.execute('DROP POLICY IF EXISTS "Public can read state fine overrides" ON state_fine_overrides;')
        op.execute("""
            CREATE POLICY "Public can read traffic violations"
            ON traffic_violations FOR SELECT
            USING (true);
        """)
        op.execute("""
            CREATE POLICY "Public can read state fine overrides"
            ON state_fine_overrides FOR SELECT
            USING (true);
        """)


def downgrade() -> None:
    op.execute('DROP POLICY IF EXISTS "Public can read state fine overrides" ON state_fine_overrides;')
    op.execute('DROP POLICY IF EXISTS "Public can read traffic violations" ON traffic_violations;')
    op.drop_index('ix_state_fine_overrides_violation_code', table_name='state_fine_overrides')
    op.drop_index('ix_state_fine_overrides_state_code', table_name='state_fine_overrides')
    op.drop_table('state_fine_overrides')
    op.drop_index('ix_traffic_violations_vehicle_class', table_name='traffic_violations')
    op.drop_index('ix_traffic_violations_code', table_name='traffic_violations')
    op.drop_table('traffic_violations')
