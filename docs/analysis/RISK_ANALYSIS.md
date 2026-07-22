# SafeVixAI — Risk Analysis (2026-05-26)

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

> What breaks first under load, stress, or attack. Ordered by severity.

---

## 1. Critical Risks (Catastrophic Impact)

### R1: Live Credentials in Git Repository
- **What**: All 3 `.env` files contain production credentials committed and tracked in git
- **Impact**: Anyone with repo access has: JWT signing key, DB password, 11 LLM API keys, Gmail app password, Supabase service_role key
- **Likelihood**: CERTAIN — already exposed
- **Attack vector**: Insider threat, compromised GitHub account, CI log leakage, branch exposure
- **Mitigation**: Rotate ALL keys immediately, git filter-branch to remove .env from history, add .env to .gitignore (already present — need to untrack)

### R2: Chatbot API Has No Authentication
- **What**: `/api/v1/chat/` and `/api/v1/chat/stream` endpoints on chatbot service (port 8010) require no JWT or service token
- **Impact**: Anyone who discovers the chatbot URL can send unlimited messages; rate limiting is per-IP (20/min) but IP-rotation breaks this
- **Likelihood**: HIGH — chatbot URL is documented in public GitHub repo
- **Attack vector**: DDoS via repeated chat requests, prompt injection probes, cost exhaustion (providers charge per token)
- **Mitigation**: Add `X-Service-Token` header validation (backend→chatbot service communication), or forward backend JWT

### R3: Render Free Tier Service Unavailability
- **What**: Two services require ~1464 hours/month; Render free tier gives 750 hours/month
- **Impact**: Services auto-sleep after 15min idle; total runtime exceeds free quota → services stop responding
- **Likelihood**: VERY HIGH — 2 services × 24h × 30.5d = 1464 hours needed
- **Mitigation**: Upgrade to Render Starter ($7/mo × 2), or reduce runtime (not practical for emergency app)

### R4: SOS Incidents Persist Indefinitely
- **What**: No data retention policy enforced; SOS incident records accumulate with no cleanup
- **Impact**: Privacy violation for SOS victims (location + phone + PII stored forever); DB growth unavoidable
- **Likelihood**: CERTAIN — migration 10005_data_retention exists but no cron job enforces it
- **Mitigation**: Enable the retention cron (delete SOS after 1 year, tracking after 30 days)

---

## 2. High Risks (Major Impact)

### R5: No RBAC Enforcement
- **What**: JWT contains `role` claim but most endpoints don't check it; any authenticated user = full access
- **Impact**: Authenticated user can read all profiles, all SOS incidents, all chat logs, all admin endpoints
- **Likelihood**: HIGH — if auth is compromised, no second layer of protection
- **Mitigation**: Add role-check decorator to all ADMIN/OPERATOR endpoints

### R6: No Host Header Validation
- **What**: Backend accepts requests with any Host header; no ALLOWED_HOSTS check
- **Impact**: Host header injection for password reset poisoning, cache poisoning, SSRF via open redirect
- **Likelihood**: MEDIUM — requires attacker to craft malicious request through a proxy
- **Mitigation**: Add ALLOWED_HOSTS middleware checking against FRONTEND_URL

### R7: Upstash Redis Rate Limit Exceeded
- **What**: Free tier allows only 10,000 commands/day; cache, rate limiting, session memory all depend on Redis
- **Impact**: All Redis systems fall back to in-memory; rate limiting resets, session memory lost on restart
- **Likelihood**: MEDIUM-HIGH — each API request uses 2-5 Redis commands (cache check + rate limit)
- **Mitigation**: Reduce cache TTLs, batch Redis commands, monitor command usage

### R8: All LLM Providers Fail Simultaneously
- **What**: All 10 providers return errors or time out; chain exhausts to TemplateProvider
- **Impact**: Chatbot returns deterministic template responses (no semantic answers), user trust degraded
- **Likelihood**: LOW — but if Groq + Cerebras + Gemini all down, chain shortens to fewer options
- **Mitigation**: TemplateProvider provides safe fallback; email alert triggers after all fail

### R9: Supabase Auto-Pause After 7 Days
- **What**: Supabase free tier auto-pauses database after 7 days of inactivity
- **Impact**: All DB queries fail; emergency locator -> zero results (CSV fallback still works)
- **Likelihood**: MEDIUM — depends on activity; health check pings may prevent this
- **Mitigation**: Scheduled cron to keep DB active (already handled by health checks)

---

## 3. Medium Risks (Moderate Impact)

### R10: SafetyChecker Output Validation Dead Code
- **What**: `check_output_safety()` defined (lines 234-255) but never called in ChatEngine
- **Impact**: LLM responses containing harmful content are not filtered server-side
- **Likelihood**: MEDIUM — depends on LLM provider's own safety filters
- **Mitigation**: Wire `check_output_safety()` into ChatEngine after ProviderRouter.generate()

### R11: Medical Disclaimer Never Added to Responses
- **What**: `add_medical_disclaimer_if_needed()` defined (lines 226-232) but never called
- **Impact**: First-aid and medical advice from chatbot lacks "Call 112 immediately" disclaimer
- **Likelihood**: HIGH — first aid tool frequently returns medical advice
- **Mitigation**: Wire disclaimer into response post-processing

