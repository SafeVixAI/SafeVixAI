# Update Management System — Deployment Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26

---

## Prerequisites

- Backend running on `:8000` with database migrations applied
- GitHub personal access token (optional, for release sync)
- `$env:SVIX_BACKEND_URL` set for CLI usage

## Migration

```bash
cd backend
alembic upgrade head
```

This creates three tables: `update_releases`, `update_installations`, `update_settings`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_VERSION` | `1.0.0` | Current application version |
| `GITHUB_REPO` | `SafeVixAI/SafeVixAI` | GitHub repo for release sync |
| `SVIX_BACKEND_URL` | `http://localhost:8000` | Backend URL for CLI |

## API Verification

```bash
# Version info
curl http://localhost:8000/api/v1/updates/version

# Check for updates
curl "http://localhost:8000/api/v1/updates/check?channel=stable"

# List channels
curl http://localhost:8000/api/v1/updates/channels

# Get settings
curl http://localhost:8000/api/v1/updates/settings

# Update settings
curl -X PUT http://localhost:8000/api/v1/updates/settings \
  -H "Content-Type: application/json" \
  -d '{"auto_update_enabled": false}'

# Sync from GitHub
curl -X POST http://localhost:8000/api/v1/updates/sync
```

## CLI Usage

```bash
# Python CLI
python scripts/safevixai_update.py check
python scripts/safevixai_update.py version --json
python scripts/safevixai_update.py channels
python scripts/safevixai_update.py install 1.1.0
python scripts/safevixai_update.py history --limit 10
python scripts/safevixai_update.py sync

# PowerShell CLI (Windows)
.\scripts\safevixai-update.ps1 check
.\scripts\safevixai-update.ps1 install 1.1.0
.\scripts\safevixai-update.ps1 history

# Makefile targets
make update-check
make update-sync
make update-history
make backend-migrate
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make update-check` | Check for available updates |
| `make update-download` | Download latest update |
| `make update-install` | Install latest update |
| `make update-rollback` | Rollback to previous version |
| `make update-history` | Show installation history |
| `make update-sync` | Sync releases from GitHub |
| `make backend-migrate` | Run pending database migrations |

## GitHub Release Workflow

The update system integrates with `SafeVixAI/SafeVixAI` GitHub releases:

1. **Create a release** via GitHub UI or CLI
2. **Tag format** determines the channel:
   - `v1.0.0` → stable
   - `v1.1.0-beta.1` → beta
   - `nightly-20260726` → nightly
   - `v2.0.0-rc.1` → pre-release
3. **Run sync**: `make update-sync` or `POST /api/v1/updates/sync`
4. **Verify**: `make update-check` shows the new version
5. **Release notes** are pulled from the GitHub release body

## Frontend Integration

The UpdateBanner component auto-mounts on all pages via the main layout.
The UpdateWidget appears in the dashboard sidebar.
The UpdateSettingsSection appears in Settings > Updates.
