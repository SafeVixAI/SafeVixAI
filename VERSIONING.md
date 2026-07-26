# Versioning Policy

> **Version:** 1.0  
> **Last updated:** 2026-07-26

---

## Semantic Versioning

SafeVixAI follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
  │      │      └── Backward-compatible bug fixes
  │      └──────── Backward-compatible new features
  └─────────────── Breaking changes
```

**Pre-release:** `MAJOR.MINOR.PATCH-alpha.N` (e.g., `1.0.0-alpha.1`)

---

## What Constitutes Each Bump

### MAJOR (e.g., 1.0.0 → 2.0.0)
- Breaking API changes (endpoint removal, request/response schema changes)
- Database schema changes requiring data migration
- Removal of deprecated functionality
- Major architectural changes (service decomposition, protocol changes)
- Minimum dependency version bumps that require user action

### MINOR (e.g., 1.0.0 → 1.1.0)
- New API endpoints (non-breaking additions)
- New features that don't break existing functionality
- Deprecation of existing features (with migration path)
- Significant performance improvements
- New LLM provider support
- New language support

### PATCH (e.g., 1.0.0 → 1.0.1)
- Bug fixes
- Security patches
- Performance optimizations
- Documentation updates
- Dependency updates (non-breaking)
- Test additions and improvements
- CI/CD improvements

---

## Pre-release Tags

| Tag | Meaning | Stability |
|-----|---------|-----------|
| `-alpha.N` | Internal testing, unstable APIs | Unstable |
| `-beta.N` | Feature complete, testing phase | Mostly stable |
| `-rc.N` | Release candidate, final testing | Stable |

---

## Backward Compatibility Guarantees

Within a MAJOR version:
- **API**: All documented endpoints remain available. Request/response schemas may only add optional fields.
- **Database**: No breaking schema changes without migration path.
- **Configuration**: Environment variables and config files remain compatible.
- **Database migrations**: All migrations are reversible.
- **Data formats**: Export/import formats remain compatible.

### Exceptions
- **Security fixes**: May break compatibility if necessary to patch a vulnerability (documented in changelog).
- **Internal APIs**: Modules and functions prefixed with `_` have no compatibility guarantee.
- **Experimental features**: Features behind feature flags may change without notice.

---

## Deprecation Policy

1. **Announcement**: Deprecated features are marked in the changelog with deprecation notice.
2. **Grace period**: Features remain functional for at least one MINOR version after deprecation.
3. **Removal**: Deprecated features are removed in the next MAJOR version.
4. **Headers**: Deprecated API endpoints return a `DeprecationWarning` header.
5. **Logging**: Server logs warn when deprecated features are used.

---

## Version Lifecycle

| Stage | Description | Timeline |
|-------|-------------|----------|
| **Development** | Active development on `main` | Pre-release |
| **Alpha** | Early preview, unstable APIs | Weeks |
| **Beta** | Feature complete, testing | 2-4 weeks |
| **Release Candidate** | Final testing before release | 1-2 weeks |
| **Current** | Latest stable release | Until next MAJOR |
| **LTS** | Long-term support (critical patches only) | 12 months |
| **EOL** | No longer supported | After LTS expires |

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 1.0.0 | 2026-07-20 | Current |
| 1.0.0-alpha | 2026-06-30 | EOL |
| 0.x | 2026-06 | EOL |
