# SafeVixAI — Runbook: Database Unavailable

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** P1  
**Service:** Backend  
**Last Updated:** 2026-05-18

---

## Symptoms
- `/health` returns `{"status": "degraded", "database_available": false}`
- Any endpoint returning 503 with `"database_available": false`
- Supabase alert email received

## Immediate Response (< 5 min)

1. **Check Supabase status** → https://status.supabase.com  
   - If degraded: wait for Supabase to recover; no action needed
2. **Check Render service logs** for the backend:
   ```
   Render dashboard → safevixai-backend → Logs
   ```
   Look for: `asyncpg connection refused`, `FATAL: remaining connection slots`, `SSL error`
3. **Verify connection limit** (Supabase free tier: 60 connections max):
   ```sql
   SELECT count(*) FROM pg_stat_activity WHERE datname = 'postgres';
   ```
   If > 50: connections are exhausted — restart the backend Render service to release connections

## Escalation (> 5 min, no recovery)

4. **Restart backend service** on Render:
   - Render dashboard → safevixai-backend → Manual Deploy → Re-deploy latest
5. **Check DATABASE_URL** env var is set correctly in Render env vars
6. **Test connectivity** from Render shell:
   ```bash
   python -c "import asyncpg, asyncio; asyncio.run(asyncpg.connect('$DATABASE_URL'))"
   ```

## Recovery Validation

- `GET /health` returns `{"status": "ok", "database_available": true}`
- `GET /api/v1/emergency/nearby?lat=13.08&lon=80.27` returns 200

## RTO: 15 minutes | RPO: 24 hours (daily Supabase backup)
