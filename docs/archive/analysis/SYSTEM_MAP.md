# SafeVixAI — Complete System Map (Updated 2026-05-26)

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

> Verified connectivity and data flows from actual code. 23 routes, 35+ endpoints, 11 LLM providers, 13 agent tools.

---

## 1. Service Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND :3000 (Vercel)                                                    │
│  Next.js 15 + React 19 + TypeScript 6.0                                    │
│  PWA + SW (safevixai-v3) | MapLibre GL 5.22 | Zustand 4.5 | GSAP 3.15     │
│  @huggingface/transformers (YOLO) | @duckdb/duckdb-wasm (SQLite offline)    │
│  SWR (underutilized — challan only) | Axios (main HTTP)                    │
│  i18next (14 locales) | sonner (toast) | posthog-js (analytics)             │
└─────┬─────────────────────────────────────────────────────┬─────────────────┘
      │ REST + SSE Streaming (JWT Bearer)                    │ REST (public)
      │                                                      │
┌─────▼──────────────────────────┐   ┌──────────────────────▼─────────────────┐
│  BACKEND :8000 (Render)        │   │  CHATBOT SERVICE :8010 (Render)       │
│  FastAPI + Uvicorn (1 worker)  │   │  FastAPI + Uvicorn (1 worker)         │
│  SQLAlchemy async + GeoAlchemy │   │  LangGraph | ChromaDB | 11 Providers  │
│  PostGIS 16 + Redis 7          │   │  Redis (session) | sentence-transformers│
│  14 Services, 35+ Endpoints,   │   │  13 Agent Tools | SafetyChecker       │
│  18 Alembic Migrations         │   │  IndicSeamless (speech, torch-based)   │
│  PBKDF2 + JWT Auth             │   │  11 Prometheus metrics                 │
└─────┬──────────────────────────┘   └──────────────────────┬─────────────────┘
      │                                                     │
      │            ┌──────────────────────────┐              │
      │            │     DATA LAYER           │              │
      │            │                          │              │
      │            │  PostgreSQL 16 + PostGIS │              │
      │            │  7 tables + GIST indexes │              │
      │            │  (Supabase free tier)    │              │
      │            │                          │              │
      │            │  Redis 7 (Upstash)       │◄─────────────┘
      │            │  Cache + RateLimit       │  (session memory)
      │            │  + Conversation Memory   │
      │            │                          │
      │            │  ChromaDB (chatbot)      │
      │            │  persisted, committed    │
      │            └──────────────────────────┘
```

---

## 2. Route Map (23 Frontend Routes + 35+ Backend Endpoints)

### Frontend Routes
| Route | Component | Auth | Key APIs Called |
|-------|-----------|------|-----------------|
| `/` | Dashboard map | None | GPS, emergency/nearby, roads/issues |
| `/assistant` | ChatInterface | None | POST /api/v1/chat/stream |
| `/bystander` | Bystander Mode | None | GPS, report/roads |
| `/challan` | ChallanCalculator | None | POST /api/v1/challan/calculate (SWR) |
| `/emergency` | Emergency page | None | GET /emergency/sos, /emergency/nearby |
| `/emergency-card/[userId]` | EmergencyCardClient | Public (signed) | Profile data via hash param |
| `/first-aid` | FirstAidClient | None | Static JSON |
| `/locator` | Locator search | None | emergency/nearby, Nominatim |
| `/login` | Operator login | Form | POST /api/v1/auth/login |
| `/profile` | User profile | Optional | Supabase + IndexedDB |
| `/report` | ReportForm | None | POST /api/v1/roads/report |
| `/settings` | Settings | Optional | Local storage |
| `/sos` | SOS page | None | POST /emergency/sos, tracking/start |
| `/track/{session_id}` | Family tracking viewer | Signed token | WebSocket + GET /live-tracking/session |
| `/tracking` | Tracking management | Auth | POST/PUT tracking endpoints |
| `/share-receive` | Share Target handler | None | URL parser (Google Maps deep link) |
| `/offline` | Offline fallback | None | Static |

### Backend API Endpoints (35+)
| Group | File | Endpoints | Auth |
|-------|------|-----------|------|
| emergency | emergency.py | GET/POST /sos, GET /nearby, /numbers, /safe-spaces | Public |
| challan | challan.py | POST /calculate | Public |
| roads | roadwatch.py | GET /issues, /authority, /infrastructure, POST /report | Public (optional auth for report) |
| routing | routing.py | GET /preview, /safe-route | Public |
| geocode | geocode.py | GET /reverse, /search | Public |
| auth | auth.py | POST /login, /logout, GET /verify, POST /refresh, /revoke | Mixed |
| users | user.py | POST, GET/{id}, PUT/{id}, DELETE/{id}, /export | Auth required |
| live-tracking | live_tracking.py | POST /start, PUT /update, GET /session/{id}, DELETE | Auth + signed token |
| chat | chat.py | POST /, POST /stream | Auth (backend only) |
| admin | admin.py | GET /complaints, POST /assign, GET /officers, /dashboard | OPERATOR role |
| circuit-breaker | circuit_breaker_api.py | GET /, /reset, /trigger, /close | Auth/Admin |
| waze | waze_feed.py | GET /feeds/waze | Public |
| analytics | analytics.py | GET /heatmap, /ward-summary, /sla-breach, /category | Public |
| tracking (WS) | tracking.py | WebSocket /{group_id} | JWT in query |

---

## 3. Data Flow: Emergency SOS (Critical Path)

```
User SOS Press
  → SOSButton (frontend, double-tap verification)
  → navigator.onLine check
  → [Online]: POST /api/v1/emergency/sos (JSON body: lat, lon, user_agent)
     → Backend checks rate limit (10/min)
     → Creates SosIncident DB record
     → EmergencyLocatorService.find_nearby()
        → PostGIS query (ST_DWithin, ::geography, GIST index scan)
        → [If < 3 results]: increase radius (500m→1km→5km→10km→25km→50km)
        → [No DB results]: LocalEmergencyCatalog CSV fallback
        → [No CSV]: OverpassService (OpenStreetMap query)
     → Response: { services[], sos_id, message }
  → [Offline]: IndexedDB enqueueSOS()
     → Stores in safevix-offline-db v2, store: sos-queue
     → Registers Background Sync event 'sos-queue-flush'
     → On 'online' event → syncOfflineSOSQueue() → per-item atomic POST
  → Start family tracking: POST /api/v1/live-tracking/start
     → Creates tracking session with 4h read-only JWT
     → Returns shareable URL: /track/{session_id}#token={view_token}
  → Share via WhatsApp/SMS with GPS link
  → PostHog event: sosActivated

