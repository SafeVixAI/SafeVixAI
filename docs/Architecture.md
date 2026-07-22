# SafeVixAI — Architecture v3.1

> **IIT Madras Road Safety Hackathon 2026** | Free & open-source (₹0 infra cost)

---

## Three-Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  frontend/         Next.js 15 + React 19 + TypeScript PWA   │
│  Port 3000         MapLibre GL 5, WebLLM, DuckDB-Wasm       │
│                    Zustand state, Tailwind CSS, GSAP         │
└──────────────┬──────────────────────────┬───────────────────┘
               │ REST/WS (JWT Bearer)      │ REST (JWT Bearer)
┌──────────────▼─────────┐  ┌─────────────▼──────────────────┐
│  backend/              │  │  chatbot_service/              │
│  FastAPI :8000         │  │  FastAPI :8010                  │
│  PostgreSQL + PostGIS  │◄─┤  10-provider LLM fallback     │
│  Redis cache           │  │  ChromaDB RAG vectorstore       │
│  DuckDB (challan SQL)  │  │  13 agent tools                 │
│  Overpass/Nominatim    │  │  Redis conversation memory      │
│  WebSocket /tracking   │  │  Prompt injection defense       │
│  28 API route modules  │  │  IndicSeamless speech           │
│  CQRS bus + Redlock    │  │  Lang detection + provider reg  │
└────────────────────────┘  └────────────────────────────────┘
```

| Service | Port | Tech Stack | Purpose |
|---------|------|------------|---------|
| **Backend** | 8000 | FastAPI, PostgreSQL + PostGIS, Redis, DuckDB | Emergency locator, challan calc, road reporting, geocoding, live tracking, auth |
| **Chatbot Service** | 8010 | FastAPI, ChromaDB, 10 LLM providers, Redis | Agentic RAG chatbot, Indian language AI, speech translation |
| **Frontend** | 3000 | Next.js 15, React 19, MapLibre GL 5, Tailwind CSS, GSAP | PWA UI, maps, offline AI (WebLLM), offline SQL (DuckDB-Wasm) |

> **Critical:** Backend and Chatbot Service have **separate** `.venv`, `.env`, `requirements.txt`, and `Dockerfile`. Never mix their dependencies.

---

## System Architecture Overview

```mermaid
graph TD
    A[User Device - Browser] --> B[Next.js 15 PWA on Vercel CDN]

    B --> C[Emergency Locator]
    B --> D[AI Chat - Online]
    B --> E[Challan Calculator]
    B --> F[Road Reporter]

    B --> G[Browser Offline Layer]
    G --> G1[WebLLM Phi-3 Mini]
    G --> G2[DuckDB-Wasm]
    G --> G3[IndexedDB + Service Worker]
    G --> G4[GeoJSON + Turf.js]

    B -->|HTTPS| H[FastAPI Backend :8000 on Render.com]
    B -->|HTTPS| CS[FastAPI Chatbot Service :8010 on Render.com]

    H --> H1[Emergency API - PostGIS + Overpass]
    H --> H3[Challan Service - DuckDB SQL]
    H --> H4[RoadWatch Service - Authority Matrix]
    H -->|proxy| CS

    CS --> CS1[ChatEngine - Agentic RAG]
    CS --> CS2[10-provider LLM Fallback Chain]
    CS --> CS3[13 Agent Tools]
    CS --> CS4[Sarvam AI - Indian Language Routing]
    CS --> CS5[ChromaDB RAG Vectorstore]

    H --> I[Core Services]
    I --> I1[Redis Cache - Upstash]
    I --> I2[PostGIS Queries]
    I --> I3[Nominatim Geocoding]

    H --> J[External Free Services]
    J --> J1[Supabase PostgreSQL + PostGIS]
    J --> J2[Upstash Redis]
    J --> J3[OSM Overpass API]
    J --> J4[HuggingFace Hub - WebLLM CDN]
