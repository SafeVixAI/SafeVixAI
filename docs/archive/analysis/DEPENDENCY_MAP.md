# SafeVixAI — Complete Dependency Map

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

> Generated: 2026-05-22 | All internal + external dependencies

---

## 1. Internal Service Dependencies

```
┌─────────────────────────────┐
│       FRONTEND (:3000)      │
│  Next.js 15 + React 19      │
├─────────────────────────────┤
│ Depends On:                  │
│  └─ Backend (:8000)          │
│     └─ /api/v1/* endpoints   │
│  └─ Chatbot (:8010)          │
│     └─ /api/v1/chat/{stream} │
│  └─ Self (Service Worker)    │
│     └─ /sw.js, /offline-data │
└─────────────────────────────┘
          │           │
          ▼           ▼
┌─────────────────────────────┐     ┌─────────────────────────────┐
│       BACKEND (:8000)       │     │    CHATBOT SERVICE (:8010)  │
│  FastAPI + SQLAlchemy       │────▶│  FastAPI + Transformers     │
├─────────────────────────────┤     ├─────────────────────────────┤
│ 14 Internal Services:       │     │ 11+ Internal Components:   │
│  ├── EmergencyLocatorService│     │  ├── ChatEngine             │
│  ├── ChallanService         │     │  ├── SafetyChecker          │
│  ├── RoutingService         │     │  ├── IntentDetector         │
│  ├── GeocodingService       │     │  ├── ContextAssembler       │
│  ├── RoadWatchService       │     │  ├── ProviderRouter         │
│  ├── LLMService (proxy)     │     │  ├── ConversationMemory    │
│  ├── OverpassService        │     │  ├── LocalVectorStore      │
│  ├── AuthorityRouter        │     │  ├── Retriever              │
│  ├── SafeSpacesService      │     │  ├── IndicSeamlessService   │
│  ├── SafeRoutingService     │     │  └── LLMResponseCache       │
│  ├── OSMContributor         │     │                              │
│  ├── ReportClassifier       │     │ 13+ Agent Tools:            │
│  ├── LocalEmergencyCatalog  │     │  ├── SosTool                │
│  └── AlertService           │     │  ├── EmergencyTool          │
│                              │     │  ├── ChallanTool           │
│ Internal Middleware:         │     │  ├── LegalSearchTool       │
│  ├── QueryProfilerMiddleware│     │  ├── FirstAidTool           │
│  ├── GeoJSONCompressMidwr   │     │  ├── WeatherTool            │
│  ├── CORSMiddleware          │     │  ├── OpenMeteoClient        │
│  ├── IdempotencyMiddleware   │     │  ├── RoadInfraTool          │
│  ├── APIVersioningMiddleware │     │  ├── RoadIssuesTool         │
│  ├── SecurityHeadersMidwr    │     │  ├── SubmitReportTool       │
│  ├── RequestIDMiddleware     │     │  ├── GeocodingClient        │
│  ├── PrometheusMetricsMidwr │     │  ├── DrugInfoTool           │
│  ├── CSRFMiddleware          │     │  └── What3WordsTool         │
│  └── TenantIsolationMidwr   │     │                              │
│                              │     │ 11+ LLM Providers:          │
│ Dependencies:               │     │  ├── GroqProvider           │
│  └─ AlertService (shared)   │     │  ├── CerebrasProvider       │
│                              │     │  ├── GeminiProvider        │
│                              │     │  ├── GitHubModelsProvider  │
│                              │     │  ├── NvidiaNimProvider     │
│                              │     │  ├── OpenRouterProvider    │
│                              │     │  ├── MistralProvider       │
│                              │     │  ├── TogetherProvider      │
│                              │     │  ├── SarvamProvider (30B)  │
│                              │     │  ├── Sarvam105BProvider    │
│                              │     │  └── TemplateProvider      │
│                              │     │                              │
│                              │     │ Dependencies:               │
│                              │     │  └─ Backend (:8000)         │
│                              │     │     └─ SOS, Challan, etc.   │
│                              │     │  └─ AlertService (shared)   │
└─────────────────────────────┘     └─────────────────────────────┘
```

---

## 2. External API Dependencies

