# Operations

> **Day-to-day operations, deployment procedures, scaling, and environment management.**

SafeVixAI runs on zero-cost infrastructure: Vercel (frontend), Render (backend + chatbot), Supabase (PostgreSQL), Upstash (Redis).

---

## Quick Links

| Area | Documentation |
|------|---------------|
| Deployment Guide | [`docs/Deployment.md`](docs/Deployment.md) |
| Deployment Strategies | [`docs/DEPLOYMENT_STRATEGIES.md`](docs/DEPLOYMENT_STRATEGIES.md) |
| Advanced Setup | [`docs/ADVANCED_SETUP.md`](docs/ADVANCED_SETUP.md) |
| Scaling Guide | [`docs/SCALING_GUIDE.md`](docs/SCALING_GUIDE.md) |
| Docker Compose | [`docs/DOCKER_COMPOSE_GUIDE.md`](docs/DOCKER_COMPOSE_GUIDE.md) |
| Environment Config | [`docs/operations/environment-configuration.md`](docs/operations/environment-configuration.md) |
| Maintenance Guide | [`docs/operations/maintenance-guide.md`](docs/operations/maintenance-guide.md) |
| Monitoring Setup | [`docs/MONITORING_SETUP.md`](docs/MONITORING_SETUP.md) |
| Runbooks | [`RUNBOOKS.md`](RUNBOOKS.md) |
| Kubernetes | [`k8s/README.md`](k8s/README.md) |
| Terraform (AWS) | [`terraform/README.md`](terraform/README.md) |

---

## Service Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │◀───▶│   Chatbot   │
│  Vercel     │     │  Render     │     │  Render     │
│  :3000      │     │  :8000      │     │  :8010      │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                    ┌──────▼──────┐      ┌──────▼──────┐
                    │  PostgreSQL  │      │    Redis     │
                    │  Supabase    │      │   Upstash    │
                    │  + PostGIS   │      │              │
                    └─────────────┘      └─────────────┘
```

---

## Deployment Commands

```bash
# Local full stack
docker compose up --build

# Backend
cd backend && uvicorn main:app --reload --port 8000

# Chatbot
cd chatbot_service && uvicorn main:app --reload --port 8010

# Frontend
cd frontend && npm run dev
```

---

## Environment Variables

| Service | Key Variables |
|---------|--------------|
| Backend | `DATABASE_URL`, `REDIS_URL`, `ADMIN_SECRET`, `OVERPASS_URLS` |
| Chatbot | `DEFAULT_LLM_PROVIDER`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `CHROMA_PERSIST_DIR` |
| Frontend | `NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_CHATBOT_URL` |

Complete reference: [`CONFIGURATION.md`](CONFIGURATION.md)

---

## Related

- [`OBSERVABILITY.md`](OBSERVABILITY.md) — metrics, logs, traces, alerting
- [`RUNBOOKS.md`](RUNBOOKS.md) — incident response procedures
- [`MONITORING.md`](MONITORING.md) — dashboard setup
