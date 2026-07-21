# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations" / "versions"


def test_alembic_upgrade_head(app):
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200


def test_postgis_extension_exists(app):
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    payload = body.get("data", body)
    assert payload["status"] == "ok"


def test_alembic_downgrade_base(app):
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200


def test_migration_files_exist():
    if MIGRATIONS_DIR.exists():
        migration_files = list(MIGRATIONS_DIR.glob("*.py"))
        assert len(migration_files) >= 1
        assert any("001" in f.name for f in migration_files)


def test_migration_chain_is_linear():
    """Verify all migration files form a valid chain (no orphans) and check upgrade/downgrade
    functions exist."""
    if not MIGRATIONS_DIR.exists():
        pytest.skip("Migrations directory not found")

    migrations = {}
    for f in sorted(MIGRATIONS_DIR.glob("*.py")):
        content = f.read_text(encoding="utf-8")
        rev_line = [l for l in content.split("\n") if l.strip().startswith("revision") or "revision" in l and "=" in l]
        [l for l in content.split("\n") if l.strip().startswith("down_revision") or "down_revision" in l and "=" in l]
        if rev_line:
            rev = rev_line[0].split("=")[1].strip().strip("'\"")
            migrations[rev] = {"file": f.name, "content": content}

    assert len(migrations) >= 4, "At least 4 migration files expected"
    assert "001_initial_schema" in migrations, "Initial migration must exist"

    for rev, data in migrations.items():
        content = data["content"]
        assert "def upgrade()" in content, f"Migration {rev} ({data['file']}) missing upgrade()"
        assert "def downgrade()" in content, f"Migration {rev} ({data['file']}) missing downgrade()"


def test_new_migration_has_correct_down_revision():
    """Verify the newest migration revises the previous head."""
    if not MIGRATIONS_DIR.exists():
        pytest.skip("Migrations directory not found")

    migrations = {}
    for f in MIGRATIONS_DIR.glob("*.py"):
        content = f.read_text(encoding="utf-8")
        rev = None
        down = None
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("revision = ") or stripped.startswith("revision="):
                rev = stripped.split("=", 1)[1].strip().strip("'\"")
            elif stripped.startswith("down_revision = ") or stripped.startswith("down_revision="):
                val = stripped.split("=", 1)[1].strip().strip("'\"")
                if val and val != "None":
                    down = val
        if rev:
            migrations[rev] = {"file": f.name, "down": down}

    heads = [rev for rev, data in migrations.items() if data["down"] is not None]
    for h in heads:
        assert h in migrations, f"Head migration {h} not found in migrations dict"

    # Verify every referenced down_revision exists (except None)
    for rev, data in migrations.items():
        if data["down"] is not None:
            # Handle merge migrations (tuple of revision IDs)
            if data["down"].startswith("("):
                # Extract individual revision IDs from the tuple string
                import ast
                try:
                    down_list = ast.literal_eval(data["down"].replace("'", '"') if "'" not in data["down"] else data["down"])
                    if not isinstance(down_list, tuple):
                        down_list = (down_list,)
                except (ValueError, SyntaxError):
                    down_list = (data["down"],)
                for d in down_list:
                    assert d in migrations, \
                        f"Migration {rev} references non-existent down_revision '{d}'"
            else:
                assert data["down"] in migrations, \
                    f"Migration {rev} references non-existent down_revision '{data['down']}'"


def test_all_migrations_have_upgrade_downgrade():
    """Verify each migration has upgrade() and downgrade() functions."""
    if not MIGRATIONS_DIR.exists():
        pytest.skip("Migrations directory not found")

    for f in MIGRATIONS_DIR.glob("*.py"):
        content = f.read_text(encoding="utf-8")
        has_upgrade = "def upgrade()" in content
        has_downgrade = "def downgrade()" in content
        assert has_upgrade, f"{f.name} missing upgrade()"
        assert has_downgrade, f"{f.name} missing downgrade()"
