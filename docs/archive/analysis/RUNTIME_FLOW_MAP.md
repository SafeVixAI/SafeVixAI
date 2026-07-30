# SafeVixAI — Runtime Flow Map

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

> Generated: 2026-05-22 | Tracing all critical execution paths

---

## 1. Application Startup Sequence

### Backend (`backend/main.py create_app()`)

```
1. Load Settings (pydantic-settings from .env)
2. Configure Logging (JSON in prod, text in dev)
3. Init Sentry SDK (error tracking, 0.1 sample rate)
4. Enter Lifespan Context
   ├── create_cache(redis_url) → CacheHelper (dual Redis+mem)
   ├── JWKSManager(jwks_url) → start background rotation loop
   ├── OverpassService(settings) → Overpass API client
   ├── GeocodingService(settings, cache) → Photon + Nominatim
   ├── AuthorityRouter(settings, overpass, cache)
   ├── EmergencyLocatorService(settings, cache, overpass)
   ├── RoutingService(settings, cache) → ORS + OSRM
   ├── ChallanService(settings) → fine calculation engine
   ├── LLMService(settings) → chatbot proxy
   └── RoadWatchService(settings, cache, geocoding, authority)
5. Attach all services to app.state.*
6. Mount middleware stack (8 layers)
7. Mount API routers (13 modules)
8. Register exception handlers
9. Start serving
```

### Chatbot Service (`chatbot_service/main.py create_app()`)

```
1. Load Settings (dataclass from os.getenv)
2. Configure Logging
3. Init Sentry (optional, try/except)
4. Enter Lifespan Context
   ├── BackendToolClient(settings) → httpx client for backend
   ├── ConversationMemoryStore(redis_url, session_ttl)
   ├── LocalVectorStore(chroma_persist_dir, rag_data_dir)
   ├── Retriever(vectorstore, top_k=5, min_score=0.28)
   ├── WeatherTool(settings) → Open-Meteo + OWM
   ├── IndicSeamlessService(settings) → speech model (preload)
   ├── What3WordsTool(api_key)
   ├── GeocodingClient(opencage_key)
   ├── DrugInfoTool()
   ├── SubmitReportTool(backend_base_url)
   ├── ContextAssembler(retriever, sos_tool, challan_tool, ...)
   ├── LLMResponseCache(redis_url)
   └── ChatEngine(memory, vectorstore, intent_detector, ...)
5. Mount middleware (security headers, request-id, CORS)
6. Mount routers (chat, admin, speech)
7. Serve on port 8010
```

### Frontend (`next start`)

```
1. Static generation + server-side rendering
2. Client hydration → RootLayout
   ├── SentryInit → initialize error tracking
   ├── AnalyticsProvider → PostHog init
   ├── ThemeProvider → load theme from localStorage
   ├── GSAPProvider → register plugins, set defaults
   ├── ConnectivityProvider → online/offline listener
   └── EnterpriseClientAppHooks
       ├── Subscribe to Supabase auth state
       ├── Start crash detection (if enabled)
       ├── Register offline sync listeners
       └── Hydrate initial data
```

---

## 2. Request Lifecycle (Backend)

```
HTTP Request
  │
  ├── CORSMiddleware (origin check, headers)
  ├── QueryProfilerMiddleware (response time tracking)
  ├── GeoJSONCompressionMiddleware (gzip for GeoJSON)
  ├── IdempotencyMiddleware (check idempotency key)
  ├── APIVersioningMiddleware (version headers)
  ├── SecurityHeadersMiddleware (HSTS, CSP, etc.)
  ├── RequestIDMiddleware (X-Request-ID correlation)
  ├── PrometheusMetricsMiddleware (request counting)
  ├── CSRFMiddleware (double-submit cookie check)
  ├── TenantIsolationMiddleware (org_id extraction)
  │
  ├── Route Handler (FastAPI endpoint)
  │   ├── Rate Limiter check (slowapi)
  │   ├── Auth check (get_current_user / get_current_user_optional)
  │   ├── Input Validation (Pydantic)
  │   ├── Service call (via app.state.*)
  │   ├── Response normalization
  │   └── Response
  │
  └── Exception Handler (if uncaught)
      ├── Sanitize error (redact SQL keywords)
      ├── Alert service (email notification)
      └── Return 500 JSON
```

---

## 3. Chatbot Execution Graph

