# SafeVixAI — Runbook: Redis Unavailable

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** P2  
**Service:** Backend + Chatbot  
**Last Updated:** 2026-05-18

---

## Symptoms
- `/health` returns `{"cache_available": false, "cache_backend": "redis"}`
- Chat history is not persisted between requests
- Rate limiting falls back to in-memory (not distributed across workers)

## Behaviour Under Degraded Redis
Both services fail gracefully — they do NOT crash:
- **Backend:** Cache operations silently skip; geocoding results not cached
- **Chatbot:** Memory falls back to in-memory `OrderedDict` (capped at 500 sessions); sessions lost on restart

## Immediate Response

1. **Check Upstash Redis status** → https://status.upstash.com  
2. **Verify REDIS_URL** in Render env vars is set and correct
3. **Test Redis connectivity** from Render shell:
   ```bash
   python -c "import redis, asyncio; r=redis.from_url('$REDIS_URL'); asyncio.run(r.ping())"
   ```

## Recovery

4. If Upstash is up but connection fails: regenerate the Redis connection string in Upstash console → update `REDIS_URL` in Render → redeploy
5. If Upstash is down: wait for recovery — services are operating in degraded-but-functional mode

## Recovery Validation
- `GET /health` returns `{"cache_available": true}`

## RTO: Service continues degraded; full recovery within 30 min of Upstash recovery | RPO: N/A (cache is ephemeral)