| API | Domain | Service | Auth Method | Free Tier Limit | Risk |
|-----|--------|---------|-------------|-----------------|------|
| **Overpass** | `overpass-api.de` | Backend+Chatbot | None | 10K queries/day | LOW |
| **Photon** | `photon.komoot.io` | Backend | None | Unlimited | LOW |
| **Nominatim** | `nominatim.openstreetmap.org` | Backend+Chatbot | User-Agent | 1 req/s | LOW |
| **OpenRouteService** | `api.openrouteservice.org` | Backend | API Key | 2K req/day | MED |
| **OSRM** | `router.project-osrm.org` | Backend | None | Unlimited, slow | LOW |
| **Healthsites.io** | `healthsites.io` | Backend | API Token | 1K/day | MED |
| **Open-Meteo** | `api.open-meteo.com` | Chatbot | None | Unlimited | LOW |
| **OpenWeather** | `api.openweathermap.org` | Chatbot | API Key | 60/min, 1M/mo | LOW |
| **What3Words** | `api.what3words.com` | Chatbot | API Key | 50K/mo | MED |
| **Open FDA** | `api.fda.gov` | Chatbot | None | Unlimited | LOW |
| **OpenCage** | `api.opencagedata.com` | Chatbot | API Key | 2.5K/day | MED |
| **BigDataCloud** | `api.bigdatacloud.net` | Frontend | None | 10K/mo | MED |
| **Supabase** | `*.supabase.co` | Backend | Service Role | 500MB, 50K MAU | MED |
| **Upstash Redis** | `*.upstash.io` | Backend+Chatbot | Password | 10K cmd/day, 256MB | HIGH |
| **Google Maps** | `maps.googleapis.com` | Frontend | API Key | $200/mo credit | MED |
| **MapTiler** | `api.maptiler.com` | Frontend | API Key | 100K views/mo | LOW |
| **OpenFreeMap** | `openfreemap.org` | Frontend | None | Unlimited | LOW |
| **Groq** | `api.groq.com` | Chatbot | API Key | 30 RPM, 14K RPD | MED |
| **Cerebras** | `api.cerebras.ai` | Chatbot | API Key | 10 RPM | MED |
| **Gemini** | `generativelanguage.googleapis.com` | Chatbot | API Key | 15 RPM, 1M token/day | MED |
| **GitHub Models** | `models.inference.ai.azure.com` | Chatbot | Token | Variable | MED |
| **NVIDIA NIM** | `integrate.api.nvidia.com` | Chatbot | API Key | 1K req/day | MED |
| **OpenRouter** | `openrouter.ai` | Chatbot | API Key | Variable | MED |
| **Mistral** | `api.mistral.ai` | Chatbot | API Key | 500 RPM | LOW |
| **Together** | `api.together.xyz` | Chatbot | API Key | Variable | MED |
| **Sarvam AI** | `api.sarvam.ai` | Chatbot | API Key | ₹2.50/1M tokens | LOW |
| **HuggingFace** | `api-inference.huggingface.co` | Chatbot | HF Token | 30K tokens/mo (free) | MED |
| **PostHog** | `app.posthog.com` | Frontend | API Key | 1M events/mo | LOW |
| **Sentry** | `o*.ingest.sentry.io` | Both | DSN | 5K errors/mo | LOW |

---

## 3. Database Dependencies

```
PostgreSQL 16 + PostGIS 3.4 (Supabase)
├── emergency_services (50K+ facilities)
│   └── GIST index on location (POINT)
├── road_issues
│   ├── GIST index on location (POINT)
│   ├── B-tree on (status, issue_type)
│   └── Composite GIST (location, status)
├── road_infrastructure
│   └── GIST index on geometry (LINESTRING)
├── sos_incidents
│   └── UUID PK (gen_random_uuid)
├── user_profiles
│   └── JSONB field for emergency_contacts
├── live_tracking (4hr TTL)
├── traffic_violations (6 seeded types)
└── state_fine_overrides (all 28+ states)

Redis 7 (Upstash)
├── DB 0: Backend cache + rate limiting + idempotency
├── DB 1: Chatbot session memory + LLM response cache
└── Pub/Sub: WebSocket tracking multi-instance broadcast

ChromaDB (File-based)
├── Collection: safevixai_rag
├── Embedding: LocalHashEmbeddingFunction (384-dim)
└── Data: Legal, medical, accidents, roads, emergency docs

IndexedDB (Browser)
├── safevix-offline-db (version 2)
│   ├── sos-queue (pending SOS triggers)
│   └── road-report-queue (pending road reports)
├── svai-storage (Zustand persist)
│   └── userProfile, prefs, map settings
└── Cache storage (Service Worker)
    └── safevixai-v3 cache
```

