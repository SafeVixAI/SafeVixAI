# System Design

> Version 1.0.0 | Last updated: 2026-07-29

## Architecture Overview

SafeVixAI is a 3-service monorepo delivering real-time emergency response, AI-powered traffic legal assistance, and road infrastructure reporting.

```mermaid
flowchart TD
    subgraph Client["Client Tier"]
        BROWSER[Next.js 15 PWA<br/>MapLibre GL, Zustand, Tailwind]
        SW[Service Worker<br/>Offline Cache, Background Sync]
        WASM[DuckDB-Wasm, WebLLM<br/>Offline Challan, Offline AI]
    end

    subgraph CDN["CDN / Edge"]
        VER[Vercel Edge<br/>Static Assets, ISR]
    end

    subgraph API["API Gateway Tier"]
        LG[Load Balancer]
        RT[Rate Limiter<br/>TokenBucket]
        AUTH[JWT Auth Middleware]
        CORS[CORS Middleware]
        IDEMP[Idempotency Middleware]
    end

    subgraph Services["Service Tier"]
        BE[FastAPI Backend :8000<br/>25 Route Modules]
        CB[FastAPI Chatbot :8010<br/>Agentic RAG]
    end

    subgraph Data["Data Tier"]
        PG[PostgreSQL 16 + PostGIS<br/>Persistent Storage]
        RD[Redis 7<br/>Cache + Session + Locks]
        DK[DuckDB<br/>Challan Analytics]
        CH[ChromaDB<br/>Vector Store RAG]
    end

    subgraph External["External Dependencies"]
        OSM[OpenStreetMap<br/>Overpass API, Nominatim]
        OWM[OpenWeather API]
        ORS[OpenRouteService]
        LLM[9+1 LLM Providers<br/>Groq, Gemini, Sarvam...]
        FDA[Open FDA Drug API]
    end

    BROWSER --> VER
    VER --> LG
    LG --> RT
    RT --> AUTH
    AUTH --> CORS
    CORS --> IDEMP
    IDEMP --> BE
    IDEMP --> CB

    BE --> PG
    BE --> RD
    BE --> DK
    CB --> CH
    CB --> RD

    BE --> OSM
    BE --> ORS
    CB --> OWM
    CB --> LLM
    CB --> FDA

    SW -.->|Offline| BROWSER
    WASM -.->|Client-side| BROWSER
```

## Data Flow

### Emergency Locator Flow

```mermaid
sequenceDiagram
    participant User as User
    participant Page as Emergency Page
    participant Store as Zustand Store
    participant API as Backend API
    participant DB as PostgreSQL
    participant Cache as Redis

    User->>Page: Open /emergency
    Page->>Page: Request geolocation
    Page-->>User: Allow GPS?

    User->>Page: Grant permission
    Page->>Store: setMapCenter(lat, lon)

    Page->>API: GET /api/v1/emergency/nearby?lat=X&lon=Y
    API->>Cache: Check cache (1h TTL)
    alt Cache Hit
        Cache-->>API: Cached result
    else Cache Miss
        API->>DB: ST_DWithin query with GiST index
        DB-->>API: Hospitals, Police, Fire sorted by distance
        API->>Cache: SETEX result (3600s)
    end
    API-->>Page: { status: "ok", data: [...] }

    Page->>Store: setNearbyServices(data)
    Page->>Page: Render markers on MapLibre
    Page-->>User: Interactive map + service cards
```

### Chatbot Flow

```
User to Frontend to /assistant to POST /api/v1/chat/ (or /chat/stream SSE)
  to Backend proxy to Chatbot Service
  to SafetyChecker.evaluate() - 12-pattern prompt injection guard
  to IntentDetector.detect() - 9 intent classes (<1ms)
  to ContextAssembler.assemble() - invoke tools + ChromaDB RAG search
  to ProviderRouter.generate() - 10-provider fallback chain
  to ConversationMemoryStore.append() - Redis (24h TTL)
  to Response: answer, intent, sources, model_used, latency_ms
```

