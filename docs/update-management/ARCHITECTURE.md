# Update Management System — Architecture

> **Version:** 1.0  
> **Last updated:** 2026-07-26

---

## Overview

The Update Management System provides enterprise-grade software update capabilities across four interfaces:

| Interface | Primary Audience | Key Features |
|-----------|-----------------|--------------|
| **API** | Internal services, CI/CD | Version check, download, install, rollback, history |
| **Frontend** | End users, operators | Update banner, dashboard widget, settings page |
| **CLI** | DevOps, administrators | Check, download, install, rollback, automate |
| **GitHub Releases** | Open-source community | Artifact hosting, release notes, channel management |

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        GitHub Releases                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Stable  │  │   Beta   │  │  Nightly │  │   Pre-release    │ │
│  │ Channel  │  │ Channel  │  │ Channel  │  │    Channel       │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────┘ │
│       └──────────────┴─────────────┴────────────────┘            │
└──────────────────────────────┬───────────────────────────────────┘
                               │ GitHub API
┌──────────────────────────────▼───────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              UpdateService Layer                          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │    │
│  │  │ Release  │ │ Version  │ │ Download │ │ Signature  │  │    │
│  │  │ Fetcher  │ │ Checker  │ │ Manager  │ │ Verifier   │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │    │
│  │  │ Install  │ │ Rollback │ │ Scheduler│ │ Notifica-  │  │    │
│  │  │ Manager  │ │ Manager  │ │          │ │ tion Engine│  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │    │
│  └──────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              Database (PostgreSQL)                        │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │    │
│  │  │update_releases│ │update_install│ │ update_settings  │  │    │
│  │  │              │ │   ations     │ │                  │  │    │
│  │  └──────────────┘ └──────────────┘ └──────────────────┘  │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
           ▲                      ▲                      ▲
           │ REST API             │ REST API             │ CLI
┌──────────┴──────────┐ ┌─────────┴──────────┐ ┌───────┴────────┐
│     Frontend PWA    │ │    CLI Tool        │ │ Third-Party    │
│  ┌────────────────┐ │ │  safevixai update  │ │ Integrations   │
│  │ Update Banner  │ │ │  ┌──────────────┐  │ │                │
│  │ DashboardWidget│ │ │  │ check        │  │ │                │
│  │ Settings Page  │ │ │  │ download     │  │ │                │
│  │ Notifications  │ │ │  │ install      │  │ │                │
│  └────────────────┘ │ │  │ rollback     │  │ │                │
└─────────────────────┘ │  │ history      │  │ │                │
                        │  │ settings     │  │ │                │
                        │  └──────────────┘  │ │                │
                        └────────────────────┘ └────────────────┘
```

---

## Data Model

### Core Entities

| Entity | Table | Description |
|--------|-------|-------------|
| Release | `update_releases` | GitHub release record with version, channel, artifacts |
| Installation | `update_installations` | Install/update history with status tracking |
| Setting | `update_settings` | Per-tenant/global update configuration |

### Relationships
```
Release 1──N Installation (each install corresponds to a release)
Setting 1──1 Tenant/Global (singleton per scope)
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/updates/version` | Current system version info |
| GET | `/api/v1/updates/check?channel=stable` | Check for available updates |
| GET | `/api/v1/updates/releases/{version}` | Get specific release details |
| GET | `/api/v1/updates/history?limit=20` | Installation history |
| POST | `/api/v1/updates/sync` | Sync releases from GitHub |
| POST | `/api/v1/updates/download/{version}` | Download release artifact |
| POST | `/api/v1/updates/install/{version}` | Install/apply update |
| POST | `/api/v1/updates/rollback` | Rollback to previous version |
| GET | `/api/v1/updates/channels` | List available update channels |
| PUT | `/api/v1/updates/settings` | Update update configuration |

---

## Channels

| Channel | Stability | Update Frequency | Auto-Promote | Target |
|---------|-----------|-----------------|--------------|--------|
| `stable` | Production-ready | Monthly | From beta | All users |
| `beta` | Feature-complete, testing | Weekly | From nightly | Opt-in users |
| `nightly` | Daily builds | Daily | — | Developers, CI |
| `pre-release` | Release candidates | Per-release | — | QA, testers |

---

## Update Flow

```
Check ──► Available? ──► Download ──► Verify ──► Install ──► Verify ──► Restart
  │                        │           │           │            │
  │                        │           │           │            └──► Auto restart
  │                        │           │           │                 or manual
  │                        │           │           │
  │                        │           │           └──► Rollback if failed
  │                        │           │
  │                        │           └──► Checksum + signature verification
  │                        │
  │                        └──► Background download with progress
  │
  └──► Notify user (banner, widget, email)
```

---

## Security

| Layer | Mechanism |
|-------|-----------|
| Transport | HTTPS for all downloads |
| Integrity | SHA-256 checksum verification |
| Authenticity | GPG digital signature verification |
| Channel | Channel-specific signing keys |
| Audit | Full installation history with timestamps |
| Rollback | Previous version preserved for rollback |

---

## Frontend Component Tree

```
UpdateBanner
├── Icon (package-update)
├── Message ("Update available: v1.1.0")
├── Changelog summary
├── "Update Now" button
├── "Remind Later" button
└── Dismiss button

DashboardWidget
├── Current version display
├── Update status (up-to-date / update available)
├── Last checked timestamp
├── "Check Now" button
└── Link to update settings

UpdateSettings
├── Channel selector (stable/beta/nightly/pre-release)
├── Auto-update toggle
├── Schedule selector (immediate/daily/weekly)
├── Background download toggle
├── Auto-restart toggle
└── Update history table
```

---

## CLI Commands

```
safevixai update check [--channel stable] [--format json]
safevixai update download <version> [--output ./artifacts]
safevixai update install <version> [--force] [--no-verify]
safevixai update rollback [--version <version>]
safevixai update history [--limit 20] [--format json]
safevixai update settings --auto-update true --channel beta
safevixai update version
```

---

## GitHub Integration

The system integrates with GitHub Releases API to:

1. **Fetch releases**: List releases from `github.com/SafeVixAI/SafeVixAI/releases`
2. **Parse version tags**: Extract semver from git tags (`v1.0.0`, `v1.1.0-beta.1`)
3. **Categorize by channel**: Tags determine channel (no suffix = stable, `-beta` = beta, `-nightly` = nightly, `-rc` = pre-release)
4. **Download artifacts**: Pull release assets (Docker images, binaries, bundles)
5. **Verify signatures**: Check GPG signatures on release assets
6. **Cache locally**: Store release metadata in PostgreSQL for fast queries
