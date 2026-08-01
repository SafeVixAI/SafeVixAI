# SafeVixAI Documentation

<p align="center">
  <strong>AI-powered road safety platform.</strong><br/>
  Emergency response · Traffic legal assistance · Road infrastructure reporting.<br/>
  Offline-first PWA with enterprise-grade security, resilience, and monitoring.
</p>

---

## Quick Navigation

| Section | Key Documents |
|---------|---------------|
| **Getting Started** | [Setup Guide](developer-guide/SETUP.md) · [Starter Guide](developer-guide/STARTER_GUIDE.md) · [Quick Start](adr/README.md) |
| **Architecture** | [System Architecture](architecture/Architecture.md) · [Tech Stack](architecture/TechStack.md) · [Design](architecture/DESIGN.md) |
| **AI & Agents** | [AI Overview](architecture/AI.md) · [Agent System](../AGENTS.md) · [Chatbot Pipeline](developer-guide/AI_Instructions.md) · [RAG](architecture/RAG.md) · [Memory](architecture/MEMORY.md) |
| **API & SDK** | [API Reference](api-reference/API.md) · [SDK Guide](api-reference/SDK_GUIDE.md) · [Error Codes](api-reference/ERROR_CODES.md) |
| **Database** | [Schema](architecture/Database.md) · [Migration Guide](sre/MIGRATION_GUIDE.md) · [Upgrade Guide](sre/UPGRADE_GUIDE.md) |
| **Security** | [Security Policy](architecture/Security.md) · [Authentication](architecture/AUTHENTICATION.md) · [Authorization](architecture/AUTHORIZATION.md) · [Privacy](compliance-and-reports/PRIVACY.md) |
| **Operations** | [Operations Overview](sre/OPERATIONS.md) · [Monitoring](sre/MONITORING.md) · [Observability](sre/OBSERVABILITY.md) · [Benchmarks](compliance-and-reports/BENCHMARKS.md) |
| **Runbooks** | [Runbooks Overview](sre/RUNBOOKS.md) · [All LLMs Down](sre/runbooks/all-llms-down.md) · [DB Down](sre/runbooks/db-down.md) |
| **Development** | [Contributing](developer-guide/Contributing.md) · [Style Guide](developer-guide/STYLE_GUIDE.md) · [Testing](developer-guide/TESTING.md) · [Best Practices](developer-guide/BEST_PRACTICES.md) |
| **Examples** | [Example Overview](adr/README.md) · [API Client](adr/README.md) · [Cookbook](adr/README.md) |
| **Community** | [Governance](../GOVERNANCE.md) · [Maintainers](../MAINTAINERS.md) · [Roadmap](developer-guide/chatbot/roadmap.md) · [FAQ](product-and-planning/FAQ.md) |

---

## Service Status

| Service | Port | Status |
|---------|------|--------|
| Backend (FastAPI) | `:8000` | `GET /health` |
| Chatbot (FastAPI) | `:8010` | `GET /health` |
| Frontend (Next.js) | `:3000` | PWA available |

---

## Quick Commands

```bash
# Full stack
docker compose up --build

# Individual services
cd backend && uvicorn main:app --reload --port 8000
cd chatbot_service && uvicorn main:app --reload --port 8010
cd frontend && npm run dev
```

---

## Contributing

See [CONTRIBUTING.md](developer-guide/Contributing.md) for contribution guidelines.
All contributions under [MIT License](../LICENSE).
