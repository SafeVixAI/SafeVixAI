# Docker Compose Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [Deployment.md](./Deployment.md), [ADVANCED_SETUP.md](./ADVANCED_SETUP.md)

---

## Overview

The `docker-compose.yml` at the project root defines 5 services:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `postgres` | postgis/postgis:16-3.4 | 5432 | Database with PostGIS |
| `redis` | redis:7-alpine | 6379 | Cache and conversation memory |
| `backend` | safevixai/backend | 8000 | FastAPI backend |
| `chatbot` | safevixai/chatbot | 8010 | Chatbot service |
| `frontend` | safevixai/frontend | 3000 | Next.js PWA |

---

## Quick Start

```bash
# Build and start all services
docker compose up --build

# Start in background
docker compose up --build -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

Verify:
```bash
curl http://localhost:8000/health
curl http://localhost:8010/health
# Open http://localhost:3000
```

---

## Environment Variables

### Backend
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://safevixai:safevixai@postgres:5432/safevixai` | PostgreSQL connection |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `CHATBOT_SERVICE_URL` | `http://chatbot:8010/api/v1` | Chatbot API URL |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |

### Chatbot
| Variable | Default | Description |
|----------|---------|-------------|
| `MAIN_BACKEND_BASE_URL` | `http://backend:8000` | Backend API URL |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `CHROMA_PERSIST_DIR` | `/app/data/chroma_db` | ChromaDB persistence path |

### Frontend
| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_CHATBOT_URL` | `http://localhost:8010` | Chatbot API URL |

---

## Volumes

| Service | Volume | Purpose |
|---------|--------|---------|
| postgres | `postgres_data:/var/lib/postgresql/data` | Persist database |
| redis | `redis_data:/data` | Persist Redis (RDB/AOF) |
| backend | `./data:/app/data` | Uploaded files, ChromaDB |
| chatbot | `./data:/app/data` | ChromaDB persistence |

---

## Networking

Services communicate via a Docker network:

```
frontend → backend:8000 (REST)
frontend → chatbot:8010 (REST)
backend  → chatbot:8010 (REST, internal)
backend  → postgres:5432 (internal)
backend  → redis:6379 (internal)
chatbot  → redis:6379 (internal)
```

---

## Development with Docker

### Hot Reload
For development, mount source directories:

```yaml
services:
  backend:
    volumes:
      - ./backend:/app
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  chatbot:
    volumes:
      - ./chatbot_service:/app
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8010

  frontend:
    volumes:
      - ./frontend:/app
```

### Running Tests
```bash
docker compose exec backend pytest tests/ -v
docker compose exec chatbot pytest tests/ -v
docker compose exec frontend npm test
```

---

## Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
services:
  backend:
    image: ghcr.io/safevixai/backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ADMIN_SECRET=${ADMIN_SECRET}
    deploy:
      replicas: 3

  chatbot:
    image: ghcr.io/safevixai/chatbot:latest
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

Run:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs backend
docker compose logs chatbot

# Check if ports are available
netstat -an | grep 3000
netstat -an | grep 8000
netstat -an | grep 8010
```

### Database Migration Fails
```bash
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

### Reset Everything
```bash
docker compose down --volumes  # WARNING: Deletes all data
docker compose up --build
```

### Rebuild Single Service
```bash
docker compose up --build -d backend
```

---

## Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  chatbot:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G  # PyTorch needs more

  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

---

## CI/CD Integration

The `docker-compose.yml` is used in CI for integration tests:

```yaml
# .github/workflows/e2e.yml
jobs:
  test:
    services:
      postgres:
        image: postgis/postgis:16-3.4
        ports:
          - 5432:5432
```
