# SafeVixAI — Service Interaction Map

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

> Generated: 2026-05-22 | All inter-service and intra-service interactions

---

## 1. Backend → External API Interactions

```
EmergencyLocatorService
  │
  ├── CacheHelper.get_json()           → Redis/In-memory
  ├── PostGIS ST_DWithin query         → Supabase PostgreSQL
  ├── LocalEmergencyCatalog CSV load   → Local filesystem
  └── OverpassService.search_services() → Overpass API (3 mirrors)
       └── Healthsites.io query (fallback)

ChallanService
  ├── PostGIS traffic_violations query  → Supabase PostgreSQL
  └── CSV file load (violations.csv)   → Local filesystem

GeocodingService
  ├── CacheHelper.get_json()           → Redis/In-memory
  ├── Photon API reverse/search        → photon.komoot.io
  └── Nominatim API reverse/search     → nominatim.openstreetmap.org
       └── Rate limited: 1 req/s via asyncio.Lock

RoutingService
  ├── CacheHelper.get_json()           → Redis/In-memory
  ├── OpenRouteService API            → api.openrouteservice.org
  └── OSRM API (fallback)             → router.project-osrm.org

RoadWatchService
  ├── CacheHelper.get_json/set_json    → Redis/In-memory
  ├── PostGIS road_issues query        → Supabase PostgreSQL
  ├── GeocodingService.reverse()       → Internal
  ├── AuthorityRouter.resolve()        → Internal
  │   ├── PostGIS road_infrastructure  → Supabase PostgreSQL
  │   └── OverpassService.get_road_context() → Overpass API
  ├── ReportClassifier.classify()      → Internal (rule-based NLP)
  ├── OSMContributor.contribute_report() → OpenStreetMap API v0.6
  └── Supabase Storage upload          → Supabase Storage

LLMService (Chat proxy)
  └── Chatbot Service HTTP POST        → chatbot:8010/api/v1/chat/

MCP Server
  ├── EmergencyLocatorService          → Internal
  ├── ChallanService                   → Internal
  ├── RoutingService                   → Internal
  └── Local first-aid JSON             → Local filesystem

LiveTracking
  ├── PostGIS live_tracking table      → Supabase PostgreSQL
  └── JWT view_token generation        → Internal (security.py)

AlertService (root)
  └── Gmail SMTP (smtp.gmail.com:587) → Email
```

---

## 2. Chatbot → External API Interactions

```
ChatEngine
  │
  ├── SafetyChecker.evaluate()         → Internal (regex-based)
  ├── IntentDetector.detect()          → Internal (keyword-based)
  ├── ContextAssembler.assemble()
  │   ├── SosTool                      → Backend GET /api/v1/emergency/sos
  │   │   ├── + What3Words API
  │   │   └── + Nominatim reverse
  │   ├── EmergencyTool                → Backend GET /api/v1/emergency/nearby
  │   ├── ChallanTool                  → Backend POST /api/v1/challan/calculate
  │   │   └── + IP-based state detection
  │   ├── LegalSearchTool              → ChromaDB (local)
  │   ├── FirstAidTool                 → Local JSON (first_aid.json)
  │   ├── WeatherTool                  → Open-Meteo → OpenWeather (fallback)
  │   ├── RoadInfrastructureTool       → Backend GET /api/v1/roads/infrastructure
  │   ├── RoadIssuesTool               → Backend GET /api/v1/roads/issues
  │   ├── SubmitReportTool             → Backend POST /api/v1/roads/report
  │   ├── GeocodingClient              → Nominatim → OpenCage (fallback)
  │   ├── DrugInfoTool                 → Open FDA API
  │   └── What3WordsTool               → What3Words API
  │
  ├── ProviderRouter.generate()
  │   ├── Groq API (primary)
  │   ├── Cerebras API
  │   ├── Gemini API
  │   ├── GitHub Models API
  │   ├── NVIDIA NIM API
  │   ├── OpenRouter API
  │   ├── Mistral API
  │   ├── Together API
  │   ├── Sarvam API → HF Inference (fallback)
  │   └── TemplateProvider (deterministic fallback, no network)
  │
  ├── ConversationMemoryStore.append() → Redis / In-memory
  ├── LLMResponseCache                 → Redis
  └── AIGovernance.evaluate()          → Internal (keyword-overlap)

IndicSeamlessService
  └── Meta SeamlessM4T v2 model       → Local (ai4bharat/indic-seamless)
      └── torch, torchaudio, transformers
```