```
chat(payload)
  │
  │ 1. Append user message to memory store
  │ 2. Get history (last 12 messages)
  │
  ├── SafetyChecker.evaluate(message)
  │   ├── Unicode normalization (NFKC, strip zero-width)
  │   ├── Dual-path evaluation (l33t AND non-l33t)
  │   ├── 24 jailbreak patterns check
  │   ├── 24 harm/evasion/violence patterns check
  │   ├── Space-inserted obfuscation check
  │   └── [BLOCKED] → return blocked response
  │
  │ 3. ConversationSummarizer.summarize(history)
  │
  ├── IntentDetector.detect(message)
  │   ├── 9 intent classes (keyword/regex-based)
  │   └── initial_intent
  │
  ├── IntentDetector.refine_intent(initial_intent, history)
  │   ├── If not 'general' → return unchanged
  │   ├── If follow-up indicator → inherit from history
  │   └── refined_intent
  │
  ├── ContextAssembler.assemble(session_id, message, intent, ...)
  │   ├── emergency → SosTool + Weather (parallel)
  │   ├── first_aid → FirstAidTool + DrugInfoTool (serial)
  │   ├── challan → ChallanTool + LegalSearchTool
  │   ├── legal → LegalSearchTool
  │   ├── road_issue → RoadInfra + RoadIssues + SubmitReport
  │   ├── road_weather → WeatherTool
  │   ├── safe_route → SafeRoute + RoadIssues + Weather (parallel)
  │   ├── road_infrastructure → RoadInfrastructureTool
  │   └── general → no tools
  │   └── ConversationContext(intent, tools, retrieved, history, ...)
  │
  ├── ProviderRouter.generate(request)
  │   ├── Check LLM response cache → return if hit
  │   ├── Language detection (Unicode script ranges)
  │   ├── Provider selection:
  │   │   ├── Indian language → Sarvam-30B
  │   │   ├── Indian + high-stakes → Sarvam-105B
  │   │   └── English → default (Groq)
  │   ├── Circuit breaker check (skip if unavailable)
  │   ├── asyncio.wait_for(provider.generate(), timeout=20s)
  │   ├── Confidence scoring (0.0 - 1.0)
  │   ├── [Low confidence < 0.3] → trigger fallback chain
  │   ├── [Success] → cache response, return
  │   └── [All fail] → alert_service, TemplateProvider
  │
  ├── AIGovernance.evaluate(response, context, tools, prompt)
  │   ├── Hallucination scoring (keyword overlap with RAG)
  │   ├── Factuality scoring (tool result alignment)
  │   ├── Citation extraction
  │   └── [Flagged] → prepend low confidence warning
  │
  │ 4. Deduplicate sources
  │ 5. Append assistant response to memory
  │ 6. Return ChatResponse(response, intent, sources, session_id)
```

---

## 4. SSE Streaming Flow

```
POST /api/v1/chat/stream
  │
  ├── Backend LLMService proxy
  │   └── POST chatbot_service /api/v1/chat/stream (with auth)
  │
  ├── Chatbot: ChatEngine.chat() → full LLM response
  │
  ├── Simulated streaming (word-split complete response):
  │   ├── html.escape(response)
  │   ├── Split into words
  │   ├── For each word: {"type":"token","text":"word"}
  │   ├── Delay 12ms between words
  │   └── Final: {"type":"done","intent":"...","sources":[...]}
  │
  └── Backend proxies SSE to frontend
```

---

## 5. WebSocket Tracking Flow

```
Client → ws://host/api/v1/tracking/{group_id}?token=JWT
  │
  ├── Origin validation (CORS check)
  ├── Token validation (_decode_bearer_token)
  ├── Connect to group
  │   ├── Register in active_connections[group_id]
  │   └── Start Redis PubSub listener (if first member)
  │
  ├── Message Loop:
  │   ├── Receive: {"lat": 13.08, "lon": 80.27}
  │   ├── Validate: lat [-90,90], lon [-180,180]
  │   ├── Validate: message size <= 4096 bytes
  │   └── Broadcast:
  │       ├── Redis PubSub: channel "tracking:{group_id}"
  │       └── Local: _local_broadcast() to all group members
  │
  └── Disconnect
      ├── Unregister from group
      └── Stop PubSub listener (if last member)
```

---

## 6. Emergency Locator Execution