### SOS Activation Flow

```mermaid
sequenceDiagram
    actor User as User
    participant SOS as SOS Button
    participant Store as Zustand Store
    participant API as Backend API
    participant WS as Tracking WebSocket
    participant Q as OfflineQueue
    participant DB as PostgreSQL

    User->>SOS: Hold button (2s)
    SOS->>SOS: RAF animation loop
    Note over SOS: performance.now + requestAnimationFrame
    SOS->>SOS: elapsed >= 2000ms
    SOS->>SOS: setActivated(true)

    alt Device Online
        SOS->>API: POST /api/v1/sos/trigger
        Note right of SOS: { lat, lon, blood_group, vehicle }
        API->>DB: INSERT sos_event
        API-->>SOS: { dispatch_id, tracking_url }
        SOS->>WS: CONNECT /api/v1/tracking/{group_id}
        WS-->>SOS: Location broadcast started
    else Device Offline
        SOS->>Q: enqueueSOS({ lat, lon, timestamp })
        Note right of Q: IndexedDB queue
        Q-->>SOS: SOS queued (will auto-sync)
        Note over Q: navigator.onLine listener to auto-flush
    end

    SOS-->>User: Dispatch Confirmed / Queued Offline
```

## Caching Strategy

```mermaid
flowchart TD
    subgraph Browser_Cache["Browser Cache"]
        BC1[Service Worker<br/>Stale-While-Revalidate]
        BC2[Next.js ISR<br/>Static Pages]
        BC3[IndexedDB<br/>Offline Data]
    end

    subgraph Redis_Cache["Redis Cache"]
        RC1[JWKS Keys<br/>TTL: 1h]
        RC2[Spatial Queries<br/>TTL: 1h]
        RC3[Token Buckets<br/>TTL: sliding window]
        RC4[Chat History<br/>TTL: 24h]
        RC5[Idempotency Keys<br/>TTL: 24h]
        RC6[Domain Events<br/>TTL: 7d]
    end

    subgraph Stampede["Stampede Protection"]
        SP1[Cache miss]
        SP2[Sets mutex key<br/>NX EX 5s]
        SP3[Recomputes data]
        SP4[Releases mutex]
        SP5[Stale-while-revalidate<br/>serves stale on mutex contention]
    end

    Browser_Cache -->|Miss| Redis_Cache
    Redis_Cache -->|Miss + Mutex| Stampede
```

### Redis Cache Layers
- **Query Cache**: Emergency results, geocoding, routes - 3600-86400s TTL
- **Session Cache**: Chat conversations - 86400s TTL
- **Rate Limiting**: Sliding window counters - TTL varies
- **Distributed Locks**: Redlock pattern - 5-30s TTL
- **JWKS Cache**: Public keys - 3600s TTL with stampede protection

### Stampede Protection
`get_json_with_stampede_protection()`:
1. Check cache - return if hit
2. Acquire mutex (SET NX EX 5s)
3. If locked: wait 50ms, retry cache (stale-while-revalidate)
4. If stale served: background refresh
5. Recalculate, store, release mutex

## Resilience Patterns

