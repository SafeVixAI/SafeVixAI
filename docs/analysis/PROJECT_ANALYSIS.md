# SafeVixAI — Complete Project Analysis (Updated 2026-05-26)

> **SNAPSHOT**: This document reflects the state as of 2026-05-26. For current state see [AGENTS.md](../../AGENTS.md).

> Deep codebase exploration complete. Contains verified ground truth (not audit tool assumptions).

---

## 1. Project Identity

**SafeVixAI** — Full-stack AI-powered road safety PWA for AI-powered road safety platform.
Total infra cost: ?0.

| Problem | Solution |
|---------|----------|
| Emergency Locator | PostGIS-powered nearest service finder (hospitals, police, fire) with radius expansion up to 50km |
| AI Chatbot | 10-provider LLM fallback chain, ChromaDB RAG (Motor Vehicles Act + first-aid + accident data), 13 agent tools |
| Challan Calculator | Dual-path (DuckDB-Wasm client-side + Python server-side) fine calculation with state overrides |
| Road Reporter | Community hazard reporting with photo upload, authority routing, OSM contribution, Waze CIFS feed |

---

## 2. Architecture

```
Frontend (Next.js 15, React 19, Port 3000)         ? Vercel
  +-- 23 routes (17 pages + special files)
  +-- 55+ components across 6 sub-directories
  +-- Zustand store (16 state slices, persist middleware)
  +-- MapLibre GL (custom marker rendering, NOT Leaflet/maplibregl.Marker)
  +-- GSAP 3.15 (ScrollTrigger, Flip, Observer, CustomEase)
  +-- @huggingface/transformers (YOLO pothole detection)
  +-- @duckdb/duckdb-wasm (offline challan SQL)
  +-- Service Worker (safevixai-v3, manual management)
  +-- SWR (underutilized — only in challan page)
  +-- i18next (14 language hreflang, ThemeProvider custom)

Backend (FastAPI, Port 8000)                         ? Render
  +-- 35+ REST endpoints + 1 WebSocket + SSE
  +-- 14 service modules + civic intel sub-package
  +-- Auth: PBKDF2 + JWT (dual validator: app JWT + Supabase JWT)
  +-- Rate limiting: slowapi, IP-based, 5-40 req/min per endpoint
  +-- PostGIS + Redis + Supabase Storage
  +-- 18 Alembic migrations (001 to enterprise tables)
  +-- Security headers, CSRF, idempotency, request ID, Prometheus

Chatbot Service (FastAPI, Port 8010)                 ? Render
  +-- ChatEngine (LangGraph graph with safety ? intent ? context ? provider)
  +-- 9 real LLM providers + 1 deterministic fallback (Template)
  +-- ChromaDB RAG (real semantic embeddings via sentence-transformers)
  +-- 13 agent tools (SOS, Challan, FirstAid, Weather, Road, etc.)
  +-- Speech translation (IndicSeamless — uses torch, handled gracefully)
  +-- Circuit breakers per provider (graduated cooldown: 60s to 24h)
  +-- Redis conversation memory (fallback: in-memory LRU)
  +-- Prometheus metrics (11 instruments)
  +-- SafetyChecker (60+ harm patterns, l33t decode, 20+ jailbreak patterns)
```

---

## 3. Corrected Audit Findings

