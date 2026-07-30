# Runbook: Database Migration Rollback

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** SEV1 | **Service:** Backend | **Time to execute:** 5 minutes

## Symptoms
- Backend fails to start after deployment
- `AlembicError` or `ProgrammingError` in logs
- `relation "xxx" does not exist` errors

## Steps

### 1. Identify the failed migration
```bash
cd backend
alembic current
# Shows current revision (e.g., "abc123 (head)")
```

### 2. Rollback to previous revision
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <previous_revision_id>

# Rollback all migrations (emergency only)
alembic downgrade base
```

### 3. Verify rollback
```bash
alembic current
# Should show the previous revision
```

### 4. Restart backend service
```bash
# On Render: trigger redeploy from dashboard
# Locally: restart uvicorn
```

### 5. Verify health
```bash
curl http://localhost:8000/health
# Should return {"status": "ok", ...}
```

## Prevention
- Always run `alembic check` before committing migrations
- Test migrations on staging before production
- Review migration SQL with `alembic upgrade head --sql`