---

## 3. Frontend → Internal API Interactions

```
Frontend (Next.js)
  │
  ├── useAppStore (Zustand)            → In-memory + IndexedDB persist
  │
  ├── api.ts client (axios)
  │   ├── GET  /api/v1/emergency/nearby    → Backend
  │   ├── GET  /api/v1/emergency/sos       → Backend
  │   ├── POST /api/v1/emergency/sos       → Backend
  │   ├── GET  /api/v1/emergency/numbers   → Backend
  │   ├── POST /api/v1/emergency/anonymous → Backend
  │   ├── POST /api/v1/challan/calculate   → Backend
  │   ├── POST /api/v1/chat/              → Backend (proxied to chatbot)
  │   ├── POST /api/v1/chat/stream        → Backend (proxied SSE)
  │   ├── GET  /api/v1/roads/issues       → Backend
  │   ├── POST /api/v1/roads/report       → Backend (multipart)
  │   ├── GET  /api/v1/routing/preview    → Backend
  │   ├── GET  /api/v1/geocode/search     → Backend
  │   ├── POST /api/v1/live-tracking/start → Backend
  │   └── GET  /api/v1/offline/bundle/{city} → Backend
  │
  ├── streamChat() (SSE)
  │   └── POST /api/v1/chat/stream       → Backend (SSE proxy to chatbot)
  │
  ├── WebSocket /api/v1/tracking/{group_id} → Backend
  │
  ├── Supabase Auth
  │   └── supabase.auth.getSession()     → Supabase Auth
  │
  ├── IndexedDB (idb/IDB)
  │   ├── safevix-offline-db.sos-queue          → Local (stored SOS triggers)
  │   └── safevix-offline-db.road-report-queue  → Local (stored reports)
  │
  ├── DuckDB-Wasm
  │   └── violations.csv parsing + SQL queries  → Local (WASM)
  │
  ├── WebLLM / Transformers.js
  │   └── Gemma 4 / Phi-3 model inference       → Local (WASM/WebGPU)
  │
  ├── Service Worker
  │   ├── Cache: safevixai-v3                  → Cache Storage
  │   ├── Sync: sos-queue-flush                → Background Sync
  │   └── Sync: road-report-queue-flush         → Background Sync
  │
  ├── Web Speech API
  │   └── SpeechRecognition + speechSynthesis   → Browser API
  │
  └── DeviceMotion API
      └── accelerationIncludingGravity           → Browser API
```

---

## 4. Inter-Service Communication Patterns