```mermaid
flowchart TD
    subgraph CircuitBreaker["Circuit Breaker"]
        CB1[Closed<br/>Normal Operation]
        CB2[Open<br/>Fail Fast<br/>30s timeout]
        CB3[Half-Open<br/>Probe Request]
        CB1 -->|5 failures| CB2
        CB2 -->|30s elapsed| CB3
        CB3 -->|Success| CB1
        CB3 -->|Failure| CB2
    end

    subgraph Retry["Retry with Backoff"]
        R1[Attempt 1<br/>0s delay]
        R2[Attempt 2<br/>1s delay]
        R3[Attempt 3<br/>2s delay]
        R4[Attempt 4<br/>4s delay]
        R5[Attempt 5<br/>8s delay to Fail]
        R1 -->|Error| R2
        R2 -->|Error| R3
        R3 -->|Error| R4
        R4 -->|Error| R5
    end

    subgraph Fallback["LLM Provider Fallback"]
        F1[Primary: Groq]
        F2[Cerebras]
        F3[Gemini]
        F4[... 9 providers]
        F5[Template<br/>Deterministic]
        F1 -->|Fail| F2
        F2 -->|Fail| F3
        F3 -->|Fail| F4
        F4 -->|Fail| F5
    end

    subgraph Alert["Alert System"]
        A1[Service Failure Detected]
        A2[Check Cooldown<br/>5 min window]
        A3[Send Email Alert<br/>3 Diagnostic Solutions]
        A1 --> A2
        A2 --> A3
    end
```

## Component Interactions

| Interaction | Protocol | Auth | Notes |
|-------------|----------|------|-------|
| Frontend to Backend | REST (axios) | JWT Bearer | All data API calls |
| Frontend to Backend | WebSocket | JWT (handshake) | Live tracking |
| Frontend to Chatbot | REST/SSE | JWT Bearer | Chat messages |
| Backend to Chatbot | REST (httpx) | Internal API Key | Chat proxy |
| Backend to PostgreSQL | asyncpg | Password | Connection pool |
| Backend to Redis | redis-py (hiredis) | Password | Cache + locks |
| Chatbot to LLM APIs | HTTP | API Keys | 10 providers |
| Backend to Overpass | HTTP (httpx) | None | OpenStreetMap data |
| Backend to Nominatim | HTTP (httpx) | User-Agent | Geocoding |

## Service Boundaries

| Service | Owns | Does Not Own |
|---------|------|-------------|
| Frontend | UI rendering, offline AI, PWA caching, client state (Zustand + IndexedDB) | Business logic, data persistence, LLM calls |
| Backend | REST API, geospatial queries, challan calc, auth, file uploads, WebSocket tracking, caching, MCP server | UI rendering, heavy ML, real-time LLM inference |
| Chatbot | LLM provider routing, RAG, intent detection, tool execution, speech translation, conversation memory | User management, persistent storage, geospatial processing |

## Security Architecture

- **Auth**: JWT (RS256 + HS256), JWKS rotation, guest UUID, internal API keys
- **Transport**: HTTPS/TLS, HSTS preload, CSP headers
- **API Security**: Rate limiting, CORS origin validation, host header validation, CSRF tokens
- **Data**: Blood group/contacts in IndexedDB only (never server), data retention scheduler
- **LLM**: Prompt injection guard, output validation, "Call 112" enforcement for injuries
- **Audit**: Request ID tracking, domain event bus, CSP violation collector

## Offline Architecture

| Component | Technology | Scope |
|-----------|-----------|-------|
| Service Worker | Cache-first for static assets, network-first for API | PWA caching |
| IndexedDB | User profile, offline SOS queue, road report queue | Privacy-critical data |
| WebLLM (Phi-3 Mini) | 2.2GB 4-bit quantized, on-demand download | Offline AI chat |
| DuckDB-Wasm | Client-side SQL for challan calculation | Offline challans |
| YOLOv8n (ONNX) | 15MB, browser-based pothole detection | Offline road reports |

## Monitoring Stack

| Component | Purpose | Configuration |
|-----------|---------|--------------|
| Prometheus | Metrics collection | /metrics endpoint, custom metrics |
| Grafana | Dashboard visualization | Provisioned dashboards in monitoring/ |
| Sentry | Error tracking | DSN config, 0.05 sample rate |
| Structured Logging | JSON NDJSON stdout | request_id, duration_ms, method, path |
| Health Check | Dependency status | GET /health, DB+Redis+Chatbot checks |
| Email Alerts | Critical failures | SMTP with 5-min cooldown |