```

---

## Backend (FastAPI :8000)

### 28 Route Modules (registered in `api/v1/__init__.py`) + 1 MCP Server

All routes live in `backend/api/v1/`:

| Module | Endpoints | Auth |
|--------|-----------|------|
| `admin.py` | Admin-only operations (system config, user management) | Admin secret |
| `analytics.py` | Heatmaps, summaries, ward-level analytics | JWT + Admin |
| `auth.py` | JWT login, signup, refresh, logout | Public / JWT |
| `authority.py` | Authority lookup and management | JWT |
| `challan.py` | Fine calculation (DuckDB-based query engine) | JWT / Public |
| `chat.py` | Chat proxy to chatbot service (`/api/v1/chat/`, `/api/v1/chat/stream`) | JWT |
| `circuit_breaker_api.py` | Circuit breaker status and reset | JWT |
| `citizen.py` | Citizen dashboard and service history | JWT |
| `civic_intel.py` | LGD codes, municipality info, administrative boundaries | Public |
| `civic_intel_municipalities.py` | Municipality CRUD, stats, rankings | Public |
| `civic_intel_streetlights.py` | Streetlight QR/nearby/outage/maintenance | Public / JWT |
| `command_center.py` | Emergency command center coordination | JWT |
| `emergency.py` | Emergency locator, SOS triggers, nearby services | JWT / Public |
| `field_workflow.py` | Field worker task management | JWT |
| `garage.py` | Vehicle/garage management | JWT |
| `geocode.py` | Geocoding forward/reverse (Nominatim, Photon) | JWT / Public |
| `live_tracking.py` | WebSocket-based live location tracking | JWT + WS |
| `mcp_server.py` | MCP protocol server (SSE + messages) for external agents | JWT |
| `officers.py` | Police/traffic officer management | JWT |
| `offline.py` | Offline data sync bundles | JWT |
| `providers.py` | AI provider API key management (encrypt/decrypt) | JWT |
| `public.py` | Unauthenticated public endpoints | None |
| `roadwatch.py` | Road issue reporting, photo uploads, status tracking | JWT Optional |
| `routing.py` | Route calculation, safe routing suggestions | JWT |
| `tracking.py` | Location tracking session CRUD | JWT |
| `user.py` | User profile management | JWT |
| `wards.py` | Ward boundary and metadata management | JWT |
| `waze_feed.py` | Waze community traffic/hazard data feed | JWT |

### Middleware Stack (applied in order)

```
Request
  ├── IdempotencyMiddleware        — Idempotency-Key header dedup
  ├── APIVersioningMiddleware       — Accept header / URL prefix version routing
  ├── SecurityHeadersMiddleware     — HSTS, CSP, X-Frame-Options, X-Content-Type-Options
  ├── RequestIDMiddleware           — X-Request-ID / X-Correlation-ID injection
  ├── PrometheusMetricsMiddleware   — Request count, latency, error metrics
  ├── CSRFMiddleware                — CSRF token validation for state-changing requests
  ├── TenantIsolationMiddleware     — Multi-tenant data boundary enforcement
  ├── AllowedHostsMiddleware        — Host header whitelist validation
  ├── QueryProfilerMiddleware       — Slow query logging and analysis
  ├── GeoJSONCompressionMiddleware  — Compress large GeoJSON responses
  ├── CORSCheckMiddleware           — CORS origin pre-validation
  ├── FastAPI CORSMiddleware        — Standard CORS headers
  └── ApiResponseMiddleware         — Uniform API envelope wrapping
