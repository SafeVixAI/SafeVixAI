# Update Management System

> Enterprise-grade software update management for SafeVixAI.

The Update Management System provides automatic version checking, update installation,
rollback capabilities, and channel management across all SafeVixAI deployments.

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture](ARCHITECTURE.md) | System design, data model, component tree |
| [API Reference](UPDATE_SYSTEM_API.md) | Complete API endpoint documentation |
| [Deployment Guide](UPDATE_SYSTEM_DEPLOYMENT.md) | Setup, CLI, Makefile targets, verification |

## Key Capabilities

- **Version checking** — Semantic version comparison against GitHub releases
- **Channel management** — Stable, Beta, Nightly, Pre-release channels
- **Rolling updates** — Download → Verify → Install flow with rollback
- **GitHub integration** — Automatic release sync from GitHub Releases API
- **User interface** — Update banner, dashboard widget, settings page
- **CLI tool** — Cross-platform update management via Python/PowerShell
- **API-first** — Full REST API for programmatic integration

## Database Tables

| Table | Description |
|-------|-------------|
| `update_releases` | Release records with version, channel, checksums |
| `update_installations` | Installation history with status tracking |
| `update_settings` | Per-deployment update configuration |
