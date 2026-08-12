# SafeVixAI — Operational Risk Map

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

> Generated: 2026-05-22 | Production operations, recovery, incident response

---

## 1. Deployment Risks

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|------------|--------|
| Render free tier idle timeout | HIGH | MEDIUM | Cold start 30-60s on first request | Accepted |
| Render free tier 750h exceeded | HIGH | MEDIUM | Services throttled after limit | Monitoring needed |
| Alembic migration failure on deploy | MEDIUM | HIGH | Manual rollback (downgrade exists) | No automation |
| Frontend build failure (TypeScript errors ignored) | MEDIUM | MEDIUM | `|| true` in CI — silent failures | Known tech debt |
| pnpm/npm lockfile drift | MEDIUM | MEDIUM | CI uses pnpm, local uses npm | Known (AGENTS.md) |
| Vercel deploy timeout (10s limit) | LOW | MEDIUM | Serverless function timeout | Acceptable |
| Docker `:latest` tag overwritten | HIGH | LOW | No versioned rollback images | Low priority |

---

## 2. Recovery Runbooks

### Service Down: Backend (Render)
```yaml
Symptoms:
  - Frontend shows "Service Unavailable"
  - /health returns 503
  - Sentry errors spike

Recovery:
  1. Check Render Dashboard → service logs
  2. Check if auto-restart triggered (Render auto-restart on crash)
  3. If still down → Manual deploy from Render dashboard
  4. Check Supabase status (auto-paused after 7 days)
  5. Check Redis connectivity
  6. Run alembic upgrade head if schema changed

Rollback:
  1. Render Dashboard → Deploy → Last successful deploy
  2. If DB migration caused issue → alembic downgrade -1
  3. If config issue → Check env vars in Render Dashboard
```

### Service Down: Chatbot (Render)
```yaml
Symptoms:
  - /health returns non-200
  - Backend marks chatbot_ready=false
  - Chat/assistant features fail

Recovery:
  1. Check Render Dashboard → service logs
  2. Check LLM provider keys (rotate if compromised)
  3. Check Redis connectivity
  4. Check disk space (ChromaDB persisted)

Degradation:
  - All non-chat features work (SOS, Emergency, Challan, Maps)
  - Backend LLMService.fallback_response() handles chat
  - Chat interface shows offline mode message
```

### Service Down: Frontend (Vercel)
```yaml
Symptoms:
  - DNS resolves but page doesn't load
  - Vercel dashboard shows build failure

Recovery:
  1. Vercel Dashboard → Deployments → Last successful → Redeploy
  2. Check GitHub Actions → frontend.yml for build errors
  3. If TypeScript error → Fix and push to main

Degradation:
  - Service Worker may serve cached pages (if previously visited)
  - Offline mode available for cached content
```

### Service Down: Database (Supabase)
```yaml
Symptoms:
  - Backend /health shows database_available=false
  - All features relying on DB fail

Recovery:
  1. Supabase Dashboard → Check project status
  2. If auto-paused (7 days inactivity) → Click "Resume project"
  3. If connection error → Check DATABASE_URL in env vars
  4. If migration issue → alembic downgrade + fix

Degradation:
  - Emergency: CSV + Overpass fallback still works
  - Challan: In-memory rules + CSV still works
  - Chatbot: Works independently (uses ChromaDB, not PostgreSQL)
  - SOS: Creates local record, syncs when DB restored
  - Reports: Stored in IndexedDB queue, syncs on restore
```

### Service Down: Redis (Upstash)
```yaml
Symptoms:
  - Backend /health shows cache_backend=memory
  - Rate limiting disabled (resets in memory)
  - Cache cold (all data fetched fresh)
  - Chatbot sessions lost

Recovery:
  1. Upstash Dashboard → Check usage limits
  2. If 10K commands/day exceeded → Wait for reset or upgrade plan
  3. If connection error → Check REDIS_URL env var

Degradation:
  - In-memory cache fallback active (limited TTL, lost on restart)
  - Rate limiting becomes per-instance (multi-worker bypass)
  - Chatbot sessions: new conversations start fresh
  - LLM response cache: disabled (new responses generated each time)
```

### API Key Rotation (All Providers)
```yaml
Scheduled: Every 90 days or on security incident

Process:
  1. Generate new API key in provider's dashboard
  2. Update env var in Render Dashboard (sync: false)
  3. Trigger Render redeploy via deploy hook
  4. Verify /health shows provider available
  5. Revoke old API key (wait 24h for propagation)

Critical:
  - SUPABASE_SERVICE_ROLE_KEY → Rotate first, update env, then revoke old
  - JWT_SECRET_KEY → Rotate only if compromised (breaks all current sessions)
  - ADMIN_SECRET → Rotate both backend and chatbot simultaneously
  - GMAIL_APP_PASSWORD → Generate new in Google Account settings
```

---

## 3. Incident Response Plan

### Triage Levels

| Level | Definition | Response Time | Escalation |
|-------|-----------|--------------|------------|
| P0 | Full outage (all services down) | 15 min | Project Lead |
| P1 | Critical feature broken (SOS, Chat) | 30 min | Tech Lead |
| P2 | Major feature degraded (maps, challan) | 2 hours | Senior Dev |
| P3 | Minor issue (UI glitch) | Next business day | Dev |
| P4 | Cosmetic / nice-to-have | Backlog | None |

