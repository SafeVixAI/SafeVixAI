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
| **Getting Started** | [Setup Guide](../SETUP.md) · [Starter Guide](STARTER_GUIDE.md) · [Quick Start](../README.md) |
| **Architecture** | [System Architecture](Architecture.md) · [Tech Stack](TechStack.md) · [Design](DESIGN.md) |
| **AI & Agents** | [AI Overview](../AI.md) · [Agent System](../AGENTS.md) · [Chatbot Pipeline](AI_Instructions.md) · [RAG](../RAG.md) · [Memory](../MEMORY.md) |
| **API & SDK** | [API Reference](API.md) · [SDK Guide](../SDK_GUIDE.md) · [Error Codes](../ERROR_CODES.md) |
| **Database** | [Schema](Database.md) · [Migration Guide](MIGRATION_GUIDE.md) · [Upgrade Guide](UPGRADE_GUIDE.md) |
| **Security** | [Security Policy](../SECURITY.md) · [Authentication](AUTHENTICATION.md) · [Authorization](AUTHORIZATION.md) · [Privacy](../PRIVACY.md) |
| **Operations** | [Operations Overview](../OPERATIONS.md) · [Monitoring](../MONITORING.md) · [Observability](../OBSERVABILITY.md) · [Benchmarks](../BENCHMARKS.md) |
| **Runbooks** | [Runbooks Overview](../RUNBOOKS.md) · [All LLMs Down](runbooks/all-llms-down.md) · [DB Down](runbooks/db-down.md) |
| **Development** | [Contributing](../CONTRIBUTING.md) · [Style Guide](../STYLE_GUIDE.md) · [Testing](../TESTING.md) · [Best Practices](BEST_PRACTICES.md) |
| **Examples** | [Example Overview](../examples/README.md) · [API Client](../examples/api-client/README.md) · [Cookbook](../examples/cookbook/README.md) |
| **Community** | [Governance](../GOVERNANCE.md) · [Maintainers](../MAINTAINERS.md) · [Roadmap](../ROADMAP.md) · [FAQ](../FAQ.md) |

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

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.
All contributions under [MIT License](../LICENSE).
