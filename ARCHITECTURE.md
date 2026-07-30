# SafeVixAI — Architecture

> **Last Updated:** 2026-07-29

SafeVixAI is a full-stack, AI-powered road safety PWA for the IIT Madras Road Safety Hackathon 2026.
Solves 3 problem statements: Emergency Locator, AI Chatbot (traffic law + first aid), Challan Calculator, and Road Reporter.
Total infra cost: ₹0. All free/open-source.

## System Architecture

```mermaid
flowchart LR
    subgraph Frontend["Frontend — Next.js 15 PWA :3000"]
        F1[Next.js App Router<br/>28 Routes]
        F2[MapLibre GL JS<br/>Maps & Heatmaps]
        F3[Zustand Store<br/>6 Slices]
        F4[Service Worker<br/>Offline Cache]
        F5[WebLLM / DuckDB-Wasm<br/>Offline AI & SQL]
    end

    subgraph Backend["Backend — FastAPI :8000"]
        B1[API Gateway<br/>25 Route Modules]
        B2[PostgreSQL + PostGIS<br/>Spatial Queries]
        B3[Redis Cache<br/>Stampede Protection]
        B4[DuckDB Engine<br/>Challan Calculation]
        B5[WebSocket Server<br/>Live Tracking]
        B6[Circuit Breaker<br/>8 External Services]
    end

    subgraph Chatbot["Chatbot Service — FastAPI :8010"]
        C1[Chat Engine<br/>Agentic RAG]
        C2[9+1 LLM Providers<br/>Auto-Fallback Chain]
        C3[ChromaDB Vectorstore<br/>Law & First-Aid RAG]
        C4[13 Agent Tools<br/>SOS, Challan, Weather...]
        C5[Conversation Memory<br/>Redis 24h TTL]
    end

    subgraph CI["CI/CD — GitHub Actions"]
        CI1[backend.yml<br/>pytest --cov=100%]
        CI2[chatbot.yml<br/>pytest --cov=97%]
        CI3[frontend.yml<br/>jest + tsc --noEmit]
        CI4[e2e.yml<br/>Playwright Full Stack]
        CI5[migration-safety.yml<br/>Alembic Upgrade/Downgrade]
        CI6[codeql.yml<br/>CodeQL Advanced]
        CI7[lighthouse.yml<br/>LHCI Audit]
        CI8[security.yml<br/>Gitleaks + Scorecard]
    end

    subgraph Infra["Infrastructure"]
        I1[Supabase<br/>PostgreSQL 16]
        I2[Upstash<br/>Serverless Redis]
        I3[Docker Compose<br/>5 Services]
    end

    F1 -- REST / WebSocket --> Backend
    F1 -- REST --> Chatbot
    B2 <--> B3
    B5 <--> F1
    B6 --> C2
    Chatbot --> B2
    Chatbot --> B3

    Backend --> I1
    Backend --> I2
    Chatbot --> I2

    F1 --> CI3
    Backend --> CI1
    Chatbot --> CI2
```

## Service Responsibilities

| Service | Language | Port | Key Dependencies |
|---------|----------|------|------------------|
| **Frontend** | TypeScript / Next.js 15 | 3000 | MapLibre GL, Zustand, Tailwind CSS |
| **Backend** | Python / FastAPI | 8000 | SQLAlchemy, GeoAlchemy2, Redis, DuckDB |
| **Chatbot** | Python / FastAPI | 8010 | ChromaDB, httpx, 9 LLM SDKs |

## Quick Summary

SafeVixAI is a 3-service monorepo:

```
SafeVixAI/
├── frontend/         Next.js 15 + React 19 PWA (Port 3000)
├── backend/          FastAPI + PostgreSQL/PostGIS + Redis (Port 8000)
└── chatbot_service/  FastAPI + ChromaDB + 10-provider LLM fallback (Port 8010)
```

Key architecture decisions are documented in [docs/adr/](docs/adr/).

For deployment architecture, see [docs/Deployment.md](docs/Deployment.md).

## Related

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Full architecture documentation
- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) — Detailed system design and component specs
- [OBSERVABILITY.md](OBSERVABILITY.md) — Logging, metrics, traces, alerting
- [MONITORING.md](MONITORING.md) — Metrics dashboards and uptime monitoring