---

## 4. Python Package Dependencies

### Backend (22 packages in requirements-render.txt)
```
fastapi>=0.115.0          → Web framework
uvicorn[standard]         → ASGI server
sqlalchemy[asyncio]>=2.0  → ORM
asyncpg                   → PostgreSQL async driver
alembic                   → Migrations
geoalchemy2               → PostGIS ORM
pydantic>=2.0             → Validation
pydantic-settings         → Config management
httpx                     → HTTP client
redis[hiredis]            → Cache
slowapi                   → Rate limiting
sentry-sdk                → Error tracking
pyjwt                     → JWT
python-multipart          → Upload parsing
prometheus-client         → Metrics
opentelemetry-api         → Tracing
opentelemetry-sdk         → Tracing SDK
opentelemetry-instrumentation-fastapi → Auto-instrumentation
Pillow                    → Image processing
aiofiles                  → Async file I/O
```

### Chatbot Service (25 packages in requirements-render.txt)
```
fastapi>=0.115.0          → Web framework
uvicorn[standard]         → ASGI server
pydantic>=2.0             → Validation
httpx                     → HTTP client
redis[hiredis]            → Cache + session
slowapi                   → Rate limiting
sentry-sdk                → Error tracking
chromadb>=1.5.0           → Vector store
sentence-transformers     → Embeddings (lazy load)
groq                      → Groq LLM client
google-generativeai       → Gemini client
openai                    → OpenAI-compatible providers
mistralai                 → Mistral client
pypdf                     → PDF reading
pdfplumber                → PDF parsing
Pillow                    → Image processing
```

### Shared (alert_service.py - project root)
```
smtplib (stdlib)          → Email alerts via Gmail SMTP
```

---

## 5. npm Package Dependencies

### Frontend (Key packages from package.json)
```json
{
  "next": "^15.5.18",
  "react": "^19.1.0",
  "react-dom": "^19.1.0",
  "maplibre-gl": "^5.22.0",
  "zustand": "4.5.4",
  "axios": "^1.16.0",
  "gsap": "^3.15.0",
  "@gsap/react": "^2.1.2",
  "@duckdb/duckdb-wasm": "1.29.0",
  "@mlc-ai/web-llm": "0.2.73",
  "@huggingface/transformers": "^4.0.1",
  "@supabase/supabase-js": "^2.105.3",
  "lucide-react": "0.427.0",
  "tailwindcss": "3.4.10",
  "posthog-js": "^1.370.0",
  "swr": "^2.4.1",
  "sonner": "^2.0.7",
  "cmdk": "^1.1.1",
  "idb": "8.0.0",
  "@turf/turf": "6.5.0",
  "geokdbush": "1.1.0",
  "hnswlib-wasm": "0.8.2",
  "qrcode.react": "^4.2.0",
  "react-speech-recognition": "3.10.0",
  "@tanstack/react-virtual": "^3.13.24",
  "class-variance-authority": "^0.7.1",
  "tw-animate-css": "^1.4.0"
}
```

---

## 6. Infrastructure Dependencies

```
Docker Desktop
├── postgis/postgis:16-3.4 → Postgres data volume
├── redis:7-alpine         → Redis data volume
├── Backend Docker image   → pip install requirements-render.txt
├── Chatbot Docker image   → pip install requirements-render.txt (no torch)
└── Frontend Docker image  → npm ci, next build (standalone)

GitHub Actions
├── ubuntu-latest runner
├── Service containers: postgis/postgis:16-3.4, redis:7-alpine
└── Caching: pip cache, npm cache

Vercel
├── Serverless functions (Node 20)
├── Edge network (global CDN)
└── Automatic HTTPS + preview deployments

Render
├── Web services (2 × free tier)
├── Health check endpoints
└── Deploy hooks

Supabase
├── PostgreSQL 16 + PostGIS
├── Storage (road-photos bucket)
└── Auth (JWT validation)

Upstash
├── Redis 7 (serverless)
└── TLS encryption
```
