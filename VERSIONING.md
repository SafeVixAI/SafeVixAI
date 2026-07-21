# Versioning Policy

SafeVixAI follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## Version Format

Given a version number `MAJOR.MINOR.PATCH`:

| Component | Description |
|-----------|-------------|
| **MAJOR** | Breaking API or behavior changes |
| **MINOR** | New features, backward-compatible |
| **PATCH** | Bug fixes, security patches, backward-compatible |

Pre-release versions use suffix: `1.0.0-alpha.1`, `2.0.0-rc.3`

## Version Source of Truth

The canonical version is stored in the `VERSION` file at the repository root.

```bash
cat VERSION
# → 1.0.0
```

All three services share the same version:
- `backend/pyproject.toml` → `version = "1.0.0"`
- `chatbot_service/pyproject.toml` → `version = "1.0.0"`
- `frontend/package.json` → `"version": "1.0.0"`

## Release Cadence

| Type | Frequency | Approvers |
|------|-----------|-----------|
| Patch | As needed | 1 Core Contributor |
| Minor | Monthly | 2 Core Contributors |
| Major | Quarterly | Project Lead + 2 Core Contributors |
| Hotfix | Emergency | 1 Core Contributor |

## Backward Compatibility

- MINOR releases guarantee API backward compatibility
- PATCH releases guarantee API + data backward compatibility
- MAJOR releases may include breaking changes with migration guide
- Database schema changes are backward-compatible within MINOR version

See [RELEASE.md](RELEASE.md) for the full release workflow.
