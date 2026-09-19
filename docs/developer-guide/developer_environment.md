# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

# Developer Guide

## Development Environment

### Required Tools

- **Node.js** 20+, npm 10+
- **Python** 3.11+
- **PostgreSQL** 16 with PostGIS extension
- **Redis** 7
- **VS Code** (recommended) or any Python/TypeScript IDE

### Recommended VS Code Extensions

- ESLint, Prettier, Tailwind CSS IntelliSense
- Python, Pylance, Ruff
- Thunder Client or REST Client (API testing)
- GitLens
- YAML Language Support

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Runs ruff (Python lint), eslint (TypeScript lint), and secrets scanning on every commit.

## Repository Structure

```
SafeVixAI/
├── backend/                FastAPI :8000 — REST API + PostGIS + Redis
│   ├── api/v1/             25+ route modules
│   ├── core/               Config, database, Redis, security, CQRS
│   ├── services/           16 business logic modules
│   ├── models/             SQLAlchemy ORM + Pydantic schemas
│   ├── migrations/         Alembic (3 migrations)
│   └── tests/              pytest (2750+ tests)
├── chatbot_service/        FastAPI :8010 — Agentic RAG chatbot
│   ├── agent/              ChatEngine, Intents, Safety, Context
│   ├── providers/          9 LLM provider implementations
│   ├── tools/              13 agent tools
│   ├── rag/                ChromaDB vector store
│   ├── memory/             Conversation memory
│   └── tests/              pytest (1600+ tests)
├── frontend/               Next.js 15 PWA — React 19
│   ├── app/                28 routes
│   ├── components/         91 components
│   ├── lib/                28 modules (store, API, utils)
│   ├── hooks/              18 custom hooks
│   └── tests/              Jest + RTL (2900+ tests)
├── docs/                   MkDocs documentation site
├── examples/               Runnable code examples (Python + TypeScript)
├── scripts/                Data pipeline scripts
└── k8s/                    Kubernetes manifests
```

## How to Add a New API Endpoint

1. **Create** `backend/api/v1/new_feature.py`:
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/api/v1/feature", tags=["Feature"])

   @router.get("/")
   async def list_items():
       return {"items": []}
   ```
2. **Register** in `backend/api/v1/__init__.py`:
   ```python
   from api.v1.new_feature import router as feature_router
   api_router.include_router(feature_router)
   ```
3. **Add tests** in `backend/tests/test_new_feature.py`
4. **Run**: `cd backend && pytest tests/test_new_feature.py -v`

## How to Add a New Frontend Page

1. **Create** `frontend/app/new-page/page.tsx` with `'use client'` directive
2. **Add optional** `loading.tsx` and `error.tsx` for loading/error states
3. **Add route metadata** if needed (SEO, OG tags)
4. **Update navigation** in any sidebar or header components

## How to Add a New LLM Provider

1. **Create** `chatbot_service/providers/new_provider.py`
2. **Implement** the `Provider` interface with `generate()` and `supports_streaming()` methods
3. **Register** in `provider_registry.py` (mapping from provider name to class)
4. **Add API key** environment variable to `config.py`
5. **Add** to fallback chain in `router.py` (provider order determines priority)

## How to Add a New Database Migration

```bash
cd backend
alembic revision --autogenerate -m "description_of_change"
alembic upgrade head
```

New model classes go in `backend/models/`. Always add PostGIS extensions before using geography columns.

## Testing Guide

| Layer | Framework | Command |
|-------|-----------|---------|
| Backend | pytest + pytest-asyncio | `cd backend && pytest` |
| Chatbot | pytest (asyncio_mode=strict) | `cd chatbot_service && pytest` |
| Frontend | Jest + React Testing Library | `cd frontend && npm test` |
| Frontend lint | ESLint | `cd frontend && npm run lint` |
| Frontend build | TypeScript | `cd frontend && npm run build` |
| E2E | Playwright | `npm run test:e2e` |

## Debugging Tips

- **Backend logs**: `docker compose logs backend`
- **Chatbot logs**: `docker compose logs chatbot`
- **Redis CLI**: `docker compose exec redis redis-cli`
- **DB queries**: `docker compose exec postgres psql -U postgres safevixai`
- **Frontend dev tools**: React DevTools, Lighthouse, Network tab
- **Slow queries**: `cd backend && python -m scripts.tail_slow_queries`
- **Chatbot metrics**: `curl http://localhost:8010/metricics | grep chatbot_response_time`

## Environment Variables

Each service has its own `.env` file (gitignored). See `.env.example` in each directory.

| Service | Key Variable | Default |
|---------|-------------|---------|
| Backend | `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/safevixai` |
| Backend | `REDIS_URL` | (in-memory fallback) |
| Chatbot | `DEFAULT_LLM_PROVIDER` | `groq` |
| Chatbot | `MAIN_BACKEND_BASE_URL` | `http://localhost:8000` |
| Frontend | `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8000` |
| Frontend | `NEXT_PUBLIC_CHATBOT_URL` | `http://localhost:8010` |

## Code Style

- Python: Ruff (line length 100), type hints required
- TypeScript: ESLint + Prettier (single quotes, semicolons)
- Tests: `function()` keyword in describe/it blocks, `var` for module-level mocks
- All files: SPDX license header `SPDX-License-Identifier: MIT`
