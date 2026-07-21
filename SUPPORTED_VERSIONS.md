# Supported Versions

## Current Release

| Version | Status | Security Fixes | Bug Fixes | EOL |
|---------|--------|---------------|-----------|-----|
| 1.0.x | Active | ✅ | ✅ | TBD |

## Older Versions

| Version | Status | Security Fixes | Bug Fixes | EOL |
|---------|--------|---------------|-----------|-----|
| < 1.0 | Unsupported | ❌ | ❌ | — |

## Support Policy

- **Active**: Receives security patches and bug fixes
- **Maintenance**: Receives only security patches
- **Unsupported**: No updates of any kind

## Upgrade Path

1. Review [CHANGELOG.md](CHANGELOG.md) for breaking changes
2. Check [RELEASE.md](RELEASE.md) for migration guides
3. For database schema changes: `alembic upgrade head` from `backend/`
4. Test the upgrade in staging before production
5. Rollback via `alembic downgrade -1` if issues arise

## Version Lifecycle

| Version | Released | EOL Target |
|---------|----------|------------|
| 1.0.0 | 2026-07-20 | 2027-01-20 (6 months after next major) |

EOL dates are extended by 6 months after each subsequent major release to ensure adequate migration time.
