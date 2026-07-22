# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Audit Row-Level Security policies across all SafeVixAI tables.

Usage:
    python backend/scripts/app/audit_rls.py

Requires a live database connection via DATABASE_URL in backend/.env.
"""
import logging
import os
import sys

logger = logging.getLogger(__name__)

TABLES = [
    'user_profiles',
    'road_issues',
    'road_infrastructure',
    'emergency_services',
    'sos_incidents',
    'live_tracking',
    'chat_logs',
    'complaint_events',
    'officers',
    'wards',
]

QUERIES = {
    'rls_enabled': """
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN :tables
          AND rowsecurity = true
        ORDER BY tablename;
    """,
    'rls_disabled': """
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN :tables
          AND (rowsecurity IS NULL OR rowsecurity = false)
        ORDER BY tablename;
    """,
    'policy_count': """
        SELECT relname AS table_name, COUNT(*) AS policy_count
        FROM pg_policies p
        JOIN pg_class c ON p.tablename = c.relname
        WHERE c.relname IN :tables
        GROUP BY relname
        ORDER BY relname;
    """,
    'policy_details': """
        SELECT
            c.relname AS table_name,
            p.policyname,
            p.permissive,
            p.cmd,
            p.qual,
            p.with_check
        FROM pg_policies p
        JOIN pg_class c ON p.tablename = c.relname
        WHERE c.relname IN :tables
        ORDER BY c.relname, p.policyname;
    """,
}


def run_audit():
    try:
        import sqlalchemy as sa
    except ImportError:
        print("FAIL: sqlalchemy not installed")
        sys.exit(1)

    # Load environment variables from .env
    from pathlib import Path
    try:
        import dotenv
        env_paths = [
            Path(__file__).resolve().parents[2] / ".env",
            Path.cwd() / "backend" / ".env",
            Path.cwd() / ".env"
        ]
        for p in env_paths:
            if p.exists():
                dotenv.load_dotenv(p)
                break
    except ImportError:
        logger.debug("Suppressed exception", exc_info=True)

    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("FAIL: DATABASE_URL not set")
        sys.exit(1)

    # Replace async pg driver with sync driver for sqlalchemy sync engine
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    if "?" in url:
        url = url.split("?")[0]

    engine = sa.create_engine(url)
    with engine.connect() as conn:
        tables_param = sa.bindparam("tables", value=TABLES, expanding=True)

        enabled = conn.execute(
            sa.text(QUERIES["rls_enabled"]).bindparams(tables_param)
        ).fetchall()
        disabled = conn.execute(
            sa.text(QUERIES["rls_disabled"]).bindparams(tables_param)
        ).fetchall()
        policy_counts = conn.execute(
            sa.text(QUERIES["policy_count"]).bindparams(tables_param)
        ).fetchall()
        policy_details = conn.execute(
            sa.text(QUERIES["policy_details"]).bindparams(tables_param)
        ).fetchall()

    print("=" * 60)
    print("SafeVixAI RLS AUDIT REPORT")
    print("=" * 60)

    print(f"\nTables with RLS enabled ({len(enabled)}):")
    for (t,) in enabled:
        print(f"  [OK] {t}")

    print(f"\nTables with RLS disabled ({len(disabled)}):")
    for (t,) in disabled:
        print(f"  [X] {t}")

    print("\nPolicy counts:")
    counts = dict.fromkeys(TABLES, 0)
    for t, c in policy_counts:
        counts[t] = c
    for t in TABLES:
        status = f"{counts[t]} policies" if counts[t] else "NO POLICIES"
        mark = "[OK]" if counts[t] else "[X]"
        print(f"  {mark} {t}: {status}")

    print("\nPolicy details:")
    for t, name, permissive, cmd, qual, wc in policy_details:
        print(f"  [{t}] {name} ({cmd})")
        if qual:
            print(f"    USING: {qual[:120]}")
        if wc:
            print(f"    CHECK: {wc[:120]}")

    print("\n" + "=" * 60)

    total_tables = len(TABLES)
    rls_ok = len(enabled)
    all_policies = all(counts.get(t, 0) > 0 for t in TABLES)

    if rls_ok == total_tables and all_policies:
        print(f"RESULT: PASS ({rls_ok}/{total_tables} tables with RLS + policies)")
        return 0
    else:
        print(f"RESULT: FAIL ({rls_ok}/{total_tables} tables with RLS)")
        if not all_policies:
            missing = [t for t in TABLES if counts.get(t, 0) == 0]
            print(f"  Tables missing policies: {', '.join(missing)}")
        return 1


if __name__ == "__main__":
    sys.exit(run_audit())