### R12: SWR Underutilized
- **What**: Only 1 of 23 pages uses SWR; most use manual Axios + useState/useEffect
- **Impact**: No request deduplication, no cache-first responses, no automatic revalidation
- **Likelihood**: HIGH — every page mount triggers fresh API calls
- **Mitigation**: Convert all data-fetching pages to SWR hooks

### R13: torch in Chatbot Service (800MB)
- **What**: torch 2.12.0 + torchaudio 2.11.0 + transformers 5.5.4 required for IndicSeamless speech
- **Impact**: Render 512MB RAM instance cannot load torch; speech translation fails to start
- **Likelihood**: CERTAIN — graceful failure handled via fallback, but feature non-functional
- **Mitigation**: Move speech to separate lightweight service or use Groq Whisper API instead

### R14: WebSocket No Origin Validation
- **What**: `backend/api/v1/tracking.py` validates origin against CORS list but doesn't enforce it strictly
- **Impact**: WebSocket connections from non-allowed origins may pass
- **Likelihood**: LOW-MEDIUM — depends on browser CORS behavior
- **Mitigation**: Add strict origin check in WebSocket accept handler

---

## 4. Low Risks (Minor Impact)

### R15: FastAPI Docs Enabled in Production
- **What**: `/docs` and `/redoc` accessible if `ENVIRONMENT != 'production'`
- **Impact**: API schema exposure (information disclosure)
- **Likelihood**: LOW — ENVIRONMENT var should be set to 'production' in Render
- **Mitigation**: Verify Render env vars

### R16: Duplicate Service Worker IndexedDB Schema
- **What**: `public/sw.js` duplicates IndexedDB schema from `lib/offline-sos-queue.ts`
- **Impact**: Schema drift between SW and client library
- **Likelihood**: MEDIUM — schema version mismatch causes runtime errors
- **Mitigation**: Extract shared schema module or use Workbox

### R17: Render Secret Sync Not Verified
- **What**: render.yaml has `sync: false` for 15+ secrets — must be manually set in Render dashboard
- **Impact**: Missing secrets → auth failures, third-party API failures
- **Likelihood**: HIGH on first deploy; low once configured
- **Mitigation**: Add secret validation endpoint, verify at startup

---

## 5. Operational Risk Matrix

| Risk | Prob | Impact | Score | Owner | Mitigation |
|------|------|--------|-------|-------|------------|
| R1: Credentials in git | CERTAIN | CRITICAL | 10 | Security | Rotate keys, git filter |
| R2: Chatbot no auth | HIGH | HIGH | 8 | Backend | Add service token |
| R3: Render quota | VERY HIGH | HIGH | 8 | DevOps | Upgrade plan |
| R4: No data retention | CERTAIN | MEDIUM | 6 | Backend | Enable retention cron |
| R5: No RBAC | HIGH | HIGH | 8 | Backend | Role-check decorator |
| R6: No Host validation | MEDIUM | HIGH | 7 | Backend | ALLOWED_HOSTS middleware |
| R7: Redis rate limit | MEDIUM | HIGH | 6 | Backend | Monitor, batch commands |
| R8: LLM all fail | LOW | MEDIUM | 4 | Chatbot | Email alert + template |
| R9: Supabase auto-pause | MEDIUM | CRITICAL | 7 | DevOps | Keep-alive cron |
| R10: Safety output dead | MEDIUM | MEDIUM | 4 | Chatbot | Wire check_output_safety |
| R11: Medical disclaimer | HIGH | MEDIUM | 6 | Chatbot | Wire disclaimer |
| R12: SWR underused | HIGH | LOW | 3 | Frontend | Convert pages |
| R13: torch over RAM | CERTAIN | LOW | 2 | Chatbot | Swap to Whisper API |
| R14: WS origin check | LOW | MEDIUM | 3 | Backend | Add strict check |
| R15: Docs enabled | LOW | LOW | 1 | Backend | Verify env |
| R16: SW schema dup | MEDIUM | LOW | 2 | Frontend | Extract shared |
| R17: Render secrets | HIGH | MEDIUM | 5 | DevOps | Add validation endpoint |

---

## 6. Attack Surface Map (External)

```
Internet
  ├── Vercel (frontend)
  │   ├── ALL routes: Public (no auth required for safety features)
  │   ├── POST /api/v1/emergency/sos: Rate limited (10/min)
  │   ├── POST /api/v1/challan/calculate: Public
  │   ├── POST /api/v1/roads/report: Public (optional auth)
  │   └── POST /api/v1/chat/stream: Auth on backend side
  │
  ├── Render (backend :8000)
  │   ├── GET /docs: Schema disclosure (if not production)
  │   ├── POST /api/v1/auth/login: 5/min rate limit
  │   ├── ALL /api/v1/admin/*: OPERATOR role required
  │   └── WebSocket /tracking: JWT query param
  │
  ├── Render (chatbot :8010)
  │   ├── POST /api/v1/chat/: NO AUTH — highest risk
  │   ├── POST /api/v1/chat/stream: NO AUTH
  │   ├── POST /speech/translate: NO AUTH (file upload)
  │   └── GET /admin/*: X-Admin-Key header (deprecated)
  │
  └── Supabase (PostgreSQL)
      ├── Direct connection string in git (DB_URL with credentials)
      └── RLS policies exist but service_role key is also committed
```

**Attack Priority**: Chatbot (no auth) > Supabase (credentials in git) > Backend (docs if exposed)
