# SafeVixAI Documentation

<p align="center">
  <strong>Enterprise AI-Powered Road Safety & Emergency Response Platform</strong><br/>
  Emergency response · Traffic legal assistance · Road infrastructure reporting<br/>
  Offline-first PWA with enterprise-grade security, resilience, and monitoring
</p>

---

## Platform Overview

```mermaid
flowchart LR
    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87

    FE["Frontend PWA<br/>Next.js 15 · React 19"]:::edge
    BE["Backend API<br/>FastAPI :8000"]:::control
    CB["AI Chatbot<br/>FastAPI :8010"]:::ai

    FE -- "REST / WebSocket" --> BE
    FE -- "REST" --> CB
    BE <--> CB
```

---

## Quick Navigation

| Section | Key Documents |
|:--------|:-------------|
| **Getting Started** | [Setup Guide](developer-guide/SETUP.md) · [Starter Guide](developer-guide/STARTER_GUIDE.md) |
| **Architecture** | [System Architecture](architecture/Architecture.md) · [Tech Stack](architecture/TechStack.md) · [Design](architecture/DESIGN.md) |
| **AI & Agents** | [AI Overview](architecture/AI.md) · [Chatbot Pipeline](developer-guide/AI_Instructions.md) · [RAG](architecture/RAG.md) · [Memory](architecture/MEMORY.md) |
| **API & SDK** | [API Reference](api-reference/API.md) · [SDK Guide](api-reference/SDK_GUIDE.md) · [Error Codes](api-reference/ERROR_CODES.md) |
| **Database** | [Schema](architecture/Database.md) |
| **Security** | [Security Policy](architecture/Security.md) · [Authentication](architecture/AUTHENTICATION.md) · [Authorization](architecture/AUTHORIZATION.md) · [Privacy](compliance-and-reports/PRIVACY.md) |
| **Operations** | [Operations Overview](sre/OPERATIONS.md) · [Monitoring](sre/MONITORING.md) · [Observability](sre/OBSERVABILITY.md) · [Benchmarks](compliance-and-reports/BENCHMARKS.md) |
| **Runbooks** | [Runbooks Overview](sre/RUNBOOKS.md) |
| **Development** | [Contributing](developer-guide/Contributing.md) · [Style Guide](developer-guide/STYLE_GUIDE.md) · [Testing](developer-guide/TESTING.md) · [Best Practices](developer-guide/BEST_PRACTICES.md) |
| **Community** | [Roadmap](product-and-planning/Roadmap.md) · [FAQ](product-and-planning/FAQ.md) |

---

## Service Status

| Service | Port | Health Check | Technology |
|:--------|:-----|:-------------|:-----------|
| **Backend** | `:8000` | `GET /health` | FastAPI + PostgreSQL + Redis |
| **Chatbot** | `:8010` | `GET /health` | FastAPI + ChromaDB + 10 LLMs |
| **Frontend** | `:3000` | PWA available | Next.js 15 + React 19 |

---

## Quick Commands

```bash
# Full stack (recommended)
docker compose up --build

# Individual services
cd backend && uvicorn main:app --reload --port 8000
cd chatbot_service && uvicorn main:app --reload --port 8010
cd frontend && npm run dev
```

---

## Test Coverage

| Service | Tests | Coverage |
|:--------|------:|:--------:|
| Backend | 2,908 | 100% |
| Chatbot | 1,819 | 97%+ |
| Frontend | 2,956 | 87%+ |
| E2E | 55 | — |
| **Total** | **7,738** | — |

---

## Contributing

See [CONTRIBUTING.md](developer-guide/Contributing.md) for contribution guidelines.
All contributions under [MIT License](../LICENSE).