Response
```

### 18+ Service Modules

All services in `backend/services/`:

| Service Module | Purpose |
|----------------|---------|
| `emergency_locator.py` | Radius search via PostGIS `ST_DWithin`, Overpass fallback, caching |
| `challan_service.py` | DuckDB SQL fine calculation from violations CSV |
| `geocoding_service.py` | Nominatim/Photon forward/reverse geocoding |
| `overpass_service.py` | OSM Overpass API query builder + rate limiter |
| `routing_service.py` | Route calculation using OpenRouteService |
| `safe_routing.py` | Safety-weighted route scoring |
| `safe_spaces.py` | Safe space (well-lit, CCTV) identification |
| `roadwatch_service.py` | Road issue lifecycle management |
| `roadwatch_photos.py` | Photo validation, EXIF stripping, Supabase upload |
| `roadwatch_moderation_service.py` | AI text moderation + EXIF authenticity verification |
| `city_center_repo.py` | DB-backed Indian metro city centers with hardcoded fallback |
| `authority_router.py` | ONDC-compliant authority routing matrix |
| `llm_service.py` | LLM proxy for basic text generation |
| `local_emergency_catalog.py` | Local emergency contact database |
| `event_bus.py` | Internal pub/sub event bus |
| `sla_monitor.py` | Service level agreement compliance tracking |
| `escalation_predictor.py` | ML-based issue escalation prediction |
| `fine_prediction_service.py` | Fine amount prediction model |
| `fraud_detector.py` | Report/claim fraud detection |
| `report_classifier.py` | Road issue severity classification |
| `duplicate_detector.py` | Duplicate report deduplication |
| `complaint_lifecycle.py` | Complaint state machine (filed → investigating → resolved) |
| `garage_service.py` | Garage/vehicle CRUD + availability |
| `officer_route_optimizer.py` | Patrol route optimization |
| `workload_balancer.py` | Officer workload distribution |
| `ward_service.py` | Ward boundary and metadata operations |
| `streetlight_service.py` | Streetlight inventory and fault reporting |
| `data_retention.py` | Automated data lifecycle management |
| `geo_verifier.py` | Geographic coordinate sanity checks |
| `ai_verification.py` | ML-based photo/report authenticity verification |
| `osm_contributor.py` | Automated OSM data contribution |
| `exceptions.py` | Custom exception definitions |
| `civic_intel/` | **Civic intelligence directory (10 modules)** |
| `civic_intel/base_ingestor.py` | Base class for all ETL ingestors |
| `civic_intel/civic_analytics_service.py` | LGD/Admin/OSM/Grievances/Municipalities stats |
| `civic_intel/osm_bulk_ingestor.py` | Streaming OSM data ingestor (iter_parse_elements) |
| `civic_intel/etl_scheduler.py` | Background ETL pipeline scheduler (asyncio) |
| `civic_intel/lgd_ingestor.py` | Local Government Directory ingestor |
| `civic_intel/boundary_ingestor.py` | Administrative boundary ingestor |
| `civic_intel/datagov_ingestor.py` | Government open data ingestor |
| `civic_intel/municipal_ingestor.py` | Municipality data ingestor |
| `civic_intel/grievance_ingestor.py` | Grievance data ingestor |
| `civic_intel/data_exporter.py` | Civic data export utility |

### Core Config (pydantic-settings)

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://...` - auto-normalized from `postgres://` |
| `REDIS_URL` | No | Falls back to in-memory cache (dict) |
| `CHATBOT_SERVICE_URL` | Yes | Default: `http://localhost:8010/api/v1` |
| `ADMIN_SECRET` | Yes | Protects admin-only endpoints |
| `JWT_SECRET_KEY` | Yes | HS256 signing for JWT tokens |
| `JWT_ALGORITHM` | No | Default: `HS256` |
| `SUPABASE_JWT_SECRET` | No | For Supabase JWT validation |
| `SUPABASE_JWT_AUDIENCE` | No | Supabase JWT audience claim |
| `ALLOWED_HOSTS` | Yes | Comma-separated Host header whitelist |
| `SENTRY_DSN` | No | Optional Sentry error tracking |
| `OPENROUTESERVICE_API_KEY` | No | For routing; free tier available |
| `DATA_GOV_API_KEY` | No | Government data endpoints |
| `CORS_ORIGINS` | No | Comma-separated CORS allowed origins |
| `MCP_ENABLED` | No | Enables MCP server (default: false) |
| `ETL_ENABLED` | No | Enables background ETL scheduler (default: false) |
| `CHATBOT_INTERNAL_API_KEY` | No | Service-to-service auth key for chatbot ↔ backend |
| `JWKS_URL` | No | JWKS endpoint URL for RS256 JWT verification |
| `REDIS_TLS_ENABLED` | No | Enables `rediss://` TLS connection to Redis |
| `REDIS_PASSWORD` | No | Redis AUTH password |

