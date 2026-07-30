# SafeVixAI — Runbook: High Error Rate

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** P1  
**Service:** Backend or Chatbot  
**Threshold:** > 5% 5xx error rate sustained over 5 minutes  
**Last Updated:** 2026-05-18

---

## Symptoms
- Render service health shows repeated 500/503 responses in logs
- Alert email received about service degradation
- Users reporting "something went wrong" screens in the app

## Immediate Response (< 5 min)

1. **Check Render logs** for stack traces:
   ```
   Render dashboard → [service] → Logs → Filter: ERROR
   ```
2. **Check /health endpoint:**
   ```
   GET /health
   ```
   Check `database_available` and `cache_available` flags
3. **Identify the failing endpoint** from logs — look for the most frequent `path` in error logs

## Common Causes & Fixes

| Error Pattern | Cause | Fix |
|---|---|---|
| `asyncpg: too many connections` | DB connection exhaustion | Restart backend service |
| `redis.exceptions.ConnectionError` | Redis down | See redis-down.md runbook |
| `sqlalchemy.exc.OperationalError` | DB down | See db-down.md runbook |
| `httpx.ReadTimeout` | External API timeout | Check Overpass/OpenCage status |
| `KeyError: 'services'` | Response schema mismatch | Check for deployment mismatch between services |

## Escalation (> 10 min, no recovery)

4. **Rollback to previous deployment:**
   - Render dashboard → [service] → Deploys → Previous deploy → Redeploy
5. **Scale up** if CPU/memory is saturated (check Render metrics tab)

## Recovery Validation
- Error rate drops below 1% in logs
- `GET /health` returns `{"status": "ok"}`

## RTO: 15 minutes
