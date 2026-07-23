# SafeVixAI

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="CODE_OF_CONDUCT.md"><img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg" alt="Code of Conduct" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/issues"><img src="https://img.shields.io/github/issues/SafeVixAI/SafeVixAI" alt="Issues" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/stargazers"><img src="https://img.shields.io/github/stars/SafeVixAI/SafeVixAI" alt="Stars" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/releases"><img src="https://img.shields.io/github/v/release/SafeVixAI/SafeVixAI" alt="Release" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/actions/workflows/backend.yml"><img src="https://img.shields.io/github/actions/workflow/status/SafeVixAI/SafeVixAI/backend.yml?label=tests" alt="Tests" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/security"><img src="https://img.shields.io/badge/SBOM-available-brightgreen" alt="SBOM" /></a>
  <a href="ROADMAP.md"><img src="https://img.shields.io/badge/roadmap-available-brightgreen" alt="Roadmap" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/SafeVixAI/SafeVixAI"><img src="https://img.shields.io/badge/Scorecard-Passing-brightgreen" alt="OpenSSF Scorecard" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/actions/workflows/codeql.yml"><img src="https://img.shields.io/badge/CodeQL-Analysis-blue" alt="CodeQL" /></a>
</p>

<p align="center">
  <strong>AI-powered road safety platform.</strong><br/>
  Emergency response · Traffic legal assistance · Road infrastructure reporting.<br/>
  Offline-first PWA with enterprise-grade security and monitoring.
</p>

| Metric | Value |
|--------|-------|
| Unit Tests | **7,160+ passing** — Frontend 2,956 / Backend 2,750 / Chatbot 1,613 |
| E2E Tests | 55/55 passing |
| LLM Providers | 10-provider fallback chain |
| Services | 3 (frontend :3000, backend :8000, chatbot :8010) |
| Coverage | Backend 100% / Frontend 86% lines / Chatbot 97%+ |
| CI Workflows | 40 (security, load, chaos, E2E, migration, benchmark) |

---

## Overview

SafeVixAI is a three-service monorepo delivering real-time emergency response, AI-powered traffic legal assistance, and road infrastructure reporting through an offline-capable progressive web application.

| Module | Function | Offline |
|--------|----------|---------|
| Emergency Locator | Nearest hospital, police, ambulance via PostGIS geospatial queries | Yes — 25 Indian cities |
| AI Chatbot | Traffic law, challan calculation, first aid via agentic RAG with 10 LLM providers | Yes — Phi-3 Mini in-browser |
| Challan Calculator | Deterministic MVA 2019 fine calculation with 36 state/UT overrides | Yes — DuckDB-Wasm |
| Road Reporter | Submit pothole/damage reports with photo geotagging, routed to civic authorities | Yes — IndexedDB queue |
| SOS + Live Tracking | Hold-to-activate emergency alert with WebSocket-based family tracking | Yes — offline queue + flush |
| Command Center | Real-time agency dashboard with incident timeline, analytics, escalation | Dashboard (live data online) |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Git

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows
pip install -r requirements.txt
cp .env.example .env               # Configure your environment
uvicorn main:app --reload --port 8000
```

Verify: `GET http://localhost:8000/health`

### Chatbot Service
```bash
cd chatbot_service
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows
pip install -r requirements.txt
cp .env.example .env               # Configure your LLM provider keys
uvicorn main:app --reload --port 8010
```

Verify: `GET http://localhost:8010/health`

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # Configure your API endpoints
npm run dev
```

Verify: `http://localhost:3000`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 15 + React 19 + TypeScript PWA)         │
│  Port 3000 — MapLibre GL, WebLLM, DuckDB-Wasm, Zustand     │
└──────────────┬──────────────────────────┬───────────────────┘
               │ REST/WS (JWT Bearer)      │ REST (JWT Bearer)
