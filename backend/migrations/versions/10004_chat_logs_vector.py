# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""create first aid articles, chat logs, and pgvector support

Revision ID: 10004_chat_logs_vector
Revises: 10003_rls_alignment
Create Date: 2026-05-16 00:00:00.000000
"""

from alembic import op
from sqlalchemy import text

revision = '10004_chat_logs_vector'
down_revision = '10003_rls_alignment'
branch_labels = None
depends_on = None


def _execute_statements(sql: str) -> None:
    for stmt in sql.split(';'):
        stmt_clean = stmt.strip()
        if stmt_clean:
            lines = [line for line in stmt_clean.splitlines() if not line.strip().startswith('--')]
            stmt_clean = '\n'.join(lines).strip()
            if stmt_clean:
                op.execute(stmt_clean)


def upgrade() -> None:
    # Check if pgvector extension is available on this PostgreSQL instance
    conn = op.get_bind()
    has_vector = False
    try:
        result = conn.execute(
            text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
        )
        if result.fetchone():
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            has_vector = True
    except Exception as exc:
        # pgvector not available — tables will use BYTEA fallback for embeddings
        import sys
        print(f"pgvector check failed (falling back to BYTEA): {exc}", file=sys.stderr)

    # Choose embedding column type based on pgvector availability
    embedding_col = 'vector(384)' if has_vector else 'BYTEA'

    # Check if 'authenticated' role exists (Supabase-specific)
    result = conn.execute(
        text("SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'")
    )
    is_supabase = result.fetchone() is not None

    if is_supabase:
        _execute_statements(
            f"""
            CREATE TABLE IF NOT EXISTS public.first_aid_articles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en',
                summary TEXT,
                body TEXT NOT NULL,
                source_url TEXT,
                embedding {embedding_col},
                is_published BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS ix_first_aid_articles_category
                ON public.first_aid_articles (category);
            CREATE INDEX IF NOT EXISTS ix_first_aid_articles_language
                ON public.first_aid_articles (language);

            ALTER TABLE public.first_aid_articles ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read first aid articles" ON public.first_aid_articles;
            CREATE POLICY "Public can read first aid articles"
                ON public.first_aid_articles FOR SELECT
                TO anon, authenticated
                USING (is_published = TRUE);
            """
        )

        _execute_statements(
            """
            CREATE TABLE IF NOT EXISTS public.chat_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id TEXT NOT NULL,
                user_id TEXT,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                intent TEXT,
                sources JSONB NOT NULL DEFAULT '[]'::jsonb,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS ix_chat_logs_session_id
                ON public.chat_logs (session_id);
            CREATE INDEX IF NOT EXISTS ix_chat_logs_user_id
                ON public.chat_logs (user_id);
            CREATE INDEX IF NOT EXISTS ix_chat_logs_created_at
                ON public.chat_logs (created_at DESC);

            ALTER TABLE public.chat_logs ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Users can read own chat logs" ON public.chat_logs;
            DROP POLICY IF EXISTS "Users can insert own chat logs" ON public.chat_logs;
            CREATE POLICY "Users can read own chat logs"
                ON public.chat_logs FOR SELECT
                TO authenticated
                USING (user_id = auth.uid()::text);
            CREATE POLICY "Users can insert own chat logs"
                ON public.chat_logs FOR INSERT
                TO authenticated
                WITH CHECK (user_id = auth.uid()::text);
            """
        )
    else:
        # Standard PostgreSQL: create tables without Supabase-specific RLS
        _execute_statements(
            f"""
            CREATE TABLE IF NOT EXISTS public.first_aid_articles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en',
                summary TEXT,
                body TEXT NOT NULL,
                source_url TEXT,
                embedding {embedding_col},
                is_published BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS ix_first_aid_articles_category
                ON public.first_aid_articles (category);
            CREATE INDEX IF NOT EXISTS ix_first_aid_articles_language
                ON public.first_aid_articles (language);

            ALTER TABLE public.first_aid_articles ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Public can read first aid articles" ON public.first_aid_articles;
            CREATE POLICY "Public can read first aid articles"
                ON public.first_aid_articles FOR SELECT
                USING (is_published = TRUE);
            """
        )

        _execute_statements(
            """
            CREATE TABLE IF NOT EXISTS public.chat_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id TEXT NOT NULL,
                user_id TEXT,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                intent TEXT,
                sources JSONB NOT NULL DEFAULT '[]'::jsonb,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS ix_chat_logs_session_id
                ON public.chat_logs (session_id);
            CREATE INDEX IF NOT EXISTS ix_chat_logs_user_id
                ON public.chat_logs (user_id);
            CREATE INDEX IF NOT EXISTS ix_chat_logs_created_at
                ON public.chat_logs (created_at DESC);

            -- Skip RLS policies for chat_logs in standard PostgreSQL
            -- Backend access control handles authorization
            """
        )


def downgrade() -> None:
    op.execute('DROP POLICY IF EXISTS "Users can insert own chat logs" ON public.chat_logs')
    op.execute('DROP POLICY IF EXISTS "Users can read own chat logs" ON public.chat_logs')
    op.execute('DROP TABLE IF EXISTS public.chat_logs')
    op.execute('DROP POLICY IF EXISTS "Public can read first aid articles" ON public.first_aid_articles')
    op.execute('DROP TABLE IF EXISTS public.first_aid_articles')
    op.execute('DROP EXTENSION IF EXISTS vector')
