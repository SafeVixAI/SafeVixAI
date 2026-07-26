# Release Process

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [VERSIONING.md](../VERSIONING.md), [CHANGELOG.md](../CHANGELOG.md), [GOVERNANCE.md](../GOVERNANCE.md)

---

## Release Cadence

| Type | Frequency | Coordination |
|------|-----------|-------------|
| Patch | As needed (bug fixes, security) | Unplanned |
| Minor | Monthly | Planned |
| Major | Quarterly | RFC + planning |

---

## Release Manager

A **Release Manager** is assigned from Core Contributors for each release. Responsibilities:
- Track release progress
- Coordinate testing and QA
- Manage changelog
- Sign artifacts
- Communicate release status

---

## Release Steps

### 1. Feature Freeze (7 days before release)
- All features for the release must be merged
- No new features — only bug fixes and documentation
- Release branch created: `release/v{x}.{y}.0`

### 2. Changelog Finalization
- Review [CHANGELOG.md](../CHANGELOG.md) for completeness
- Ensure all changes are documented
- Add migration notes if applicable

### 3. QA Gates
- [ ] All CI workflows pass
- [ ] E2E tests pass (55/55)
- [ ] Security scan passes (gitleaks, CodeQL)
- [ ] Load tests pass (k6, no regression)
- [ ] Mutation tests pass (backend, informational)
- [ ] Contract validation tests pass
- [ ] Hypothesis property tests pass

### 4. SBOM Generation
```bash
# CycloneDX (Python)
cd backend && cyclonedx-py requirements.txt --output sbom.backend.json
cd chatbot_service && cyclonedx-py requirements.txt --output sbom.chatbot.json

# SPDX (npm)
cd frontend && npx license-checker --production --csv --out sbom.frontend.csv
```

### 5. Docker Image Signing
```bash
# Cosign keyless signing via GitHub OIDC
cosign sign --keyless \
  ghcr.io/safevixai/backend:v1.0.0

cosign sign --keyless \
  ghcr.io/safevixai/chatbot:v1.0.0

cosign sign --keyless \
  ghcr.io/safevixai/frontend:v1.0.0
```

### 6. GitHub Release
```bash
# Create tag
git tag -a v1.0.0 -m "v1.0.0: Release title"
git push origin v1.0.0

# Release notes auto-generated from CHANGELOG.md
gh release create v1.0.0 \
  --title "v1.0.0" \
  --notes-file CHANGELOG.md \
  sbom.backend.json sbom.chatbot.json sbom.frontend.csv
```

### 7. Post-Release Verification
- [ ] Smoke tests pass against deployed release
- [ ] Release notes published on GitHub
- [ ] Docker images available on GHCR
- [ ] Documentation site updated (MkDocs deploy)
- [ ] Deployment manifests updated (k8s, terraform)

---

## Hotfix Process

For critical bugs in production:

1. Branch from the release tag: `git checkout -b hotfix/v1.0.1 v1.0.0`
2. Apply the fix
3. Bump version in `VERSION`
4. Update changelog
5. Create PR targeting `main` and the release branch
6. Deploy from release branch
7. Merge to `main`

**Emergency process** (security vulnerability): Skip PR review, deploy from private fork, coordinate disclosure.

---

## Release Artifacts

| Artifact | Format | Location |
|----------|--------|----------|
| Source code | Git tag | GitHub |
| Docker images | OCI | ghcr.io/safevixai/* |
| SBOM | CycloneDX, SPDX | GitHub Release |
| Documentation | MkDocs site | GitHub Pages |
| Client libraries | npm, PyPI | TBD |

---

## Version History

| Version | Date | Release Manager | Status |
|---------|------|-----------------|--------|
| 1.0.0 | 2026-07-20 | SafeVixAI Team | Current |
| 1.0.0-alpha | 2026-07-08 | — | Archived |
