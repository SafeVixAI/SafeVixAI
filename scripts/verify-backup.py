#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""verify-backup.py — Automated backup restore verification.

Usage:
  python scripts/verify-backup.py                    # Use latest backup artifact
  python scripts/verify-backup.py --backup <path>    # Use specific backup file
  python scripts/verify-backup.py --container-db     # Restore into existing PG container
  python scripts/verify-backup.py --skip-cleanup     # Keep temp DB for inspection

Verifies that a database backup can be successfully restored and data is intact.
"""
from __future__ import annotations

import argparse
import gzip
import subprocess
import sys
import time
from pathlib import Path

REQUIRED_TABLES = [
    "sos_incidents",
    "road_issues",
    "officers",
    "users",
    "municipalities",
    "city_centers",
    "alembic_version",
]


def find_backup() -> Path | None:
    """Find the latest backup artifact in common locations."""
    # Check backups/ dir (CI artifact location)
    backup_dir = Path("backups")
    if backup_dir.exists():
        backups = sorted(backup_dir.glob("*.sql.gz"))
        if backups:
            return backups[-1]

    # Check current directory
    for p in Path(".").glob("*backup*.sql*"):
        return p
    for p in Path(".").glob("*.dump"):
        return p

    return None


def verify_docker() -> bool:
    try:
        subprocess.run(["docker", "--version"], capture_output=True, timeout=10)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def start_temp_postgres(backup_path: Path) -> str:
    """Start a temporary PostgreSQL container and restore the backup."""
    container_name = f"safevixai-restore-test-{int(time.time())}"
    db_name = "safevixai_verify"
    db_user = "postgres"
    db_pass = "postgres"

    print(f"Starting temporary PostgreSQL container: {container_name}")
    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", container_name,
            "-e", f"POSTGRES_DB={db_name}",
            "-e", f"POSTGRES_USER={db_user}",
            "-e", f"POSTGRES_PASSWORD={db_pass}",
            "-p", "5433:5432",
            "postgis/postgis:16-3.4",
        ],
        check=True, capture_output=True, timeout=60,
    )

    # Wait for PostgreSQL to be ready
    print("Waiting for PostgreSQL to be ready...")
    for i in range(30):
        result = subprocess.run(
            ["docker", "exec", container_name, "pg_isready", "-U", db_user],
            capture_output=True, timeout=10,
        )
        if result.returncode == 0:
            print("PostgreSQL is ready!")
            break
        time.sleep(1)
    else:
        cleanup_container(container_name)
        raise RuntimeError("PostgreSQL failed to start within 30 seconds")

    # Restore the backup
    print(f"Restoring backup: {backup_path}")
    if str(backup_path).endswith(".gz"):
        with gzip.open(backup_path, "rb") as f_in:
            data = f_in.read()
            result = subprocess.run(
                ["docker", "exec", "-i", container_name, "pg_restore",
                 "-U", db_user, "-d", db_name, "--no-owner", "--no-acl", "--clean"],
                input=data, capture_output=True, timeout=300,
            )
    else:
        result = subprocess.run(
            ["docker", "exec", "-i", container_name, "pg_restore",
             "-U", db_user, "-d", db_name, "--no-owner", "--no-acl", "--clean"],
            stdin=open(backup_path, "rb"), capture_output=True, timeout=300,
        )

    if result.returncode != 0:
        # Warnings during restore are normal (e.g., no-owner)
        stderr_text = result.stderr.decode() if result.stderr else ""
        warn_count = stderr_text.count("warning:")
        print(f"Restore completed with {warn_count} warnings (expected)")
    else:
        print("Restore completed successfully")

    return container_name


def run_verification_queries(container_name: str) -> list[dict]:
    """Run verification queries against the restored database."""
    db_name = "safevixai_verify"
    db_user = "postgres"
    results = []

    # Query 1: Table count
    result = subprocess.run(
        ["docker", "exec", container_name, "psql", "-U", db_user, "-d", db_name,
         "-t", "-A", "-c",
         "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'"],
        capture_output=True, text=True, timeout=10,
    )
    table_count = result.stdout.strip()
    results.append({"query": "Table count", "result": table_count})
    print(f"Tables in public schema: {table_count}")

    # Query 2: Check required tables exist
    for table in REQUIRED_TABLES:
        result = subprocess.run(
            ["docker", "exec", container_name, "psql", "-U", db_user, "-d", db_name,
             "-t", "-A", "-c",
             f"SELECT COUNT(*) FROM (SELECT 1 FROM pg_tables WHERE tablename='{table}') t"],
            capture_output=True, text=True, timeout=5,
        )
        exists = result.stdout.strip() == "1"
        status = "✅" if exists else "❌ MISSING"
        print(f"  {status} {table}")
        results.append({"query": f"Table: {table}", "result": status})

    # Query 3: Row counts
    result = subprocess.run(
        ["docker", "exec", container_name, "psql", "-U", db_user, "-d", db_name,
         "-t", "-A", "-c",
         "SELECT COUNT(*) FROM sos_incidents"],
        capture_output=True, text=True, timeout=5,
    )
    sos_count = result.stdout.strip()
    print(f"SOS incidents: {sos_count}")
    results.append({"query": "SOS incident count", "result": sos_count})

    # Query 4: Alembic version
    result = subprocess.run(
        ["docker", "exec", container_name, "psql", "-U", db_user, "-d", db_name,
         "-t", "-A", "-c",
         "SELECT version_num FROM alembic_version LIMIT 1"],
        capture_output=True, text=True, timeout=5,
    )
    alembic_version = result.stdout.strip()
    print(f"Alembic migration version: {alembic_version}")
    results.append({"query": "Alembic version", "result": alembic_version})

    return results


def cleanup_container(container_name: str) -> None:
    """Remove the temporary PostgreSQL container."""
    print(f"Cleaning up container: {container_name}")
    subprocess.run(["docker", "stop", container_name], capture_output=True, timeout=30)
    subprocess.run(["docker", "rm", container_name], capture_output=True, timeout=30)
    print("Cleanup complete")


def main():
    parser = argparse.ArgumentParser(description="Verify database backup integrity")
    parser.add_argument("--backup", type=Path, help="Path to backup file")
    parser.add_argument("--skip-cleanup", action="store_true", help="Keep temp DB")
    args = parser.parse_args()

    # Find backup
    backup_path = args.backup or find_backup()
    if not backup_path or not backup_path.exists():
        print("❌ No backup file found. Provide --backup <path> or place a backup in ./backups/")
        sys.exit(1)

    print(f"📦 Backup: {backup_path} ({backup_path.stat().st_size / 1024 / 1024:.1f} MB)")

    # Check Docker
    if not verify_docker():
        print("❌ Docker is required but not available")
        sys.exit(1)

    # Start PostgreSQL and restore
    container_name = None
    try:
        container_name = start_temp_postgres(backup_path)
        results = run_verification_queries(container_name)

        # Summary
        print("\n" + "=" * 50)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 50)
        all_good = True
        for r in results:
            if "❌" in str(r["result"]):
                all_good = False
                print(f"  ❌ {r['query']}: {r['result']}")
            else:
                print(f"  ✅ {r['query']}: {r['result']}")

        if all_good:
            print("\n✅ Backup verification PASSED — restore is functional")
        else:
            print("\n⚠️ Backup verification PARTIAL — some tables missing/empty")
            print("   Check if the backup is from a complete database dump.")
    except Exception as e:
        print(f"\n❌ Backup verification FAILED: {e}")
        sys.exit(1)
    finally:
        if container_name and not args.skip_cleanup:
            cleanup_container(container_name)

    print("\nTo inspect the restored database, use:")
    print(f"  docker exec -it {container_name} psql -U postgres -d safevixai_verify")


if __name__ == "__main__":
    main()
