# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Enterprise Roads, Traffic, and Streetlights expansion.

Revision ID: 10010_enterprise_roads
Revises: 10009_sos_retention
Create Date: 2026-05-23 15:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry

revision = '10010_enterprise_roads'
down_revision = '10009_sos_retention'
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


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    result = conn.execute(
        sa.text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = :table_name AND column_name = :column_name
        """),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Add new columns to road_issues table
    if _table_exists(conn, "road_issues"):
        if not _column_exists(conn, "road_issues", "category"):
            op.add_column("road_issues", sa.Column("category", sa.String(32), server_default="roads", nullable=False))
        if not _column_exists(conn, "road_issues", "sub_category"):
            op.add_column("road_issues", sa.Column("sub_category", sa.String(64), nullable=True))
        if not _column_exists(conn, "road_issues", "ward_id"):
            op.add_column("road_issues", sa.Column("ward_id", sa.String(64), nullable=True))
        if not _column_exists(conn, "road_issues", "ward_name"):
            op.add_column("road_issues", sa.Column("ward_name", sa.Text(), nullable=True))
        if not _column_exists(conn, "road_issues", "assigned_officer_id"):
            op.add_column("road_issues", sa.Column("assigned_officer_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        if not _column_exists(conn, "road_issues", "sla_deadline"):
            op.add_column("road_issues", sa.Column("sla_deadline", sa.DateTime(), nullable=True))
        if not _column_exists(conn, "road_issues", "resolved_at"):
            op.add_column("road_issues", sa.Column("resolved_at", sa.DateTime(), nullable=True))
        if not _column_exists(conn, "road_issues", "duplicate_of_uuid"):
            op.add_column("road_issues", sa.Column("duplicate_of_uuid", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        if not _column_exists(conn, "road_issues", "citizen_phone"):
            op.add_column("road_issues", sa.Column("citizen_phone", sa.String(20), nullable=True))
        if not _column_exists(conn, "road_issues", "confirmation_count"):
            op.add_column("road_issues", sa.Column("confirmation_count", sa.Integer(), server_default="0", nullable=False))
        if not _column_exists(conn, "road_issues", "before_photo_url"):
            op.add_column("road_issues", sa.Column("before_photo_url", sa.Text(), nullable=True))
        if not _column_exists(conn, "road_issues", "after_photo_url"):
            op.add_column("road_issues", sa.Column("after_photo_url", sa.Text(), nullable=True))
        if not _column_exists(conn, "road_issues", "ai_confidence"):
            op.add_column("road_issues", sa.Column("ai_confidence", sa.Float(), nullable=True))
        if not _column_exists(conn, "road_issues", "ai_model_version"):
            op.add_column("road_issues", sa.Column("ai_model_version", sa.String(32), nullable=True))

        # Add index on category
        op.create_index("ix_road_issues_category", "road_issues", ["category"], if_not_exists=True)
        # Add index on ward_id
        op.create_index("ix_road_issues_ward_id", "road_issues", ["ward_id"], if_not_exists=True)

    # 2. Create wards table
    if not _table_exists(conn, "wards"):
        op.create_table(
            "wards",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("org_id", sa.String(36), nullable=True),
            sa.Column("ward_id", sa.String(64), unique=True, nullable=False),
            sa.Column("ward_name", sa.Text(), nullable=False),
            sa.Column("zone_name", sa.Text(), nullable=True),
            sa.Column("city", sa.Text(), nullable=True),
            sa.Column("state_code", sa.String(2), nullable=True),
            sa.Column("boundary", Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=False),
            sa.Column("officer_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("population", sa.Integer(), nullable=True),
            sa.Column("area_sqkm", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
        )
        op.create_index("ix_wards_ward_id", "wards", ["ward_id"], unique=True)
        op.create_index("ix_wards_org_id", "wards", ["org_id"])

    # 3. Create officers table
    if not _table_exists(conn, "officers"):
        op.create_table(
            "officers",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("org_id", sa.String(36), nullable=True),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("phone", sa.String(20), nullable=True),
            sa.Column("email", sa.Text(), nullable=True),
            sa.Column("role", sa.String(32), server_default="field_officer", nullable=False),
            sa.Column("ward_id", sa.String(64), nullable=True),
            sa.Column("department", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("last_checkin", sa.DateTime(), nullable=True),
            sa.Column("last_location", Geometry(geometry_type="POINT", srid=4326), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
        )
        op.create_index("ix_officers_org_id", "officers", ["org_id"])
        op.create_index("ix_officers_ward_id", "officers", ["ward_id"])

    # 4. Create complaint_events table
    if not _table_exists(conn, "complaint_events"):
        op.create_table(
            "complaint_events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("org_id", sa.String(36), nullable=True),
            sa.Column("complaint_uuid", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("event_type", sa.String(32), nullable=False),
            sa.Column("actor_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("actor_role", sa.String(32), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("event_metadata", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
        )
        op.create_index("ix_complaint_events_complaint_uuid", "complaint_events", ["complaint_uuid"])
        op.create_index("ix_complaint_events_org_id", "complaint_events", ["org_id"])


def downgrade() -> None:
    conn = op.get_bind()

    # 1. Drop complaint_events table
    if _table_exists(conn, "complaint_events"):
        op.drop_table("complaint_events")

    # 2. Drop officers table
    if _table_exists(conn, "officers"):
        op.drop_table("officers")

    # 3. Drop wards table
    if _table_exists(conn, "wards"):
        op.drop_table("wards")

    # 4. Drop columns from road_issues table
    if _table_exists(conn, "road_issues"):
        op.drop_index("ix_road_issues_category", table_name="road_issues", if_exists=True)
        op.drop_index("ix_road_issues_ward_id", table_name="road_issues", if_exists=True)

        columns_to_drop = [
            "category", "sub_category", "ward_id", "ward_name",
            "assigned_officer_id", "sla_deadline", "resolved_at",
            "duplicate_of_uuid", "citizen_phone", "confirmation_count",
            "before_photo_url", "after_photo_url", "ai_confidence",
            "ai_model_version"
        ]
        for col in columns_to_drop:
            if _column_exists(conn, "road_issues", col):
                op.drop_column("road_issues", col)
