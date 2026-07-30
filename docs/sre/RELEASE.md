# Release Process

## Versioning

This project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Given a version number `MAJOR.MINOR.PATCH`:

- **MAJOR** — Breaking API or behavior changes
- **MINOR** — New features, backward-compatible
- **PATCH** — Bug fixes, security patches, backward-compatible

Pre-release versions use suffix: `1.0.0-alpha.1`, `2.0.0-rc.3`

Version source of truth: `VERSION` file at repository root.

## Branching Model

```mermaid
gitGraph
    commit
    branch staging
    commit
    branch feat/feature-1
    commit
    commit
    checkout staging
    merge feat/feature-1
    branch fix/bug-1
    commit
    checkout staging
    merge fix/bug-1
    checkout main
    merge staging tag: "v1.0.0"
    branch chore/cleanup
    commit
    checkout main
    merge chore/cleanup
```

## Release Types

| Type | Frequency | Approvers | Artifacts |
|------|-----------|-----------|-----------|
| Patch | As needed | 1 Core Contributor | Docker + GitHub Release |
| Minor | Monthly | 2 Core Contributors | Docker + GitHub Release + SBOM |
| Major | Quarterly | Project Lead + 2 Core Contributors | Docker + GitHub Release + SBOM + Changelog |
| Hotfix | Emergency | 1 Core Contributor | Docker + GitHub Release |

## Release Workflow

```mermaid
flowchart LR
    FR[Freeze] --> CL[Changelog]
    CL --> VB[Version Bump]
    VB --> CI[CI Validation]
    CI --> GR[GitHub Release]
    GR --> PR[Post-Release]

    subgraph CI_Steps["CI Validation"]
        direction TB
        T1[All tests pass]
        T2[Lint + type-check]
        T3[SBOM generated]
        T4[Docker images built + signed]
    end

    CI --> CI_Steps

    style FR fill:#da3633,color:#fff
    style CL fill:#1f6feb,color:#fff
    style VB fill:#9e6a03,color:#fff
    style CI fill:#238636,color:#fff
    style GR fill:#6e5494,color:#fff
    style PR fill:#8957e5,color:#fff
```

1. **Freeze** — All changes for the release are merged to `main`
2. **Changelog** — `CHANGELOG.md` is updated and frozen
3. **Version bump** — `VERSION` file updated, committed, tagged (`vX.Y.Z`)
4. **CI validation** — Release workflow triggered by tag push:
   - Tag matches `VERSION` file
   - All tests pass (unit, E2E, security, load, chaos)
   - Lint + type-check pass
   - SBOM generated (CycloneDX + SPDX)
   - Docker images built, signed, pushed to GHCR
   - SLSA provenance attestation generated
5. **GitHub Release** — Created with auto-generated notes from `CHANGELOG.md`
6. **Post-release** — Release artifacts attached (SBOM, provenance, signed checksums)

## Hotfix Process

1. Branch from `main`: `git checkout -b hotfix/HF-xxx`
2. Fix and test
3. Merge directly to `main` (bypass staging)
4. Tag and release immediately
5. Cherry-pick fix to `staging` if needed

## Rollback Process

### Container Rollback
```bash
# Rollback to previous Docker tag
docker pull ghcr.io/safevixai/backend:vX.Y.Z-1
docker service update --image ghcr.io/safevixai/backend:vX.Y.Z-1 safevixai_backend
```

### Database Rollback
1. Restore from backup: `pg_restore -d safevixai backup/safevixai_YYYYMMDD.sql`
2. Run Alembic downgrade: `alembic downgrade -1`
3. Verify data integrity before re-deploying

## Release Approval

| Role | Responsibility |
|------|---------------|
| Release Manager | Shepherds the release, owns the timeline |
| Core Contributors | Review changelog, approve artifacts |
| Project Lead | Final sign-off on Major releases |
| Security Team | Sign-off on releases with security fixes |

## Maintenance & Upgrade Path

### Older Version Support

| Version | Status | Security Fixes | EOL |
|---------|--------|---------------|-----|
| 1.x | Active | Yes | TBD |

### Upgrade Path

1. Review the [CHANGELOG.md](CHANGELOG.md) for breaking changes between versions.
2. Check [RELEASE_NOTES.md](RELEASE_NOTES.md) for migration guides specific to your upgrade path.
3. For database schema changes, run Alembic migrations: `alembic upgrade head` from `backend/`.
4. Test the upgrade in a staging environment before applying to production.
5. Rollback via `alembic downgrade -1` if issues arise (schema rollback supported within the same minor version).

### Upgrade Notices

Upgrade notices (including breaking changes, deprecations, and migration guidance) are published as:
- GitHub Release notes for the affected version
- `CHANGELOG.md` with clear marking of breaking changes
- GitHub Issue tagged `upgrade-notice` for critical migrations

## Verification

Every release MUST verify:

- [ ] `make test` — all tests pass
- [ ] `make lint` — zero errors
- [ ] `make build` — all containers build
- [ ] `make security-scan` — trivy + gitleaks pass
- [ ] SBOM generated and attached
- [ ] Docker images signed with cosign
- [ ] SLSA provenance generated
- [ ] GitHub Release created with notes
- [ ] Smoke tests pass against deployed release