┌──────────────▼─────────┐  ┌─────────────▼──────────────────┐
│  Backend (FastAPI)     │  │  Chatbot Service (FastAPI)     │
│  Port 8000             │  │  Port 8010                     │
│  PostgreSQL + PostGIS  │◄─┤  10-provider LLM fallback     │
│  Redis cache           │  │  ChromaDB RAG vector store     │
│  DuckDB (challan)      │  │  13 agent tools                │
│  Overpass/Nominatim    │  │  Redis conversation memory     │
│  WebSocket /tracking   │  │  Prompt injection defense      │
└────────────────────────┘  └────────────────────────────────┘
```

---

## Enterprise Features

| Layer | Capability | Implementation |
|-------|-----------|----------------|
| **Resilience** | 9-provider LLM fallback chain | Sequential fallback with timeout, TemplateProvider as last resort |
| **Resilience** | Circuit breaker | 3-failure threshold, 30s half-open on all 8 external API calls |
| **Resilience** | Cache stampede protection | SET NX EX mutex + stale-while-revalidate |
| **Resilience** | Distributed locking | Redlock with Redis + in-memory fallback |
| **Consistency** | CQRS bus | Command/Query buses with middleware for write-heavy operations |
| **Consistency** | Idempotency keys | SHA-256 hash + distributed lock for critical POST endpoints |
| **Security** | JWT authentication | RS256 + HS256, JWKS atomic key fetching with stampede protection |
| **Security** | Rate limiting | Token bucket per endpoint, Redis-backed |
| **Security** | CORS guard | Fail-fast RuntimeError if wildcard `*` in production |
| **Security** | Security headers | CSP, HSTS preload, XFO, COOP, CORP, COEP |
| **Observability** | Structured logging | JSON format with request_id, method, path, duration_ms |
| **Observability** | Prometheus metrics | Custom metrics per endpoint, Redis and Postgres exporters |
| **Observability** | Grafana dashboards | Provisioned dashboard with resource, latency, error, saturation views |
| **Observability** | Email alerting | SMTP with 5-min cooldown for all-provider failure, DB errors |
| **Supply Chain** | SLSA Level 3 | Build provenance attestation per commit |
| **Supply Chain** | Container signing | Cosign keyless signing via GitHub OIDC |
| **Supply Chain** | SBOM | CycloneDX + SPDX generated every build |
| **Supply Chain** | Secret scanning | Gitleaks pre-commit with 18 custom provider patterns |

---

## Security Hardening

| Layer | Protection | Location |
|-------|-----------|----------|
| CORS | Fail-fast `RuntimeError` if wildcard `*` in production | `backend/core/config.py` |
| Auth | JWT Bearer tokens + service-to-service API keys | `backend/api/v1/auth.py` |
| LLM Safety | 12-pattern prompt injection guard + SafetyChecker | `chatbot_service/agent/safety_checker.py` |
| LLM Timeout | `asyncio.wait_for()` on every provider call | `chatbot_service/providers/router.py` |
| Error Boundary | Global React error boundary | `frontend/app/error.tsx` |
| Env Validation | Throws at import if `NEXT_PUBLIC_*` URL missing | `frontend/lib/public-env.ts` |
| Host Validation | ALLOWED_HOSTS middleware | `backend/middleware/allowed_hosts.py` |

---

## Project Structure

```
SafeVixAI/
├── backend/              FastAPI Python 3.11 — PostgreSQL/PostGIS, Redis, DuckDB
│   ├── api/v1/           25 route modules
│   ├── core/             Config, security, caching, CQRS, Redlock, JWKS
│   ├── services/         16 domain services + 10 civic_intel modules
│   ├── models/           20 SQLAlchemy ORM models + Pydantic schemas
│   └── migrations/       Alembic — 11 migration files
├── chatbot_service/      FastAPI — Agentic RAG, 10 LLM providers, ChromaDB
│   ├── agent/            ChatEngine, IntentDetector, SafetyChecker
│   ├── providers/        LLM routing, lang_detection, provider_registry
│   ├── rag/              ChromaDB vector store, retriever, embeddings
│   └── tools/            13 agent tools (SOS, Challan, Legal, FirstAid, etc.)
├── frontend/             Next.js 15 + React 19 + TypeScript PWA
│   ├── app/              28 routes with error boundaries + loading states
│   ├── components/       91 components across 13 domains
│   └── lib/              28 modules — API client, state, offline AI, tracking
├── docs/                 Architecture, API, database, deployment, ADRs, runbooks
├── monitoring/           Prometheus config + Grafana dashboards + alert rules
├── k8s/                  Kubernetes manifests (kustomize)
├── terraform/            AWS infrastructure (VPC, ECS, RDS, ElastiCache)
└── .github/              40+ CI/CD workflows
```

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/Agent.md](docs/Agent.md) | Complete app overview for new developers |
| [docs/Architecture.md](docs/Architecture.md) | System architecture and data flows |
| [docs/API.md](docs/API.md) | All endpoints with request/response examples |
| [docs/Database.md](docs/Database.md) | Schema definitions and migration history |
| [docs/Deployment.md](docs/Deployment.md) | Deployment guides for Vercel, Render, Docker |
| [docs/adr/](docs/adr/) | 12 Architecture Decision Records |
| [docs/runbooks/](docs/runbooks/) | 12+ incident response runbooks |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [RELEASE.md](RELEASE.md) | Release process, versioning, rollback |
| [FAQ.md](FAQ.md) | Frequently asked questions |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and resolutions |

---

## Data Intelligence

The SafeVixAI intelligence layer — pre-trained models, road damage datasets, and legal archives — is hosted on the Hugging Face Dataset Hub.

**[SafeVixAI Dataset Hub](https://huggingface.co/datasets/SafeVixAI/SafeVixAI-Dataset-Hub)**

Research notebooks (Colab-ready, free T4 GPU):
1. **YOLOv8 Pothole Detection** — ONNX road damage model training
2. **ChromaDB RAG Build** — Vector store for legal document retrieval
3. **Accident EDA & Hotspot Generator** — Blackspot seed CSV + heatmap
4. **Roads Data Processing** — PMGSY GeoJSON sampling
5. **Risk Model ONNX Training** — Risk scoring model

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | FastAPI, SQLAlchemy (async), PostGIS, Redis (hiredis), DuckDB, Overpass/Nominatim |
| Chatbot | FastAPI, ChromaDB, LangChain, 10 LLM providers (Groq, Gemini, Sarvam AI, Cerebras, etc.) |
| Frontend | Next.js 15, React 19, TypeScript 5, Tailwind CSS 3, MapLibre GL, WebLLM, DuckDB-Wasm |
| Infrastructure | Docker Compose, Kubernetes (kustomize), Terraform (AWS), Vercel, Render |
| Monitoring | Prometheus, Grafana, Sentry, structured JSON logging |
| CI/CD | GitHub Actions (40+ workflows) |

---

## Testing

| Layer | Framework | Tests | Coverage |
|-------|-----------|-------|----------|
| Backend | pytest + hypothesis + testcontainers | 2,750 | 100% lines, 100% branches |
| Chatbot | pytest + pytest-httpx + ChromaDB integration | 1,613 | 97%+ lines |
| Frontend | Jest + React Testing Library + jest-axe | 2,956 | 86% lines, 72% branches |
| E2E | Playwright | 55 | — |
| Mutation | mutmut (backend) | — | CI (informational) |

---

## Contributing

We welcome contributions of all sizes. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

- Report bugs: [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues)
- Feature requests: [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.yml)
- Security vulnerabilities: [SECURITY.md](SECURITY.md)
- Governance: [GOVERNANCE.md](GOVERNANCE.md)
- Roadmap: [ROADMAP.md](ROADMAP.md)
- Support: [SUPPORT.md](SUPPORT.md)
- All contributions under [MIT License](LICENSE)

## License

MIT License — see [LICENSE](LICENSE) for details.