```
GET /api/v1/emergency/nearby?lat=13.08&lon=80.27&categories=hospital,police&radius=5000
  │
  ├── Cache check: emergency:nearby:13.08:80.27:...
  │   └── [HIT] → return cached EmergencyResponse
  │
  ├── Radius stepping: [500, 1000, 5000, 10000, 25000, 50000]
  │
  ├── Tier 1: PostGIS query (for each radius step)
  │   └── ST_DWithin(location::geography, point::geography, radius)
  │   └── [Count >= 3] → stop expanding radius
  │
  ├── Tier 2: Local CSV catalog (Haversine)
  │   └── Dedup against Tier 1 results
  │   └── [Count >= 3] → stop
  │
  ├── Tier 3: Overpass API (with retry)
  │   └── 3 mirrors, exponential backoff
  │   └── Dedup against Tier 1+2 results
  │
  ├── Cache: set_json(cache_key, response, 3600s)
  │
  └── Return: {services[], count, radius_used, source}
```

---

## 7. Offline SOS Queue Sync

```
User triggers SOS while offline
  │
  ├── Capture: GPS, authToken, userId, bloodGroup, contacts
  ├── Store in IndexedDB (safevix-offline-db, sos-queue store)
  ├── Register Background Sync (sync sos-queue-flush)
  ├── Show "SOS queued - will send when online" toast
  │
  ┌── [Online event detected] ─────────────────────────┐
  │                                                     │
  ├── For each queued SOS (atomic per-item):            │
  │   ├── POST /api/v1/emergency/sos (with retry)       │
  │   ├── [Success] → Delete from IndexedDB             │
  │   ├── [Failed] → Log error, retry next interval     │
  │   └── Timeout: 8s per item                          │
  │                                                     │
  └── Show "SOS sent successfully" notification         │
```

---

## 8. Crash Detection Flow

```
DeviceMotionEvent.accelerationIncludingGravity
  │
  ├── [crashDetectionEnabled = false] → ignore
  │
  ├── [G-force >= 15G threshold] → crash detected
  │   ├── Debounce check (60s since last crash)
  │   └── Debounce [OK] →
  │       ├── Store G-force, timestamp
  │       ├── Set severity (based on G-force)
  │       ├── Show CrashCountdown overlay (z-index 9999)
  │       │   ├── 20-second countdown
  │       │   ├── GSAP anim: progress ring depletes
  │       │   ├── Haptic + sound per tick
  │       │   └── Color shifts: white → red at 5s
  │       │
  │       ├── [User cancels → "I AM SAFE"]
  │       │   └── Hide overlay, log cancellation
  │       │
  │       └── [Countdown reaches 0]
  │           ├── Haptic SOS pattern (.sos())
  │           ├── Sound 880Hz tone
  │           ├── [Online] triggerSos() → backend POST
  │           ├── [Offline] enqueueSOS() → IndexedDB
  │           ├── Start family tracking (beginLocationBroadcast)
  │           └── Haptic + toast confirmation
```

---

## 9. Error Propagation Paths

```
LLM Provider Failure:
  ProviderRouter.generate()
    └── asyncio.wait_for(provider.generate(), timeout=20)
        └── [Timeout / HTTP Error / Rate Limit]
            ├── Circuit breaker opens (duration by error type)
            ├── Log + metrics (fallback_total)
            ├── Next provider in chain
            └── [All 9 fail]
                ├── alert_service.alert_all_providers_failed()
                └── TemplateProvider (always works)

Database Failure:
  EmergencyLocatorService._query_database()
    └── [SQLAlchemy error]
        ├── Log error
        ├── Jump to Tier 2 (CSV catalog)
        └── alert_service.alert_supabase_failed()

Overpass API Failure:
  OverpassService._execute_query()
    └── [Mirror 1 fails] → retry 3x, backoff
        └── [Mirror 2 fails] → retry 3x, backoff
            └── [Mirror 3 fails]
                ├── alert_service.alert_external_api_failed()
                └── Return empty results

Geocoding Failure:
  GeocodingService.reverse()
    └── [Photon fails] → log
        └── [Nominatim fails] → log
            ├── alert_service.alert_external_api_failed()
            └── Return None (no address)

Redis Failure:
  CacheHelper.set_json() / get_json()
    └── [Redis error] → set _redis_healthy = False
        └── In-memory dict fallback
```

---

## 10. Startup Timing (Cold Start)

```
Backend (Docker, Render):
  ├── Package install: ~10s (requirements-render.txt is lightweight)
  ├── App start: ~2s
  ├── Service init: ~0.5s
  └── Total: ~12-15s

Chatbot (Docker, Render):
  ├── Package install: ~15s (no torch in requirements-render.txt)
  ├── App start: ~2s
  ├── ChromaDB load: ~3s
  ├── Speech model preload: ~5-30s (async, non-blocking)
  └── Total: ~20-50s

Frontend (Vercel):
  ├── Serverless function cold start: ~1s
  ├── Client hydration: ~2-5s (depends on device)
  └── Map tiles load: ~3-10s (network)
```
