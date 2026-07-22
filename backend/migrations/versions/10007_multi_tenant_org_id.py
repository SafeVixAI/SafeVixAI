# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Add org_id column to all tables for multi-tenant isolation.

Phase 0.6: Enables tenant-aware queries and data isolation.
Revision ID: 10007
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "10007"
down_revision = "10006_sos_rls"
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

    # Add org_id to users table (if it exists)
    if _table_exists(conn, "users"):
        if not _column_exists(conn, "users", "org_id"):
            op.add_column("users", sa.Column("org_id", sa.String(36), nullable=True))
        op.create_index("ix_users_org_id", "users", ["org_id"], if_not_exists=True)

    # Add org_id to emergency_services table
    if _table_exists(conn, "emergency_services"):
        if not _column_exists(conn, "emergency_services", "org_id"):
            op.add_column("emergency_services", sa.Column("org_id", sa.String(36), nullable=True))
        op.create_index("ix_emergency_services_org_id", "emergency_services", ["org_id"], if_not_exists=True)

    # Add org_id to road_issues table
    if _table_exists(conn, "road_issues"):
        if not _column_exists(conn, "road_issues", "org_id"):
            op.add_column("road_issues", sa.Column("org_id", sa.String(36), nullable=True))
        op.create_index("ix_road_issues_org_id", "road_issues", ["org_id"], if_not_exists=True)

    # Add org_id to road_infrastructure table
    if _table_exists(conn, "road_infrastructure"):
        if not _column_exists(conn, "road_infrastructure", "org_id"):
            op.add_column("road_infrastructure", sa.Column("org_id", sa.String(36), nullable=True))
        op.create_index("ix_road_infrastructure_org_id", "road_infrastructure", ["org_id"], if_not_exists=True)

    # Add org_id to sos_incidents table
    if _table_exists(conn, "sos_incidents"):
        if not _column_exists(conn, "sos_incidents", "org_id"):
            op.add_column("sos_incidents", sa.Column("org_id", sa.String(36), nullable=True))
        op.create_index("ix_sos_incidents_org_id", "sos_incidents", ["org_id"], if_not_exists=True)

    # Add org_id to user_profiles table
    if _table_exists(conn, "user_profiles"):
        if not _column_exists(conn, "user_profiles", "org_id"):
            op.add_column("user_profiles", sa.Column("org_id", sa.String(36), nullable=True))
        op.create_index("ix_user_profiles_org_id", "user_profiles", ["org_id"], if_not_exists=True)


def downgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "user_profiles"):
        op.drop_index("ix_user_profiles_org_id", table_name="user_profiles", if_exists=True)
        op.drop_column("user_profiles", "org_id")

    if _table_exists(conn, "sos_incidents"):
        op.drop_index("ix_sos_incidents_org_id", table_name="sos_incidents", if_exists=True)
        op.drop_column("sos_incidents", "org_id")

    if _table_exists(conn, "road_infrastructure"):
        op.drop_index("ix_road_infrastructure_org_id", table_name="road_infrastructure", if_exists=True)
        op.drop_column("road_infrastructure", "org_id")

    if _table_exists(conn, "road_issues"):
        op.drop_index("ix_road_issues_org_id", table_name="road_issues", if_exists=True)
        op.drop_column("road_issues", "org_id")

    if _table_exists(conn, "emergency_services"):
        op.drop_index("ix_emergency_services_org_id", table_name="emergency_services", if_exists=True)
        op.drop_column("emergency_services", "org_id")

    if _table_exists(conn, "users"):
        op.drop_index("ix_users_org_id", table_name="users", if_exists=True)
        op.drop_column("users", "org_id")
