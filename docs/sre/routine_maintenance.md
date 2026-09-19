# Maintenance Guide

## Scheduled Maintenance

### Weekly
- Review Dependabot PRs (pip, npm, GitHub Actions)
- Check CI workflow health (no failing workflows)
- Review open issues for stale items

### Monthly
- Apply non-critical dependency updates (minor/patch)
- Rotate secrets if policy requires it (see `scripts/rotate-secrets.py`)
- Review Sentry error trends for new patterns
- Run load tests (`make k6-load`) to check for regressions

### Quarterly
- Review and update documentation
- Review and rotate API keys for external services
- Full dependency audit (all ecosystems)
- Run security scan (gitleaks + trivy + codeql)
- Update ADRs for any architectural changes
- Review coverage thresholds and raise if possible

## Upgrade Procedures

### Dependency Upgrades
1. Create a branch: `chore/deps-YYYY-MM-DD`
2. Run `npm audit --fix` and `pip-audit`
3. Run full test suite across all 3 services
4. Deploy to staging, verify smoke tests
5. Merge to `main`

### Database Migrations
1. Review migration SQL before running
2. Always backup before migration: `pg_dump -d safevixai > pre_migration.sql`
3. Run `alembic upgrade head` from `backend/`
4. Verify data integrity with spot checks
5. Keep migration in git for rollback (`alembic downgrade -1`)

### TLS Certificate Renewal
- Handled automatically by Vercel and Render
- For custom domains: certs auto-renew via Let's Encrypt
- No manual action required unless DNS changes

## Capacity Planning

| Metric | Current Usage | Limit | Growth Plan |
|--------|-------------|-------|-------------|
| Backend API calls | < 1K/day | Free tier | Upgrade GPU plan |
| Chatbot API calls | < 500/day | Free tier | Upgrade GPU plan |
| DB storage | < 100MB | 500MB | Purge old data or upgrade |
| Redis memory | < 10MB | 30MB | Upgrade to paid tier |