---

### Enterprise Patterns

Enterprise-grade patterns added in Batch 16-22 hardening:

| Module | Pattern | Purpose |
|--------|---------|---------|
| `core/cqrs.py` | CQRS | Command and Query message bus with middleware support |
| `core/distributed_lock.py` | Redlock | Distributed locking with Redis + local asyncio lock fallback |
| `core/exception_handlers.py` | Domain Exceptions | Global handlers: DomainError (400), ResourceNotFoundError (404), InvalidTransitionError (409), IntegrityError (409) |
| `core/idempotency.py` | Idempotency Keys | Idempotency-Key header dedup with audit logging and distributed lock isolation |
| `core/security.py` | RS256 JWT | RS256 JWT validation with atomic JWKS fetching and distributed caching |
| `core/jwks.py` | JWKS Manager | Key rotation, caching (TTL-based), historical key fallback for gradual rotation |
| `core/alert.py` | Email Alerts | When all 10 LLM providers fail, sends email with 3 diagnostic solutions. 5-min cooldown. |
| `core/redis_client.py` | Stampede Protection | `get_json_with_stampede_protection()` — Redis SET NX EX mutex + stale-while-revalidate + retry |
| `models/values.py` | Value Objects | `Coordinates(lat, lon)` with haversine `distance_to()`, `Severity(level)` with `from_risk_score()`, `Distance(meters)` |
| `models/schemas_*.py` | Domain Schemas | 9 supplementary domain-specific Pydantic schema files alongside monolithic `schemas.py` |

---

## Chatbot Service (FastAPI :8010)

### Agentic RAG Architecture

```mermaid
flowchart TD
    A[User Message] --> B[SafetyChecker.evaluate]
    B -->|Blocked| C[Safety response]
    B -->|Pass| D[IntentDetector.detect]
    D --> E{9 intent classes}
    E -->|emergency| F1[SosTool]
    E -->|first_aid| F2[FirstAidTool]
    E -->|challan| F3[ChallanTool]
    E -->|legal| F4[LegalSearchTool]
    E -->|road_weather| F5[WeatherTool / OpenMeteoTool]
    E -->|safe_route| F6[EmergencyTool]
    E -->|road_infrastructure| F7[RoadInfrastructureTool]
    E -->|road_issue| F8[RoadIssuesTool / SubmitReportTool]
    E -->|general| F9[ContextAssembler]

    F1 --> G[Tool results]
    F2 --> G
    F3 --> G
    F4 --> G
    F5 --> G
    F6 --> G
    F7 --> G
    F8 --> G
    F9 --> G

    G --> H[ChromaDB RAG - top 5 chunks]
    H --> I[ProviderRouter.generate]
    I --> J{Language detection}
    J -->|Indian| K[Sarvam AI 30B / 105B]
    J -->|English| L[Groq → Cerebras → Gemini → ...]
    K --> M[ConversationMemoryStore.append]
    L --> M
    M --> N[ChatResponse]
```

### 10-provider LLM Fallback Chain

```mermaid
flowchart LR
    A[User Message] --> B{Language?}
    B -->|Indian| S[Sarvam AI]
    S --> S1[sarvam-30b General]
    S --> S2[sarvam-105b Legal]
    B -->|English| C[Groq 300+ tok/s]
    C -->|fail| D[Cerebras 2000+ tok/s]
    D -->|fail| E[Gemini 1M context]
    E -->|fail| F[GitHub Models]
    F -->|fail| G[NVIDIA NIM]
    G -->|fail| H[OpenRouter]
    H -->|fail| I[Mistral]
    I -->|fail| J[Together]
    J -->|fail| K[Template - deterministic fallback]
```

> Language detection is regex-based (Unicode script ranges for Devanagari, Tamil, Telugu, Kannada, Bengali, etc.) — no NLTK dependency.

