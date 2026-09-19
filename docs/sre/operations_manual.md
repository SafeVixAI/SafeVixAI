# Operations

> **Day-to-day operations, deployment procedures, scaling, and environment management.**

SafeVixAI runs on zero-cost infrastructure: Vercel (frontend), Render (backend + chatbot), Supabase (PostgreSQL), Upstash (Redis).

---

## Quick Links

| Area | Documentation |
|------|---------------|
| Deployment Guide | [`docs/Deployment.md`](deployment_guide.md) |
| Deployment Strategies | [`docs/DEPLOYMENT_STRATEGIES.md`](deployment_strategies.md) |
| Advanced Setup | [`docs/ADVANCED_SETUP.md`](advanced_setup.md) |
| Scaling Guide | [`docs/SCALING_GUIDE.md`](scaling_guide.md) |
| Docker Compose | [`docs/DOCKER_COMPOSE_GUIDE.md`](../developer-guide/docker_compose_guide.md) |
| Environment Config | [`docs/operations/environment-configuration.md`](environment_configuration.md) |
| Maintenance Guide | [`docs/operations/maintenance-guide.md`](routine_maintenance.md) |
| Monitoring Setup | [`docs/MONITORING_SETUP.md`](../spec/engineering/metrics.spec.md) |
| Runbooks | [`RUNBOOKS.md`](runbooks_overview.md) |
| Kubernetes | [`k8s/README.md`](../incident-response/response_protocol.md) |
| Terraform (AWS) | [`terraform/README.md`](../incident-response/response_protocol.md) |

---

## Service Architecture

```mermaid
flowchart LR
    subgraph Client["Client Layer"]
        F[Frontend<br/>Vercel :3000<br/>Next.js PWA]
    end

    subgraph API["API Layer"]
        B[Backend<br/>Render :8000<br/>FastAPI]
        CB[Chatbot<br/>Render :8010<br/>FastAPI]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL<br/>Supabase + PostGIS)]
        RD[(Redis<br/>Upstash)]
    end

    F -->|REST/WS JWT| B
    F -->|REST JWT| CB
    B <--> CB
    B --> PG
    B --> RD
    CB --> RD
```

## Deployment Workflow

```mermaid
flowchart TB
    subgraph Dev["Development"]
        CODE[code push]
        PR[pull request]
    end

    subgraph CI["CI Pipeline"]
        LINT[lint & typecheck]
        TEST[unit tests]
        COV[coverage check]
        BUILD[production build]
    end

    subgraph Deploy["Deployment"]
        FEND[Vercel<br/>Frontend]
        BEND[Render<br/>Backend]
        CHAT[Render<br/>Chatbot]
        DB[(Supabase<br/>PostgreSQL)]
    end

    CODE --> PR
    PR --> LINT --> TEST --> COV --> BUILD
    BUILD --> FEND
    BUILD --> BEND
    BUILD --> CHAT
    BEND --> DB
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

Complete reference: [`CONFIGURATION.md`](../spec/engineering/env_configuration.spec.md)

---

## Related

- [`OBSERVABILITY.md`](observability.md) — metrics, logs, traces, alerting
- [`RUNBOOKS.md`](runbooks_overview.md) — incident response procedures
- [`MONITORING.md`](monitoring_overview.md) — dashboard setup
