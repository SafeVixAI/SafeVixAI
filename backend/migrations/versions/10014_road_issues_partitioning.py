# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Enterprise range partitioning for road_issues table.

Revision ID: 10014_road_issues_partitioning
Revises: 10013_officer_gist_index
Create Date: 2026-05-28 22:15:00.000000
"""

from __future__ import annotations

from alembic import op

revision = '10014_road_issues_partitioning'
down_revision = '10013_officer_gist_index'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Implement PostgreSQL range partitioning on road_issues by created_at."""
    op.execute(
        """
        DO $$
        BEGIN
            -- 1. Create a partitioned table with composite primary key (id, created_at)
            CREATE TABLE IF NOT EXISTS public.road_issues_partitioned (
                id SERIAL,
                org_id VARCHAR(36),
                uuid UUID NOT NULL,
                issue_type VARCHAR(64) NOT NULL,
                severity INTEGER NOT NULL,
                description TEXT,
                location geometry(Point, 4326),
                location_address TEXT,
                road_name TEXT,
                road_type VARCHAR(64),
                road_number VARCHAR(64),
                photo_url TEXT,
                ai_detection JSONB,
                reporter_id UUID,
                authority_name TEXT,
                authority_phone VARCHAR(64),
                authority_email TEXT,
                complaint_ref VARCHAR(128),
                status VARCHAR(32) DEFAULT 'open',
                status_updated TIMESTAMP WITHOUT TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                category VARCHAR(32) DEFAULT 'roads',
                sub_category VARCHAR(64),
                ward_id VARCHAR(64),
                ward_name TEXT,
                assigned_officer_id UUID,
                sla_deadline TIMESTAMP WITHOUT TIME ZONE,
                resolved_at TIMESTAMP WITHOUT TIME ZONE,
                duplicate_of_uuid UUID,
                citizen_phone VARCHAR(20),
                confirmation_count INTEGER DEFAULT 0,
                before_photo_url TEXT,
                after_photo_url TEXT,
                ai_confidence FLOAT,
                ai_model_version VARCHAR(32),
                escalation_tier INTEGER DEFAULT 0,
                accepted_at TIMESTAMP WITHOUT TIME ZONE,
                accepted_by UUID,
                work_started_at TIMESTAMP WITHOUT TIME ZONE,
                citizen_confirmed_at TIMESTAMP WITHOUT TIME ZONE,
                citizen_rating INTEGER,
                department VARCHAR(64),
                rejection_reason TEXT,
                reopen_count INTEGER DEFAULT 0,
                PRIMARY KEY (id, created_at)
            ) PARTITION BY RANGE (created_at);

            -- 2. Create the default partition to handle all historical and fallback ranges
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c 
                JOIN pg_namespace n ON n.oid = c.relnamespace 
                WHERE c.relname = 'road_issues_default' AND n.nspname = 'public'
            ) THEN
                CREATE TABLE public.road_issues_default PARTITION OF public.road_issues_partitioned DEFAULT;
            END IF;

            -- 3. Copy existing records from old table to new partitioned table (if old table exists)
            IF to_regclass('public.road_issues') IS NOT NULL AND to_regclass('public.road_issues_old') IS NULL THEN
                -- Temporary disable triggers/RLS during data load
                ALTER TABLE public.road_issues DISABLE TRIGGER ALL;
                
                -- List columns explicitly to avoid position mismatch from ALTER TABLE ADD COLUMN
                INSERT INTO public.road_issues_partitioned (
                    id, org_id, uuid, issue_type, severity, description,
                    location, location_address, road_name, road_type, road_number,
                    photo_url, ai_detection, reporter_id, authority_name,
                    authority_phone, authority_email, complaint_ref, status,
                    status_updated, created_at, category, sub_category, ward_id,
                    ward_name, assigned_officer_id, sla_deadline, resolved_at,
                    duplicate_of_uuid, citizen_phone, confirmation_count,
                    before_photo_url, after_photo_url, ai_confidence,
                    ai_model_version, escalation_tier, accepted_at, accepted_by,
                    work_started_at, citizen_confirmed_at, citizen_rating,
                    department, rejection_reason, reopen_count
                )
                SELECT
                    id, org_id, uuid::uuid, issue_type, severity, description,
                    location, location_address, road_name, road_type, road_number,
                    photo_url, ai_detection, reporter_id, authority_name,
                    authority_phone, authority_email, complaint_ref, status,
                    status_updated, created_at, category, sub_category, ward_id,
                    ward_name, assigned_officer_id, sla_deadline, resolved_at,
                    duplicate_of_uuid, citizen_phone, confirmation_count,
                    before_photo_url, after_photo_url, ai_confidence,
                    ai_model_version, escalation_tier, accepted_at, accepted_by,
                    work_started_at, citizen_confirmed_at, citizen_rating,
                    department, rejection_reason, reopen_count
                FROM public.road_issues 
                ON CONFLICT (id, created_at) DO NOTHING;
                
                ALTER TABLE public.road_issues ENABLE TRIGGER ALL;

                -- 4. Swap tables atomically inside the DO block transaction
                ALTER TABLE public.road_issues RENAME TO road_issues_old;
                ALTER TABLE public.road_issues_partitioned RENAME TO road_issues;

                -- 5. Re-create spatial index on active table
                CREATE INDEX IF NOT EXISTS ix_road_issues_location_gist 
                ON public.road_issues USING gist (location);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Downgrade and restore unpartitioned road_issues table."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Swap back if backup exists
            IF to_regclass('public.road_issues_old') IS NOT NULL THEN
                DROP TABLE IF EXISTS public.road_issues;
                ALTER TABLE public.road_issues_old RENAME TO road_issues;
                DROP TABLE IF EXISTS public.road_issues_partitioned;
            END IF;
        END $$;
        """
    )
