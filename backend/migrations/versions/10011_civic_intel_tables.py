# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Enterprise Civic Intelligence Platform — 8 new tables.

Revision ID: 10011_civic_intel_tables
Revises: 10010_enterprise_roads
Create Date: 2026-05-23 23:45:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry

revision = '10011_civic_intel_tables'
down_revision = '10010_enterprise_roads'
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
    conn = op.get_bind()

    # 1. lgd_entities — Local Government Directory hierarchy
    if not _table_exists(conn, 'lgd_entities'):
        op.create_table(
            'lgd_entities',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('lgd_code', sa.Integer(), unique=True, nullable=False),
            sa.Column('entity_type', sa.String(32), nullable=False, comment='state, district, subdistrict, block, ulb, gp, village'),
            sa.Column('name_en', sa.Text(), nullable=False),
            sa.Column('name_local', sa.Text(), nullable=True),
            sa.Column('parent_lgd_code', sa.Integer(), nullable=True),
            sa.Column('state_code', sa.String(2), nullable=False),
            sa.Column('census_code_2011', sa.String(16), nullable=True),
            sa.Column('population_census_2011', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('metadata_json', sa.dialects.postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )
        op.create_index('ix_lgd_entities_lgd_code', 'lgd_entities', ['lgd_code'])
        op.create_index('ix_lgd_entities_entity_type', 'lgd_entities', ['entity_type'])
        op.create_index('ix_lgd_entities_state_code', 'lgd_entities', ['state_code'])
        op.create_index('ix_lgd_entities_parent_lgd_code', 'lgd_entities', ['parent_lgd_code'])

    # 2. admin_boundaries — Datameet / India Geodata admin polygons
    if not _table_exists(conn, 'admin_boundaries'):
        op.create_table(
            'admin_boundaries',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('level', sa.String(32), nullable=False, comment='state, district, subdistrict, ward'),
            sa.Column('code', sa.String(32), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('state_code', sa.String(2), nullable=False),
            sa.Column('parent_code', sa.String(32), nullable=True),
            sa.Column('boundary', Geometry('MULTIPOLYGON', srid=4326), nullable=False),
            sa.Column('area_sqkm', sa.Float(), nullable=True),
            sa.Column('centroid_lat', sa.Float(), nullable=True),
            sa.Column('centroid_lon', sa.Float(), nullable=True),
            sa.Column('source', sa.String(32), nullable=False, comment='datameet, india_geodata, manual'),
            sa.Column('source_version', sa.String(64), nullable=True),
            sa.Column('properties_json', sa.dialects.postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )
        op.create_index('ix_admin_boundaries_level', 'admin_boundaries', ['level'])
        op.create_index('ix_admin_boundaries_code', 'admin_boundaries', ['code'])
        op.create_index('ix_admin_boundaries_state_code', 'admin_boundaries', ['state_code'])
        op.create_index('ix_admin_boundaries_boundary', 'admin_boundaries', ['boundary'], postgresql_using='gist')

    # 3. osm_civic_features — OSM civic infrastructure points
    if not _table_exists(conn, 'osm_civic_features'):
        op.create_table(
            'osm_civic_features',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('osm_id', sa.BigInteger(), nullable=False),
            sa.Column('feature_type', sa.String(32), nullable=False, comment='streetlight, traffic_signal, bus_stop, speed_bump, cctv, zebra_crossing, toll_booth'),
            sa.Column('city', sa.String(128), nullable=True),
            sa.Column('district_code', sa.String(32), nullable=True),
            sa.Column('location', Geometry('POINT', srid=4326), nullable=False),
            sa.Column('tags_json', sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column('source_timestamp', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )
        op.create_index('ix_osm_civic_features_osm_id', 'osm_civic_features', ['osm_id'])
        op.create_index('ix_osm_civic_features_feature_type', 'osm_civic_features', ['feature_type'])
        op.create_index('ix_osm_civic_features_city', 'osm_civic_features', ['city'])
        op.create_index('ix_osm_civic_features_location', 'osm_civic_features', ['location'], postgresql_using='gist')

    # 4. gov_datasets — Data.gov.in records
    if not _table_exists(conn, 'gov_datasets'):
        op.create_table(
            'gov_datasets',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('dataset_slug', sa.String(128), nullable=False),
            sa.Column('resource_id', sa.String(128), nullable=False),
            sa.Column('year', sa.Integer(), nullable=True),
            sa.Column('state_code', sa.String(2), nullable=True),
            sa.Column('district_name', sa.Text(), nullable=True),
            sa.Column('data_json', sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column('metric_name', sa.String(128), nullable=True),
            sa.Column('metric_value', sa.Float(), nullable=True),
            sa.Column('unit', sa.String(32), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )
        op.create_index('ix_gov_datasets_dataset_slug', 'gov_datasets', ['dataset_slug'])
        op.create_index('ix_gov_datasets_year', 'gov_datasets', ['year'])
        op.create_index('ix_gov_datasets_state_code', 'gov_datasets', ['state_code'])

    # 5. municipal_features — Municipal GIS features
    if not _table_exists(conn, 'municipal_features'):
        op.create_table(
            'municipal_features',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('municipality', sa.String(32), nullable=False, comment='BMC, GCC, GVMC, BBMP, GHMC, etc.'),
            sa.Column('layer_name', sa.String(128), nullable=False, comment='pothole_repairs, road_works, stormwater_drains, ward_boundaries, etc.'),
            sa.Column('feature_id', sa.String(128), nullable=False),
            sa.Column('geometry', Geometry('GEOMETRY', srid=4326), nullable=False),
            sa.Column('attributes_json', sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column('last_synced', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )
        op.create_index('ix_municipal_features_municipality', 'municipal_features', ['municipality'])
        op.create_index('ix_municipal_features_layer_name', 'municipal_features', ['layer_name'])
        op.create_index('ix_municipal_features_geometry', 'municipal_features', ['geometry'], postgresql_using='gist')

    # 6. grievances — CPGRAMS + state PGRS grievances
    if not _table_exists(conn, 'grievances'):
        op.create_table(
            'grievances',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('source', sa.String(32), nullable=False, comment='cpgrams, tn_pgrs, ap_pgrs, meekosam, ka_cm_helpline, mh_samadhan, up_jansunwai'),
            sa.Column('grievance_ref', sa.String(128), unique=True, nullable=False),
            sa.Column('category', sa.String(32), nullable=False, comment='road_damage, traffic, streetlight, drainage, other'),
            sa.Column('subcategory', sa.String(64), nullable=True),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('complainant_district', sa.Text(), nullable=True),
            sa.Column('state_code', sa.String(2), nullable=True),
            sa.Column('location', Geometry('POINT', srid=4326), nullable=True),
            sa.Column('status', sa.String(32), nullable=False, server_default=sa.text("'pending'")),
            sa.Column('filed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('ministry', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )
        op.create_index('ix_grievances_source', 'grievances', ['source'])
        op.create_index('ix_grievances_category', 'grievances', ['category'])
        op.create_index('ix_grievances_state_code', 'grievances', ['state_code'])
        op.create_index('ix_grievances_location', 'grievances', ['location'], postgresql_using='gist')

    # 7. etl_run_log — ETL audit trail
    if not _table_exists(conn, 'etl_run_log'):
        op.create_table(
            'etl_run_log',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('pipeline_name', sa.String(64), nullable=False),
            sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('status', sa.String(16), nullable=False, server_default=sa.text("'running'"), comment='running, success, partial, failed'),
            sa.Column('records_fetched', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('records_inserted', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('records_updated', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('records_skipped', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.dialects.postgresql.JSONB(), nullable=True),
        )
        op.create_index('ix_etl_run_log_pipeline_name', 'etl_run_log', ['pipeline_name'])

    # 8. municipalities — MeraWard-style directory
    if not _table_exists(conn, 'municipalities'):
        op.create_table(
            'municipalities',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('slug', sa.String(128), unique=True, nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('short_name', sa.String(16), nullable=False),
            sa.Column('municipality_type', sa.String(32), nullable=False, comment='municipal_corporation, municipality, town_panchayat, cantonment_board'),
            sa.Column('city', sa.String(128), nullable=False),
            sa.Column('state_code', sa.String(2), nullable=False),
            sa.Column('state_name', sa.String(64), nullable=False),
            sa.Column('lgd_code', sa.Integer(), nullable=True),
            sa.Column('district_name', sa.Text(), nullable=True),
            # Contact channels
            sa.Column('headquarters_address', sa.Text(), nullable=True),
            sa.Column('helpline_phone', sa.String(20), nullable=True),
            sa.Column('whatsapp_number', sa.String(20), nullable=True),
            sa.Column('email', sa.Text(), nullable=True),
            sa.Column('website_url', sa.Text(), nullable=True),
            sa.Column('app_name', sa.String(64), nullable=True),
            sa.Column('app_url', sa.Text(), nullable=True),
            sa.Column('grievance_portal_url', sa.Text(), nullable=True),
            # Leadership
            sa.Column('mayor_name', sa.Text(), nullable=True),
            sa.Column('mayor_photo_url', sa.Text(), nullable=True),
            sa.Column('commissioner_name', sa.Text(), nullable=True),
            sa.Column('commissioner_phone', sa.String(20), nullable=True),
            # Geo + stats
            sa.Column('ward_count', sa.Integer(), nullable=True),
            sa.Column('population', sa.Integer(), nullable=True),
            sa.Column('area_sqkm', sa.Float(), nullable=True),
            sa.Column('centroid_lat', sa.Float(), nullable=True),
            sa.Column('centroid_lon', sa.Float(), nullable=True),
            sa.Column('boundary', Geometry('MULTIPOLYGON', srid=4326), nullable=True),
            # About
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('services_offered', sa.dialects.postgresql.JSONB(), nullable=True),
            # Metadata
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('data_source', sa.String(64), nullable=True),
            sa.Column('last_verified', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        )
        op.create_index('ix_municipalities_slug', 'municipalities', ['slug'])
        op.create_index('ix_municipalities_municipality_type', 'municipalities', ['municipality_type'])
        op.create_index('ix_municipalities_state_code', 'municipalities', ['state_code'])
        op.create_index('ix_municipalities_lgd_code', 'municipalities', ['lgd_code'])
        op.create_index('ix_municipalities_boundary', 'municipalities', ['boundary'], postgresql_using='gist')


def downgrade() -> None:
    tables = [
        'municipalities', 'etl_run_log', 'grievances', 'municipal_features',
        'gov_datasets', 'osm_civic_features', 'admin_boundaries', 'lgd_entities',
    ]
    conn = op.get_bind()
    for table_name in tables:
        if _table_exists(conn, table_name):
            op.drop_table(table_name)
