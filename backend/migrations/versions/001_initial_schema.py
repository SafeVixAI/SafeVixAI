# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Initial map schema.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-04-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')

    op.create_table(
        'emergency_services',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('osm_id', sa.BigInteger(), nullable=True, unique=True),
        sa.Column('osm_type', sa.String(length=32), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('name_local', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=32), nullable=False),
        sa.Column('sub_category', sa.String(length=64), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=64), nullable=True),
        sa.Column('phone_emergency', sa.String(length=64), nullable=True),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('location', Geometry(geometry_type='POINT', srid=4326, spatial_index=False), nullable=False),
        sa.Column('city', sa.String(length=128), nullable=True),
        sa.Column('district', sa.String(length=128), nullable=True),
        sa.Column('state', sa.String(length=128), nullable=True),
        sa.Column('state_code', sa.String(length=2), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=False, server_default='IN'),
        sa.Column('is_24hr', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('has_trauma', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('has_icu', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('bed_count', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('source', sa.String(length=32), nullable=False, server_default='overpass'),
        sa.Column('raw_tags', sa.JSON(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_emergency_services_category', 'emergency_services', ['category'])
    op.create_index('ix_emergency_services_state_code', 'emergency_services', ['state_code'])
    op.create_index('ix_emergency_services_country_code', 'emergency_services', ['country_code'])
    op.create_index(
        'ix_emergency_services_location_gist',
        'emergency_services',
        ['location'],
        postgresql_using='gist',
    )

    op.create_table(
        'road_infrastructure',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('road_id', sa.String(length=128), nullable=False, unique=True),
        sa.Column('road_name', sa.Text(), nullable=True),
        sa.Column('road_type', sa.String(length=64), nullable=True),
        sa.Column('road_number', sa.String(length=64), nullable=True),
        sa.Column('length_km', sa.Float(), nullable=True),
        sa.Column('geometry', Geometry(geometry_type='LINESTRING', srid=4326, spatial_index=False), nullable=False),
        sa.Column('state_code', sa.String(length=2), nullable=True),
        sa.Column('contractor_name', sa.Text(), nullable=True),
        sa.Column('exec_engineer', sa.Text(), nullable=True),
        sa.Column('exec_engineer_phone', sa.String(length=64), nullable=True),
        sa.Column('budget_sanctioned', sa.BigInteger(), nullable=True),
        sa.Column('budget_spent', sa.BigInteger(), nullable=True),
        sa.Column('construction_date', sa.Date(), nullable=True),
        sa.Column('last_relayed_date', sa.Date(), nullable=True),
        sa.Column('next_maintenance', sa.Date(), nullable=True),
        sa.Column('project_source', sa.String(length=64), nullable=True),
        sa.Column('data_source_url', sa.Text(), nullable=True),
    )
    op.create_index('ix_road_infrastructure_state_code', 'road_infrastructure', ['state_code'])
    op.create_index(
        'ix_road_infrastructure_geometry_gist',
        'road_infrastructure',
        ['geometry'],
        postgresql_using='gist',
    )

    op.create_table(
        'road_issues',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('issue_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', Geometry(geometry_type='POINT', srid=4326, spatial_index=False), nullable=False),
        sa.Column('location_address', sa.Text(), nullable=True),
        sa.Column('road_name', sa.Text(), nullable=True),
        sa.Column('road_type', sa.String(length=64), nullable=True),
        sa.Column('road_number', sa.String(length=64), nullable=True),
        sa.Column('photo_url', sa.Text(), nullable=True),
        sa.Column('ai_detection', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('authority_name', sa.Text(), nullable=True),
        sa.Column('authority_phone', sa.String(length=64), nullable=True),
        sa.Column('authority_email', sa.Text(), nullable=True),
        sa.Column('complaint_ref', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='open'),
        sa.Column('status_updated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index(
        'ix_road_issues_location_gist',
        'road_issues',
        ['location'],
        postgresql_using='gist',
    )
    op.create_index('ix_road_issues_status', 'road_issues', ['status'])


def downgrade() -> None:
    op.drop_index('ix_road_issues_status', table_name='road_issues')
    op.drop_index('ix_road_issues_location_gist', table_name='road_issues')
    op.drop_table('road_issues')

    op.drop_index('ix_road_infrastructure_geometry_gist', table_name='road_infrastructure')
    op.drop_index('ix_road_infrastructure_state_code', table_name='road_infrastructure')
    op.drop_table('road_infrastructure')

    op.drop_index('ix_emergency_services_location_gist', table_name='emergency_services')
    op.drop_index('ix_emergency_services_country_code', table_name='emergency_services')
    op.drop_index('ix_emergency_services_state_code', table_name='emergency_services')
    op.drop_index('ix_emergency_services_category', table_name='emergency_services')
    op.drop_table('emergency_services')