Crash Detection (parallel path):
  → Accelerometer listener (devicemotion event)
  → Total acceleration > 15G threshold
  → CrashCountdown shows 20s countdown (GSAP number flip)
  → [Cancel pressed]: Dismiss countdown, log cancellation
  → [Timer expires]: Auto-dispatch SOS (same flow as above)
```

---

## 4. Data Flow: Chatbot Message

```
User → ChatInterface → POST /api/v1/chat/stream (SSE)
  → Backend LLMService proxy (timeout 30s, fallback to local)
  → chatbot_service /chat endpoint (rate limit 20/min)
     → ConversationMemoryStore.get_history(session_id, limit=20)
     → SafetyChecker.evaluate() → [Blocked] → return blocked response
     → Summarizer.get_summary_for_history() (8+ messages triggers)
     → IntentDetector.detect() → 9 intent classes
     → IntentDetector.refine_intent() (follow-up detection)
     → ContextAssembler.assemble()
        → Intent routing (parallel tool calls per intent table)
        → ChromaDB query: sentence-transformers embedding → cosine search
        → [Score < 0.28 threshold]: return empty, LLM handles
     → ProviderRouter.generate()
        → Language detection (Unicode script ranges)
        → Indian language → Sarvam (30B or 105B for legal)
        → English → default provider (groq)
        → Circuit breaker check → [Tripped] → skip to next
        → LLM API call with asyncio.wait_for(timeout=30)
        → [429 RateLimit]: read Retry-After, mark provider, try next
        → [402 QuotaExhausted]: mark until midnight UTC, email alert
        → [403 InvalidKey]: email alert, mark provider dead
        → [503/504 Timeout]: circuit breaker, try next
        → [All fail]: TemplateProvider (deterministic, always works)
     → AIGovernance.evaluate() (hallucination check)
     → ConversationMemoryStore.append()
     → SSE streaming response
```

---

## 5. External API Dependency Matrix

| API | Used By | Rate Limit | Fallback | Has Circuit Breaker |
|-----|---------|-----------|----------|---------------------|
| Groq LLM | Chatbot | 30 RPM, 6000 TPM | Cerebras | YES (trips at 429) |
| Cerebras | Chatbot | 10 RPM | Gemini | YES |
| Gemini | Chatbot | 15 RPM, 1M tkns/day | GitHub Models | YES |
| GitHub Models | Chatbot | Bandwidth limits | NVIDIA NIM | YES |
| NVIDIA NIM | Chatbot | 1000 req/day | OpenRouter | YES |
| OpenRouter | Chatbot | Variable | Mistral | YES |
| Mistral | Chatbot | 500 RPM | Together | YES |
| Together | Chatbot | Variable | Template | NO (last non-template) |
| Sarvam AI | Chatbot | Credits-based | HF Inference | YES |
| Overpass | Backend | Fair use | 3 mirrors + Healthsites | NO (retry-based) |
| OpenRouteService | Backend | 2000/day | OSRM public | NO |
| Nominatim | Backend+Chatbot | 1 req/sec | Photon/OpenCage | NO (lock-based) |
| OpenWeather | Chatbot | 60/min, 1M/mo | Open-Meteo (free) | NO |
| What3Words | Chatbot | 50K/mo | None (core feature) | NO (3 retries) |
| Open FDA | Chatbot | Unlim | None | NO |
| MapTiler | Frontend | Freemium | OpenFreeMap | NO |
| TomTom | Frontend | 50K tiles/day | Google Maps raster | NO |
| PostHog | Frontend | Unlimited | None | NO |

---

## 6. Caching Strategy

| Cache Key | TTL | Backend | Invalidation |
|-----------|-----|---------|-------------|
| emergency:nearby | 3600s | Redis+Mem | TTL |
| geocode:reverse | 86400s | Redis+Mem | TTL |
| geocode:search | 86400s | Redis+Mem | TTL |
| route:preview | 900s | Redis+Mem | TTL |
| roads:issues:v{ver} | 3600s | Redis+Mem | Version increment on new report |
| roads:infra | 3600s | Redis+Mem | TTL |
| roads:authority | 3600s | Redis+Mem | TTL |
| chat:session:{id} | 86400s | Redis | TTL (24h) |
| LLM response | 3600s | Redis | SHA-256 hash key |
| idempotency | 86400s | Redis+Mem | TTL |
