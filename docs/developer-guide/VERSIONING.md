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

## Version Bump Decision Tree

```mermaid
flowchart TB
    CHANGE[Code Change] --> TYPE{"Change Type?"}

    TYPE -->|"Breaking API / DB Schema"| MAJOR["MAJOR bump<br/>1.0.0 → 2.0.0"]
    TYPE -->|"New Feature / Deprecation"| MINOR["MINOR bump<br/>1.0.0 → 1.1.0"]
    TYPE -->|"Bug Fix / Security Patch"| PATCH["PATCH bump<br/>1.0.0 → 1.0.1"]

    MAJOR --> NOTES[Announce migration path]
    MINOR --> NOTES2[Add deprecation warnings]
    PATCH --> NOTES3[Hotfix release]


    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b
    classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#7c2d12
    classDef neutral fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b

    class CHANGE neutral
    class TYPE decision
    class MAJOR neutral
    class MINOR neutral
    class PATCH neutral
    class NOTES neutral
    class NOTES2 neutral
    class NOTES3 neutral```

## Version Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Development
    Development --> Alpha : Code complete
    Alpha --> Beta : Feature freeze
    Beta --> RC : All tests pass
    RC --> Current : Release approval
    Current --> LTS : Major version bumps
    LTS --> EOL : 12 months after LTS start

    note right of Development
        Active development on main
    end note

    note right of LTS
        Critical patches only
    end note
```

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