### Indian Language Auto-Routing

- **Sarvam-30B** — General Indian language queries (Hindi, Tamil, Telugu, etc.)
- **Sarvam-105B** — Legal/challan queries in Indian languages (higher accuracy)
- If `SARVAM_API_KEY` is set → direct Sarvam API; otherwise falls back to `HF_TOKEN` via HuggingFace Inference API

### 13 Agent Tools

| Tool | Module | Purpose |
|------|--------|---------|
| **SosTool** | `tools/sos_tool.py` | Nearby emergency services via backend API |
| **EmergencyTool** | `tools/emergency_tool.py` | Emergency service phone/address lookup |
| **ChallanTool** | `tools/challan_tool.py` | Fine calculation via backend challan API |
| **LegalSearchTool** | `tools/legal_search_tool.py` | ChromaDB vector search (Motor Vehicles Act, MoRTH) |
| **FirstAidTool** | `tools/first_aid_tool.py` | Static JSON first-aid protocols |
| **WeatherTool** | `tools/weather_tool.py` | OpenWeather API current conditions |
| **OpenMeteoTool** | `tools/open_meteo.py` | Open-Meteo weather (visibility, precipitation) |
| **RoadInfrastructureTool** | `tools/road_infra_tool.py` | Road contractor data, budget info |
| **RoadIssuesTool** | `tools/road_issues_tool.py` | Community-reported road issues |
| **SubmitReportTool** | `tools/submit_report_tool.py` | Submit road damage reports |
| **GeocodingClient** | `tools/geocoding.py` | Photon/BigDataCloud geocoding |
| **DrugInfoTool** | `tools/drug_info.py` | Open FDA drug/medical information |
| **What3WordsTool** | `tools/what3words.py` | What3Words location resolution |

### Speech Translation

- `POST /speech/translate` — ASR + translation for 14 Indian languages
- `GET /speech/status` — Service health check
- `IndicSeamlessService` — Indian language ASR/TTS pipeline (IndicSeamless models)

---

## Frontend (Next.js 15 :3000)

### 28 Routes

```
/                          Landing / Home
/assistant                 AI chatbot assistant
/auth/*                    Authentication flow (callback, error)
/bystander                 Bystander mode — witness reporting
/challan                   Challan/fine calculator
/command-center            Emergency command center dashboard
/emergency                 Emergency locator
/emergency-card/[userId]   Shareable emergency QR card
/first-aid                 First-aid guide
/forgot-password           Password reset request
/guide                     Safety guide index
/guide/[slug]              Individual guide article
/landing                   Marketing landing page
/locator                   Nearby emergency services map
/login                     User login
/officer                   Officer dashboard
/offline                   Offline mode status/info
/privacy                   Privacy policy
/profile                   User profile (blood group, emergency contacts)
/report                    Report a road issue
/report/track              Track submitted report status
/reset-password            Password reset form
/settings                  App settings
/share-receive             Receive shared emergency card
/signup                    User registration
/sos                       SOS emergency trigger
/terms                     Terms of service
/track/[session_id]        Live tracking session view
/tracking                  Live tracking dashboard
```

### 52 Lib Modules

Key modules in `frontend/lib/`:

| Module | Purpose |
|--------|---------|
| `api.ts` | Axios client with JWT interceptor |
| `store.ts` | Zustand global state (GPS, services, AI mode, auth) |
| `swr-fetcher.ts` | 7 cached SWR hooks for data fetching |
| `duckdb-challan.ts` | DuckDB-Wasm offline challan calculation |
| `offline-ai.ts` | WebLLM Phi-3 Mini integration |
| `offline-sos-queue.ts` | IndexedDB-based SOS offline queue |
| `crash-detection.ts` | Accelerometer-based crash detection |
| `live-tracking.ts` | WebSocket live tracking client |
| `geolocation.ts` | GPS position tracking + permission management |
| `guest-auth.ts` | Anonymous UUID-based guest authentication |
| `languages.ts` | 14-language 4-code mapping (UI → recognition → speech → synthesis) |
| `public-env.ts` | Runtime environment variable access |
| `safety-constants.ts` | Safety configuration constants |
| `client-logger.ts` | Client-side structured logging |
| `utils.ts` | General utility functions |