### P1 Incident: Chatbot Unavailable
```yaml
Trigger: Multiple users report "Chat not working" or /health shows chatbot inactive

Response:
  1. [5 min] Check chatbot /health
  2. [10 min] Check Render chatbot logs for errors
  3. [15 min] Check LLM provider status pages:
     - Groq status → https://status.groq.com
     - Gemini status → https://status.cloud.google.com
     - Other providers
  4. [20 min] If provider outage → Mark in docs, rely on fallback chain
  5. [30 min] If Render crash → Restart
  6. [1 hour] If Redis issue → Check Upstash dashboard

Communications:
  - Post to status page (if exists)
  - Update GitHub issue with ETA
  - Notify users in-app via banner
```

### P1 Incident: SOS Not Working
```yaml
Trigger: User reports "SOS didn't send" or failed /api/v1/emergency/sos

Response:
  1. [2 min] Test POST /api/v1/emergency/sos manually with curl
  2. [5 min] Check backend logs for errors
  3. [10 min] Check if BackendService is running
  4. [15 min] Check database connectivity
  5. [20 min] If offline user → Check IndexedDB queue flushing
  6. [30 min] Verify offline → online transition triggers queue flush

Degradation:
  - If backend down → SOS still works with offline queue
  - If database down → SOS logs locally, syncs when DB restored
  - If Overpass down → Uses cached + CSV data (slightly stale)
```

### P2 Incident: Maps Not Loading
```yaml
Trigger: Users report blank map or "Map Error"

Response:
  1. [5 min] Check MapLibre GL version compat
  2. [10 min] Check map provider status:
     - Google Maps → Check billing/API key
     - MapTiler → Check API key usage
     - OpenFreeMap → Check if service is up
  3. [15 min] If style rotation fails → All 3 backends checked
  4. [30 min] If API key issue → Rotate key

Degradation:
  - MapLibre has 3 backends (Google → MapTiler → OpenFreeMap)
  - Auto-style rotation on failure
  - Text fallback alternative (address-based) available
```

---

## 4. Monitoring Requirements

### Must-Alert Conditions
```yaml
Critical (Email + Sentry):
  - /health returns non-200 for >30s
  - All LLM providers fail simultaneously
  - Database connection lost
  - Secrets leak detected
  - SOS dispatch failure rate >10%
  - Chatbot response time >30s

Warning (Sentry + Log):
  - Any LLM provider failure (circuit breaker opens)
  - Redis connectivity lost (memory fallback active)
  - Overpass API mirror exhaustion
  - Response time >5s for any endpoint
  - High rate limit usage >80%
  - API 5xx rate >1%
```

### Health Check Thresholds
```yaml
Endpoint: GET /health (all services)
  Interval: 30s (Render automated)
  Success: 200 OK within 5s
  Failure: 503 if database unavailable
  Critical Degradation: Database down + chatbot down = RED
  Warning Degradation: Cache down (memory fallback) = YELLOW
```

---

## 5. Cost Management

### Free Tier Headroom
```yaml
Vercel Hobby:
  Bandwidth: 100 GB/month
  Build minutes: 6000/month
  Functions: 10s timeout
  Risk: LOW For initial traffic

Render Free:
  Hours: 750/month total (needs 1488 for 24/7)
  RAM: 512 MB
  CPU: 0.1 vCPU
  Risk: HIGH if traffic increases

Supabase Free:
  DB: 500 MB (currently <50 MB)
  Bandwidth: 5 GB
  MAU: 50,000
  Storage: 2 GB
  Risk: LOW

Upstash Free:
  Commands: 10,000/day
  Storage: 256 MB
  Risk: MEDIUM (10K commands/day is low)

API Keys Free Tiers:
  Groq: 30 RPM, 14,400 RPD → MEDIUM risk
  Gemini: 15 RPM, 1M tokens/day → LOW risk
  What3Words: 50K/month → LOW risk
  OpenWeather: 60/min, 1M/month → LOW risk
  Key: Routes through Groq first, 30 RPM sufficient for low traffic
```

---

## 6. Operational Runbooks (Quick Reference)

### Daily Checks
```yaml
1. Check GitHub Actions → All workflows green
2. Quick health check:
   - curl https://safevixai-backend.onrender.com/health
   - curl https://safevixai-chatbot.onrender.com/health
   - curl https://safevixai.vercel.app
3. Check Sentry for error spikes
4. Check Supabase DB size

Commands:
  curl -s https://safevixai-backend.onrender.com/health | python -m json.tool
```

### Weekly Tasks
```yaml
1. Review Dependabot PRs → Merge or defer
2. Check Render Dashboard → Service logs for errors
3. Check Upstash Dashboard → Command usage
4. Review Sentry → New error patterns
5. Run load test manually if needed:
   - cd tests/load && k6 run backend_api_load.js
```

### Monthly Tasks
```yaml
1. Rotate API keys (scheduled)
2. Review Supabase backup → Verify auto-backup exists
3. Review GitHub security tab → Address any findings
4. Update AGENTS.md with new learnings
5. Run full CI suite manually → Verify all passing
6. Check Docker images → Prune old GHCR images
```

### Emergency Contacts
```yaml
Infra:
  - Render: support@render.com (24/7)
  - Supabase: support@supabase.com
  - Vercel: support@vercel.com
  - Upstash: support@upstash.com

In Case of Breach:
  - IMMEDIATE: Rotate ALL secrets
  - Revoke compromised keys
  - Report to project lead
  - Document incident in docs/INCIDENTS.md
```
