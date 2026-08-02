# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""add privacy retention cleanup function

Revision ID: 10005_data_retention
Revises: 10004_chat_logs_vector
Create Date: 2026-05-16 00:05:00.000000
"""

from alembic import op

revision = '10005_data_retention'
down_revision = '10004_chat_logs_vector'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.safevixai_cleanup_expired_data()
        RETURNS void
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        BEGIN
          IF to_regclass('public.live_tracking') IS NOT NULL THEN
            DELETE FROM public.live_tracking
            WHERE updated_at < NOW() - INTERVAL '30 days'
               OR expires_at < NOW() - INTERVAL '7 days';
          END IF;

          IF to_regclass('public.chat_logs') IS NOT NULL THEN
            DELETE FROM public.chat_logs
            WHERE created_at < NOW() - INTERVAL '90 days';
          END IF;

          IF to_regclass('public.sos_incidents') IS NOT NULL THEN
            DELETE FROM public.sos_incidents
            WHERE created_at < NOW() - INTERVAL '1 year';
          END IF;
        END;
        $$;
        """
    )


def downgrade() -> None:
    op.execute('DROP FUNCTION IF EXISTS public.safevixai_cleanup_expired_data()')
