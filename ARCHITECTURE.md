# Architecture Overview

For the full architecture documentation, see [docs/Architecture.md](docs/Architecture.md).

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
