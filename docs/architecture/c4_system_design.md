# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

# SafeVixAI System Design

## Overview

SafeVixAI is a full-stack, AI-powered road safety platform architected as three independent services communicating over REST/WebSocket. The system serves as an emergency locator, AI legal assistant, challan calculator, and road reporter for Indian roads.

## Architecture Diagrams

### C4 Context Diagram

```
                     ┌────────────────────────────────────────┐
                     │         [User/Driver]                  │
                     │  (Web browser / Mobile PWA)            │
                     └──────────────┬─────────────────────────┘
                                    │ HTTPS
                                    ▼
                     ┌────────────────────────────────────────┐
                     │     SafeVixAI PWA (Next.js 15)         │
                     │  Port 3000                             │
                     │  MapLibre GL, Zustand, DuckDB-Wasm     │
                     └──────────────┬─────────────────────────┘
                                    │ REST/WS (JWT Bearer)
                    ┌───────────────┴────────────────┐
                    ▼                                 ▼
     ┌───────────────────────────┐    ┌───────────────────────────┐
     │  Backend API (FastAPI)    │    │  Chatbot Service (FastAPI)│
     │  Port 8000                │    │  Port 8010                │
     │  PostgreSQL + PostGIS     │◄───┤  9 LLM Providers          │
     │  Redis Cache + Queue      │    │  ChromaDB RAG             │
     │  WebSocket /tracking      │    │  Speech Translation       │
     │  DuckDB (offline challan) │    │  Conversation Memory      │
     └───────────────────────────┘    └───────────────────────────┘
```

### Container Diagram

| Container | Technology | Port | Purpose |
|-----------|-----------|------|---------|
| Frontend | Next.js 15, React 19, TypeScript, MapLibre GL | 3000 | PWA road safety UI |
| Backend | FastAPI, SQLAlchemy async, GeoAlchemy2 | 8000 | REST API + WebSocket tracking |
| Chatbot | FastAPI, LangGraph, ChromaDB | 8010 | Agentic RAG chatbot |
| Database | PostgreSQL 16 + PostGIS | 5432 | Geospatial data persistence |
| Cache/Queue | Redis 7 | 6379 | Session cache, pub/sub, task queue |

### Deployment Topology

```
Frontend (Vercel Edge Network)
  → Backend (Render Web Service, auto-scaled)
    → PostgreSQL (Supabase with PostGIS 16)
    → Redis (Upstash Serverless)
  → Chatbot (Render Web Service, auto-scaled)
    → ChromaDB (local file persistence, committed to git)
    → 9 LLM Provider APIs (Groq, Gemini, Cerebras, GitHub, etc.)
```

## Data Flow: SOS Alerting

```
User holds SOS button (2s hold detection via requestAnimationFrame)
  → navigator.geolocation → {lat, lon}
  → POST /api/v1/emergency/sos
  → Backend: create SOS event record in DB
  → Backend: create tracking session with unique session_id
  → WebSocket broadcast: family tracking updates
  → SMS/WhatsApp: notify emergency contacts (if configured)
  → Frontend: redirect to tracking URL with live map
```

## Data Flow: Chat Query

```
User message
  → SafetyChecker.evaluate() — block harmful queries
  → IntentDetector.detect() — classify into 9 intents
  → ContextAssembler.assemble() — call relevant tools + retrieve RAG
  → ProviderRouter.generate() — LLM call with fallback chain
  → ConversationMemoryStore.append() — Redis persistence
```

## Data Flow: Update Management

```
Startup:
  → UpdateScheduler starts in lifespan
  → Periodic (24h): check GitHub releases
  → If update available: sync to DB
  → Release channels: stable, beta, nightly, prerelease

User visits app:
  → UpdateBanner detects pending update
  → "Update Now" → download (SSE progress) → verify checksum
  → Verify GPG signature → install → restart
  → Offline: bundle queued in IndexedDB via Service Worker
```

## Component Architecture: Backend

```
api/v1/ (25+ route modules)
  ├── emergency.py       — SOS, nearby hospitals/police/fire
  ├── challan.py         — Fine calculation
  ├── roadwatch.py       — Road issue reporting
  ├── updates.py         — Update management (14 endpoints)
  ├── admin.py           — Cache purge, metrics
  ├── probes.py          — Kubernetes /readyz, /livez, /startupz
  └── ...

services/ (16 modules)
  ├── emergency_locator.py     — Spatial queries for nearby services
  ├── challan_service.py       — Violation calculation engine
  ├── roadwatch_service.py     — Photo verification, EXIF stripping
  ├── update_service.py        — Release management, verification
  ├── update_scheduler.py      — Periodic update checks
  └── ...

core/
  ├── security.py        — JWT validation, RBAC
  ├── database.py        — SQLAlchemy async engine
  ├── redis_client.py    — Cache with stampede protection
  ├── cqrs.py            — Command/Query bus
  └── ...
```

## Component Architecture: Chatbot

```
agent/
  ├── graph.py               — ChatEngine (LangGraph-based)
  ├── intent_detector.py     — 9 intent classification
  ├── safety_checker.py      — Prompt injection defense
  ├── context_assembler.py   — Tool orchestration
  └── ...

providers/ (9 providers + routing)
  ├── groq_provider.py, gemini_provider.py, ...
  ├── provider_registry.py   — API key → provider mapping
  ├── router.py              — Fallback chain + auto-routing
  └── ...

tools/ (13 tools)
  ├── sos_tool.py, challan_tool.py, legal_search_tool.py, ...
  └── ...

rag/
  ├── vectorstore.py    — ChromaDB wrapper
  ├── retriever.py      — Semantic search with reranking
  └── ...
```

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Map library | MapLibre GL | Free, open-source; no API costs unlike Google Maps |
| State management | Zustand | 90% less boilerplate than Redux; sufficient for PWA scale |
| Offline AI | WebLLM Phi-3 | 2.2GB model, runs entirely in-browser via WebGPU |
| Embedding model | LocalHashEmbeddingFunction | Zero ML dependencies, hash-based 384-dim vectors |
| Challan engine | DuckDB (server) + DuckDB-Wasm (client) | Deterministic SQL; LLMs hallucinate fine amounts |
| Authentication | JWT + Supabase Auth | Stateless, standard, generous free tier |
| API style | FastAPI with Pydantic v2 | Auto-generated OpenAPI docs, validation, serialization |
| Containerization | Docker Compose | 5 services; single command for full stack |

## Scaling Characteristics

- **Backend**: Horizontal scaling via stateless FastAPI workers + PostgreSQL connection pooling (asyncpg)
- **Database**: PostGIS GiST indexes on spatial columns for <50ms radius queries
- **Cache**: Redis with stampede protection (SET NX EX + stale-while-revalidate) for popular endpoints
- **Chatbot**: Provider fallback chain (9 providers) ensures 99.9%+ uptime; each failure cascades to next
- **Frontend**: CDN-cached static assets; PWA service worker for offline capability; all API calls through SWR with deduplication
- **Files**: Static uploads served directly by FastAPI (no object storage dependency)

## Security Architecture

- JWT authentication with RS256 signature validation
- CSP headers with strict policy (no inline scripts except trusted)
- Host header validation and CORS origin checking
- Rate limiting via slowapi (token bucket algorithm)
- Idempotency keys for POST/PUT endpoints
- Request correlation IDs through the entire request lifecycle
- CSRF token validation for state-changing operations
