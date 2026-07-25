# System Design

> Version 1.0.0 | Last updated: 2026-07-25

## Architecture Overview

SafeVixAI is a 3-service monorepo delivering real-time emergency response, AI-powered traffic legal assistance, and road infrastructure reporting.

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15 + React 19)              │
│                    Port 3000 — PWA, MapLibre GL, WebLLM          │
│                    Zustand state, Tailwind CSS 3, DuckDB-Wasm     │
└──────────┬──────────────────────────┬──────────────────────────┬──┘
           │ REST/WS (JWT Bearer)     │ REST (JWT Bearer)        │
           │ WebSocket /tracking      │ SSE /chat/stream         │
┌──────────▼──────────┐  ┌───────────▼──────────────────────┐
│  Backend (FastAPI)  │  │  Chatbot Service (FastAPI)       │
│  Port 8000          │  │  Port 8010                       │
│                     │  │                                  │
│  PostgreSQL +       │  │  ChromaDB RAG Vectorstore        │
│    PostGIS 3.4      │◄─┤  10-Provider LLM Fallback Chain │
│  Redis 7 Cache      │  │  Redis Conversation Memory       │
│  DuckDB (Challans)  │  │  13 Agent Tools                  │
│  Overpass/Nominatim │  │  IndicSeamless Speech Service    │
│  WebSocket Server   │  │  Safety Checker + Governance     │
└──────────┬──────────┘  └──────────────────────────────────┘
           │
    ┌──────▼──────┐
    │  PostgreSQL  │
    │  + PostGIS   │
    └─────────────┘
```

## Data Flow

### User Request Flow (Emergency Locator)
```
User → Frontend PWA → /emergency → GET /api/v1/emergency/nearby?lat=&lon=
  → Backend: check Redis cache → if miss: PostGIS ST_DWithin query
  → PostGIS: radius expansion (500m → 50km), GiST index scan
  → Backend: cache result in Redis (3600s TTL)
  → Response: JSON with services, distances, phone numbers
```

### User Request Flow (Chatbot)
```
User → Frontend → /assistant → POST /api/v1/chat/ (or /chat/stream SSE)
  → Backend proxy → Chatbot Service
  → SafetyChecker.evaluate() — 12-pattern prompt injection guard
  → IntentDetector.detect() — 9 intent classes (<1ms)
  → ContextAssembler.assemble() — invoke tools + ChromaDB RAG search
  → ProviderRouter.generate() — 10-provider fallback chain
  → ConversationMemoryStore.append() — Redis (24h TTL)
  → Response: answer, intent, sources, model_used, latency_ms
```

### SOS Flow
```
User → Frontend → Hold-to-activate (2s) → POST /api/v1/emergency/sos
  → Geolocation capture (GPS/cell tower)
  → If offline: enqueue in IndexedDB (offline-sos-queue.ts)
  → Backend: create sos_incident record (PostGIS point)
  → WhatsApp/SMS share via generateSosWhatsAppLink
  → WebSocket tracking session created
  → Family members connect via ws://host/tracking/{group_id}
```

## Component Interactions

| Interaction | Protocol | Auth | Notes |
|-------------|----------|------|-------|
| Frontend ↔ Backend | REST (axios) | JWT Bearer | All data API calls |
| Frontend ↔ Backend | WebSocket | JWT (handshake) | Live tracking |
| Frontend ↔ Chatbot | REST/SSE | JWT Bearer | Chat messages |
| Backend ↔ Chatbot | REST (httpx) | Internal API Key | Chat proxy |
| Backend ↔ PostgreSQL | asyncpg | Password | Connection pool |
| Backend ↔ Redis | redis-py (hiredis) | Password | Cache + locks |
| Chatbot ↔ LLM APIs | HTTP | API Keys | 10 providers |
| Backend ↔ Overpass | HTTP (httpx) | None | OpenStreetMap data |
| Backend ↔ Nominatim | HTTP (httpx) | User-Agent | Geocoding |

## Service Boundaries

| Service | Owns | Does Not Own |
|---------|------|-------------|
| Frontend | UI rendering, offline AI, PWA caching, client state (Zustand + IndexedDB) | Business logic, data persistence, LLM calls |
| Backend | REST API, geospatial queries, challan calc, auth, file uploads, WebSocket tracking, caching, MCP server | UI rendering, heavy ML, real-time LLM inference |
| Chatbot | LLM provider routing, RAG, intent detection, tool execution, speech translation, conversation memory | User management, persistent storage, geospatial processing |

## Caching Strategy

### Redis Cache Layers
- **Query Cache**: Emergency results, geocoding, routes — 3600-86400s TTL
- **Session Cache**: Chat conversations — 86400s TTL
- **Rate Limiting**: Sliding window counters — TTL varies
- **Distributed Locks**: Redlock pattern — 5-30s TTL
- **JWKS Cache**: Public keys — 3600s TTL with stampede protection

### Stampede Protection
`get_json_with_stampede_protection()`:
1. Check cache — return if hit
2. Acquire mutex (SET NX EX 5s)
3. If locked: wait 50ms, retry cache (stale-while-revalidate)
4. If stale served: background refresh
5. Recalculate, store, release mutex

## Resilience Patterns

| Pattern | Implementation | Coverage |
|---------|---------------|----------|
| Circuit Breaker | 3-failure threshold, 30s half-open | All 8 external APIs |
| LLM Fallback Chain | 10 providers, sequential fallback | Chat completions |
| Cache Stampede Protection | SET NX EX + stale-while-revalidate | All cache keys |
| Distributed Locking | Redlock (Redis) + in-memory fallback | Critical POST endpoints |
| Idempotency Keys | SHA-256 hash + distributed lock | POST/PUT endpoints |
| Connection Pooling | asyncpg pool, httpx connection pools | DB + external APIs |
| Graceful Degradation | Redis fallback to in-memory | Chat, cache, rate limiting |
| Offline Queue | IndexedDB queue + flush on online | SOS, road reports |

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