### 91 Components (13 subdirectories)

```
components/
├── ui/               — shadcn/ui primitives (button, card, dialog, input, etc.)
├── maps/             — MapLibre GL map components (dynamic import, ssr: false)
├── auth/             — Login/signup forms, AuthGuard
├── chat/             — Chat interface, message bubbles, streaming text
├── crash/            — Crash detection overlay, CrashCountdown UI
├── dashboard/        — Citizen and officer dashboards
├── first-aid/        — First-aid step-by-step guides
├── guide/            — Safety guide cards and detail views
├── profile/          — User profile editor
├── report/           — Road issue report forms
├── search/           — Search suggestions, autocomplete
├── voice-input/      — VoiceInput component (14 Indian languages)
└── command-center/   — Emergency command center widgets
```

---

## Dual-Layer AI Architecture

Online RAG with multi-provider fallback when connected, full offline AI using WebLLM when not.

```mermaid
flowchart TD
    A[User sends message] --> B{Is network available?}

    B -->|YES| CS[Chatbot Service :8010]
    B -->|NO| D[WebLLM Phi-3 Mini - runs on device]

    CS --> CS1[IntentDetector - classify query]
    CS --> CS2[ContextAssembler - call tools]
    CS --> CS3[ChromaDB RAG - top 5 law/medical chunks]
    CS --> CS4[ProviderRouter - 10 LLM fallback]
    CS4 --> CS5{Indian language?}
    CS5 -->|YES| CS6[Sarvam AI 30B/105B]
    CS5 -->|NO| CS7[Groq → Cerebras → Gemini → ...]

    D --> D1[IndexedDB first-aid.json]
    D --> D2[Turf.js GeoJSON for nearby POI]

    CS6 --> E[Response to user]
    CS7 --> E
    D1 --> E
    D2 --> E
```

| Aspect | Online — Layer 1 | Offline — Layer 2 |
|--------|-----------------|-------------------|
| LLM | 10-provider chain (Groq primary) | WebLLM Phi-3-mini-4k (4-bit, 2.2GB) |
| Indian Languages | Sarvam AI (30B/105B) | English only |
| Runs on | Cloud (Groq/Gemini/etc.) | User's browser (WebGPU) |
| RAG | ChromaDB on chatbot service | None (static first-aid.json) |
| POI Search | PostGIS ST_DWithin | Turf.js haversine on GeoJSON |
| Challan | DuckDB SQL on backend | DuckDB-Wasm in browser |
| Cost | ₹0 (all free tiers) | ₹0 (local device compute) |

---

## 5-Layer Offline Architecture

```mermaid
graph LR
    L1[Layer 1 - App Shell] --> L1D["All UI, JS, CSS, fonts — Service Worker precache"]
    L2[Layer 2 - Emergency POI] --> L2D["india-emergency.geojson — Turf.js haversine"]
    L3[Layer 3 - Challan Calc] --> L3D["DuckDB-Wasm + violations.csv + state_overrides.csv"]
    L4[Layer 4 - AI Chatbot] --> L4D["WebLLM Phi-3 Mini ~2.2GB + first-aid.json"]
    L5[Layer 5 - Road Reports] --> L5D["IndexedDB + Background Sync — offline SOS queue"]
```

---

## Data Flow: Emergency Locator

```mermaid
sequenceDiagram
    participant U as User Browser
    participant F as Backend :8000
    participant R as Redis Cache
    participant P as PostGIS DB
    participant O as OSM Overpass

    U->>F: GET /api/v1/emergency/nearby?lat=X&lon=Y
    F->>R: Check cache key nearby:lat:lon
    R-->>F: HIT — return cached result
    F-->>U: Return cached hospitals/police/fire

    Note over F,R: On cache MISS:
    F->>P: ST_DWithin(geog, ST_MakePoint(lon,lat), 5000) ::geography
    P-->>F: Nearby emergency services
    F->>F: If count < 3, expand radius up to 50km
    F->>O: Fallback to Overpass API if still < 3
    O-->>F: Additional POI from OSM
    F->>R: Cache result for 1 hour
    F-->>U: EmergencyResponse with sorted results
    U->>U: Render MapLibre GL markers by category
```