| Claim from previous audit | Verdict | Reality |
|--------------------------|---------|---------|
| `admin123` hardcoded in auth.py | **FALSE** | Uses PBKDF2 + AUTH_OPERATOR_EMAIL env var. No hardcoded password. |
| `mock-jwt-token` accepted | **FALSE** | REJECTED_STATIC_TOKENS set explicitly blocks these (security.py:44-49) |
| RAG is lexical not ChromaDB | **FALSE** | ChromaDB with sentence-transformers, lexical is fallback only |
| Crash detection shows TOAST only | **PARTIAL** | EnterpriseClientAppHooks renders CrashCountdown; ClientAppHooks is orphaned |
| SOS is GET not POST | **FALSE** | BOTH exist — GET (quick lookup) + POST (incident creation) |
| CORS wildcard with credentials | **MISLEADING** | .env CORS_ORIGINS blocks '*' in production; config validates |
| Chatbot report tool sends wrong field names | **VERIFIED** | Uses `data=` (form-encoded) not `json=`, field names match backend |
| Waze feed imports nonexistent module | **FALSE** | Uses proper imports from backend.core.config |
| JWT_SECRET_KEY regenerated on every restart | **PARTIAL** | Only in dev; production requires JWT_SECRET_KEY env var |
| User profile ownership checks missing | **PARTIAL** | Backend endpoints require auth but no user_id verification found |

### 3.1 Remaining Critical Issues (Verified as Live)

1. **ALL 3 .env files committed with live credentials** — 15+ API keys, JWT secret, Gmail app password, Supabase service role key
2. **SafetyChecker.check_output_safety() and add_medical_disclaimer_if_needed() are defined but NEVER called** (dead code)
3. **SWR used only in 1 of 23 pages** — most data fetching via raw Axios with manual retry
4. **Chatbot SubmitReportTool uses `data=` not `json=`** — works but non-standard for JSON API
5. **safevixai.com hardcoded in 16 hreflang URLs** — should use NEXT_PUBLIC_APP_URL
6. **torch 2.12.0 in chatbot requirements (800MB > Render 512MB RAM)** — only for speech, graceful fallback exists
7. **EmergencyTool instantiated but never wired into ContextAssembler** — orphan tool
8. **Dead code in context_assembler.py** — 3 route context methods defined but never called
9. **No data retention policies** — SOS incidents persist forever
10. **Next.js docs enabled in production** — /docs and /redoc accessible unless ENVIRONMENT=production

---

## 4. Security-Sensitive Systems (Verified)

| System | Risk | Notes |
|--------|------|-------|
| Live credentials in git | **CRITICAL** | All 3 .env files have production secrets committed and tracked |
| JWT Auth | HIGH | HS256 symmetric, 24h expiry, no revocation mechanism |
| Auth token in IndexedDB | HIGH | JWT stored in offline queue with GPS PII |
| Chatbot API auth | HIGH | Rate-limited (5/min) but no token required for chat endpoints |
| No RBAC enforcement | HIGH | JWT role claim unused in most endpoint checks |
| No Host header validation | MEDIUM | No ALLOWED_HOSTS check — potential Host header injection |
| CSP with unsafe-inline | MEDIUM | Required by Next.js; unsafe-eval in dev only |
| Sentry DSN (if exposed) | MEDIUM | Traces sample rate 0.1 in dev; production config depends on env |

---

## 5. Scaling Risks

| Risk | Impact | Current State |
|------|--------|---------------|
| Render free tier 512MB RAM | Backend OOM under load | Single worker, pool=1 |
| Render 750h/month limit | Services spin down | ~1464h needed for 2 services |
| Upstash Redis 10K commands/day | Rate limiting and cache disabled | In-memory fallback works |
| LLM API rate limits | Chatbot degraded | 10-provider chain handles failover |
| Single-threaded workers | No request parallelism | Keep-alive, I/O-bound design |

---

## 6. Operationally Critical Workflows

1. **Emergency SOS Dispatch** — Must work with POST, offline via IndexedDB queue, auto-flush on reconnect
2. **Chatbot LLM Generation** — 10 providers in chain, TemplateProvider as final deterministic fallback
3. **Crash Detection** — Accelerometer + 20s countdown ? auto-dispatch; false positives acceptable, false negatives not
4. **Database Migration** — 18 Alembic versions, PostgreSQL+PostGIS required, RLS policies applied
5. **Offline Data Sync** — SOS + road report queues in IndexedDB v2, per-item atomic delete-after-send
