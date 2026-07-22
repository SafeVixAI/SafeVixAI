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