```
┌──────────────────────────────────────────────────────────────────┐
│                    SYNCHRONOUS (REST/HTTP)                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Frontend → Backend (axios, withCredentials)                      │
│    └── All API calls, JWT in cookie/Bearer header                │
│    └── CSRF token in X-CSRF-Token header                         │
│    └── Exponential backoff retry (3 attempts)                    │
│    └── 8s default timeout                                        │
│                                                                   │
│  Frontend → Chatbot (axios, direct)                              │
│    └── Chat streaming (SSE via ReadableStream)                   │
│    └── 15s default timeout                                        │
│                                                                   │
│  Backend → Chatbot (httpx, proxy)                                │
│    └── LLMService proxies POST /api/v1/chat/ to chatbot         │
│    └── 20s timeout                                                │
│    └── Fallback response on failure                              │
│                                                                   │
│  Chatbot → Backend (httpx, via BackendToolClient)                │
│    └── SOS, Challan, Emergency, Road endpoints                   │
│    └── 20s timeout                                                 │
│    └── Tools return None on failure, ContextAssembler handles    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    STREAMING (SSE)                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Frontend ←stream→ Backend ←stream→ Chatbot                      │
│    └── Chat streaming pipeline                                   │
│    └── Frontend: ReadableStream.getReader()                      │
│    └── Backend: httpx stream proxy                               │
│    └── Chatbot: Word-split simulation (12ms/delay)               │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    REALTIME (WebSocket)                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Frontend ←WS→ Backend                                           │
│    └── /api/v1/tracking/{group_id}                               │
│    └── JWT auth via query param                                  │
│    └── Redis Pub/Sub for multi-instance broadcast                │
│    └── 4096 byte max message size                                │
│    └── CORS origin validation on connect                         │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    EVENT-DRIVEN (Background Sync)                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Service Worker → Backend (on online event)                       │
│    └── SOS queue flush (IndexedDB → POST /api/v1/emergency/sos)  │
│    └── Road report flush (IndexedDB → POST /api/v1/roads/report) │
│    └── Atomic per-item: delete only after successful POST        │
│    └── Background Sync API + online event listener               │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    DATA FLOW (Database)                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Backend ↔ PostgreSQL (asyncpg)                                  │
│    └── All ORM queries via SQLAlchemy async session              │
│    └── Raw spatial queries via text() with bind params           │
│    └── Connection pool: 10 (dev), 1 (Render prod)               │
│                                                                   │
│  Backend ↔ Redis (redis-py)                                     │
│    └── Cache store (geocode, routes, emergency, etc.)           │
│    └── Rate limiting (slowapi Redis backend)                    │
│    └── Idempotency store                                        │
│                                                                   │
│  Chatbot ↔ Redis (redis-py)                                     │
│    └── Conversation memory (TTL: 24h)                           │
│    └── LLM response cache                                        │
│                                                                   │
│  Chatbot ↔ ChromaDB (local filesystem)                          │
│    └── Legal, medical, accident vector search                    │
│    └── LocalHashEmbeddingFunction (384-dim)                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Authentication Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    AUTH SERVICE INTERACTIONS                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Login:                                                           │
│    Frontend → POST /api/v1/auth/login                            │
│      → Backend verifies PBKDF2 password hash                     │
│      → Creates JWT (HS256, 24h expiry)                           │
│      → Sets HttpOnly cookie (access_token)                       │
│      → Returns token in body                                     │
│      → Frontend stores in Zustand (memory only, not persisted)   │
│                                                                   │
│  Auth Verification (per request):                                │
│    → Backend checks cookie first (get_current_user)              │
│    → Falls back to Authorization: Bearer header                  │
│    → Decodes: App JWT → Supabase JWT → JWKS                     │
│    → Returns {sub, role, org_id} or 401                          │
│                                                                   │
│  Supabase Auth (alternative):                                    │
│    Frontend → supabase.auth.signInWithPassword()                 │
│      → Supabase returns session with JWT                         │
│      → Backend _decode_supabase_token() validates                │
│      → Uses SUPABASE_JWT_SECRET, aud=authenticated              │
│                                                                   │
│  Offline Auth (SOS queue):                                       │
│    → Captures authToken = localStorage.getItem('access_token')   │
│    → Stores in IndexedDB alongside SOS data                      │
│    → Replayed when online via Service Worker or fetch            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Error Propagation

```
Chain 1: LLM Generation Failure
────────────────────────────
  ProviderRouter.generate()
    → Provider A (Groq): Timeout/Error
    → Provider B (Cerebras): Rate limited
    → Provider C (Gemini): API error
    ...
    → Provider J (Template): Always succeeds
      └── If all 9 fail:
          → alert_service.alert_all_providers_failed()
          → TemplateProvider returns generic response

Chain 2: Backend Service Failure
────────────────────────────
  EmergencyLocatorService.find_nearby()
    → Cache: Redis fail → In-memory fallback
    → DB: Supabase fail → Log → Jump to Tier 2 (CSV)
    → CSV: File not found → Log → Jump to Tier 3 (Overpass)
    → Overpass: All mirrors fail → alert → Return empty
    → Final: Empty array with source="all-fallbacks-exhausted"

Chain 3: Chatbot → Backend Failure
────────────────────────────
  ContextAssembler → Tool calls Backend API
    → BackendToolClient: httpx error/timeout
    → Tool returns None
    → ContextAssembler continues with partial context
    → LLM generates response with available context only
    → No crash, degraded experience

Chain 4: Frontend → Chatbot Failure
────────────────────────────
  ChatInterface.streamChat()
    → SSE connection fails
    → Fall back to POST /api/v1/chat/ (non-streaming)
    → If that also fails:
      → Fallback to offline AI (Transformers.js/WebLLM)
      → If no offline model → keyword fallback (15 responses)
      → Show connectivity badge
```