> **Note:** `ST_MakePoint` takes **longitude FIRST**, latitude second. Always use `::geography` (meters), never `::geometry` (degrees).

---

## Data Flow: AI Chatbot (Agentic RAG)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend :3000
    participant CS as Chatbot Service :8010
    participant PR as ProviderRouter
    participant C as ChromaDB
    participant R as Redis
    participant BE as Backend :8000

    U->>FE: Types or speaks a message
    FE->>CS: POST /api/v1/chat/
    CS->>CS: SafetyChecker.evaluate()
    CS->>CS: IntentDetector.detect() — classify into 9 intents
    CS->>CS: ContextAssembler.assemble()

    alt Emergency intent
        CS->>BE: Call /api/v1/emergency/nearby
        BE-->>CS: Nearby services
    end
    alt Legal intent
        CS->>C: ChromaDB vector search — top 5 chunks
        C-->>CS: Relevant law text
    end

    CS->>R: Load conversation history
    R-->>CS: Previous messages
    CS->>PR: ProviderRouter.generate() with context
    PR->>PR: Auto-detect language → route to provider
    PR-->>CS: LLM response
    CS->>R: Store updated history
    CS-->>FE: ChatResponse (text + intent + sources)
    FE-->>U: Display formatted response
```

---

## Data Flow: Live Tracking

```mermaid
sequenceDiagram
    participant U as User Browser
    participant W as WebSocket Server
    participant R as Redis PubSub
    participant G as Group Members

    U->>W: ws://host/api/v1/tracking/{group_id}
    W->>W: Authenticate via JWT (query param)
    W->>R: Subscribe to group:group_id
    U->>W: {"type":"location","lat":13.08,"lon":80.27,"accuracy":10}
    W->>R: PUBLISH group:group_id location payload
    R-->>G: SUBSCRIBE receives location update
    G->>G: Update MapLibre GL markers in real-time
```

---

## Data Flow: RoadWatch (Road Issue Reporting)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend :3000
    participant BE as Backend :8000
    participant AI as AI Verification
    participant AR as Authority Router

    U->>FE: Submit road issue form + photo
    FE->>BE: POST /api/v1/roads/report (JWT optional)
    BE->>BE: Validate report data
    BE->>AI: Run AI verification on photo
    AI-->>BE: Verification score + severity
    BE->>AR: Route to appropriate authority (ONDC/SLA)
    AR-->>BE: Authority assigned
    BE-->>FE: ReportResponse with tracking ID
    FE-->>U: "Report filed — Track status"
    U->>FE: GET /report/track?id=XXX
    FE->>BE: GET /api/v1/roads/status/{id}
    BE-->>FE: Current status (filed → investigating → resolved)
```

---

## Monorepo Structure

```
SafeVixAI/
├── backend/                 FastAPI :8000
│   ├── main.py              App factory (create_app → lifespan → services)
│   ├── api/v1/              28 route modules (registered) + 1 MCP server
│   ├── core/                Config, database, redis, security, rate limiter, circuit_breaker, cqrs, alert
│   ├── services/            47 service modules (37 core + 10 civic_intel) — 17 wired in app.state
│   ├── models/              SQLAlchemy ORM (30) + Pydantic schemas + value objects
│   ├── middleware/           Middleware stack (3 registered + 7 inline decorators)
│   ├── migrations/          Alembic (25 versions: initial + GiST + city_centers + 22 autogenerated)
│   ├── scripts/             DB seeders + data transforms
│   └── data/                violations_seed.csv, state_overrides.csv, chroma_db/
│
├── chatbot_service/         FastAPI :8010
│   ├── main.py              App factory (create_app → lifespan → ChatEngine)
│   ├── agent/               ChatEngine graph, IntentDetector, SafetyChecker, ContextAssembler
│   ├── providers/           10 LLM providers + TemplateProvider + ProviderRouter
│   ├── rag/                 ChromaDB local vectorstore, Retriever, embeddings
│   ├── tools/               13 agent tools
│   ├── memory/              Redis conversation memory with session TTL
│   ├── services/            Speech translation (IndicSeamlessService)
│   └── data/                chroma_db/ (COMMITTED — never delete)
│
├── frontend/                Next.js 15 PWA
│   ├── app/                 28 routes + error.tsx
│   ├── components/          91 components across 13 subdirs
│   ├── lib/                 52+ modules
│   └── public/              manifest.json, theme-init.js, icons/, offline-data/
│
├── scripts/                 Root-level data pipeline + wiki automation
│   ├── app/                 3 DB seeders
│   └── data/                16 standalone fetchers/extractors
│
├── docs/                    18+ markdown docs + wiki/ (231 auto-generated API docs)
├── .github/workflows/       GitHub Actions CI/CD (8 workflows)
├── docker-compose.yml       5 services: postgres, redis, backend, chatbot, frontend
├── AGENTS.md                AI agent quick-reference
├── SETUP.md                 Full installation guide
└── README.md                Project overview
```

---

## Deployment

| Component | Platform | Notes |
|-----------|----------|-------|
| Frontend | Vercel | Auto-deploys from `main`; WASM support in `next.config.js` |
| Backend | Render.com | Free tier (512MB RAM); `render.yaml` at root |
| Chatbot Service | Render.com | Free tier (2GB RAM for torch); `chatbot_service/render.yaml` |
| Database | Supabase | PostgreSQL 16 + PostGIS; enable extension manually |
| Redis | Upstash | Serverless Redis; set `REDIS_URL` in both services |
| Docker (local) | docker-compose.yml | 5 services: postgres (PostGIS 16), redis 7, backend, chatbot, frontend |

### Infrastructure Cost: ₹0

All services use free tiers or open-source self-hosted alternatives:
- **Maps:** MapLibre GL (free, no API key) + OSM Overpass (free)
- **Geocoding:** Nominatim (free, with User-Agent header)
- **LLM APIs:** Groq, Cerebras, Gemini, GitHub Models, NVIDIA NIM, OpenRouter, Mistral, Together — all have free tiers
- **Database:** Supabase free tier (500MB, 1 CPU)
- **Redis:** Upstash free tier (256MB)
- **Compute:** Render.com + Vercel free tiers
- **WebLLM:** HuggingFace CDN (free)

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Two separate FastAPI services | Chatbot has heavy ML deps (torch ~2GB); backend stays lightweight |
| 10-provider LLM fallback | Zero downtime — if one API rate-limits, next takes over |
| Sarvam AI for Indian languages | Trained on 4 trillion Indic tokens; best Hindi/Tamil legal accuracy |
| DuckDB for challans (not LLM) | Deterministic SQL; LLMs hallucinate fine amounts |
| ChromaDB committed to git | Render cold-starts need pre-built vectorstore; rebuild takes 10 min |
| PostGIS over MongoDB | `ST_DWithin` with GIST index < 50ms; Mongo much slower for radius |
| MapLibre GL over Google Maps | Google Maps costs ₹; MapLibre is free and open source |
| Zustand over Redux | 90% less boilerplate; sufficient for this app's state |
| IndexedDB for user profile | Blood group never leaves device — privacy by architecture |
| 13-middleware middleware stack | Production-grade security, observability, and reliability |

---

## Safety Rules

- Any AI response about injuries **must** start with "Call 112 immediately" — enforced in `agent/safety_checker.py`
- Blood group, emergency contacts stored in IndexedDB only (never sent to server)
- Guest auth uses anonymous UUIDs — no PII required
- Prompt injection defense in chatbot safety checker

---

*Document version: 3.2 | IIT Madras Road Safety Hackathon 2026 | ₹0 Infrastructure | Enterprise Hardening Batch 26*
