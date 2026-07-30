# Configuration Reference

> Version 1.0.0 | Last updated: 2026-07-29

This document describes all configuration parameters across the three services.

## Configuration Flow

```mermaid
flowchart LR
    subgraph Sources[".env Sources"]
        BE[".env<br/>backend/"]
        CE[".env<br/>chatbot_service/"]
        FE[".env.local<br/>frontend/"]
    end

    subgraph Pydantic["pydantic-settings Validation"]
        BS[BackendSettings<br/>DATABASE_URL, REDIS_URL<br/>OVERPASS_URLS, ADMIN_SECRET]
        CS[ChatbotSettings<br/>DEFAULT_LLM_PROVIDER<br/>CHROMA_PERSIST_DIR]
        FS[PublicEnv<br/>NEXT_PUBLIC_BACKEND_URL<br/>NEXT_PUBLIC_CHATBOT_URL]
    end

    subgraph State["App State (lifespan)"]
        AS[app.state<br/>db, redis, services]
        CAS[app.state<br/>ChatEngine, VectorStore]
    end

    subgraph Services["Consumed By"]
        BSRV[Backend Services<br/>challan, roadwatch<br/>emergency, tracking]
        CSRV[Chatbot Services<br/>agent, providers<br/>rag, tools]
        FSRV[Frontend Components<br/>pages, hooks<br/>offline-ai, duckdb]
    end

    BE --> BS --> AS --> BSRV
    CE --> CS --> CAS --> CSRV
    FE --> FS --> FSRV
```

## Redis Cache Key Patterns

```mermaid
flowchart LR
    subgraph Patterns["Redis Cache Key Patterns & TTL"]
        direction TB
        SK["session:{user_id}<br/>TTL: 24h"]
        CK["challan:{violation}:{state}<br/>TTL: 1h"]
        GK["geocode:{lat}:{lon}<br/>TTL: 7d"]
        WK["weather:{lat}:{lon}<br/>TTL: 30min"]
        EK["emergency:{lat}:{lon}<br/>TTL: 5min"]
        RK["rate_limit:{ip}:{endpoint}<br/>TTL: 1min"]
        LK["lock:{resource}<br/>TTL: 10s (NX EX mutex)"]
    end
```

## Backend Configuration (backend/.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | No | In-memory fallback | `redis://:password@host:6379/0` or `rediss://` |
| `CHATBOT_SERVICE_URL` | Yes | `http://localhost:8010/api/v1` | Chatbot service address |
| `ADMIN_SECRET` | Yes | - | Protects admin-only endpoints |
| `CORS_ORIGINS` | No | `["*"]` | Allowed origins (comma-separated) |
| `ENVIRONMENT` | No | `development` | `development`, `staging`, `production` |
| `SENTRY_DSN` | No | - | Sentry error tracking DSN |
| `SUPABASE_URL` | No | - | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | No | - | Supabase service role key |
| `SUPABASE_JWT_SECRET` | No | - | JWT secret for token verification |
| `OPENROUTESERVICE_API_KEY` | No | - | Route optimization API |
| `OVERPASS_URLS` | No | `https://overpass-api.de/api/interpreter` | Overpass API endpoints |
| `DATA_GOV_API_KEY` | No | - | Indian government data portal |
| `OPENWEATHER_API_KEY` | No | - | Weather data |
| `LOCAL_UPLOAD_BASE_URL` | No | `/uploads` | Uploaded file URL prefix |
| `MCP_ENABLED` | No | `false` | Enable MCP server |
| `REDIS_TLS_ENABLED` | No | `false` | Enable Redis TLS (`rediss://`) |
| `REDIS_PASSWORD` | No | - | Redis password |
| `DEFAULT_RADIUS` | No | `5000` | Default emergency search radius (m) |
| `MAX_RADIUS` | No | `50000` | Maximum search radius (m) |
| `CACHE_TTL` | No | `3600` | Default cache TTL (seconds) |

## Chatbot Service Configuration (chatbot_service/.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEFAULT_LLM_PROVIDER` | Yes | `groq` | Primary LLM provider |
| `DEFAULT_LLM_MODEL` | Yes | `llama-3.1-8b-instant` | Model ID for provider |
| `GROQ_API_KEY` | For Groq | - | Groq API key |
| `CEREBRAS_API_KEY` | For Cerebras | - | Cerebras API key |
| `GEMINI_API_KEY` | For Gemini | - | Google AI API key |
| `SARVAM_API_KEY` | For Sarvam | - | Sarvam AI API key |
| `GITHUB_TOKEN` | For GitHub Models | - | GitHub PAT |
| `NVIDIA_NIM_API_KEY` | For NVIDIA | - | NVIDIA API key |
| `OPENROUTER_API_KEY` | For OpenRouter | - | OpenRouter API key |
| `MISTRAL_API_KEY` | For Mistral | - | Mistral API key |
| `TOGETHER_API_KEY` | For Together | - | Together AI API key |
| `HF_TOKEN` | No | - | HuggingFace token (Sarvam fallback) |
| `MAIN_BACKEND_BASE_URL` | Yes | `http://localhost:8000` | Backend API URL |
| `REDIS_URL` | No | In-memory fallback | Redis for conversation memory |
| `CHROMA_PERSIST_DIR` | No | `./data/chroma_db` | ChromaDB persistence path |
| `EMBEDDING_MODEL` | No | `LocalHashEmbeddingFunction` | Embedding model config |
| `CORS_ORIGINS` | No | `["*"]` | Allowed origins |
| `W3W_API_KEY` | No | - | What3Words API key |
| `OPENCAGE_API_KEY` | No | - | OpenCage geocoding fallback |

## Frontend Configuration (frontend/.env.local)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | Yes | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_CHATBOT_URL` | Yes | `http://localhost:8010` | Chatbot service URL |
| `NEXT_PUBLIC_POSTHOG_KEY` | No | - | PostHog analytics key |
| `NEXT_PUBLIC_POSTHOG_HOST` | No | `https://app.posthog.com` | PostHog host |

## Docker Compose

See `docker-compose.yml` for full configuration. Key resource limits:

| Service | Memory | CPU | Image |
|---------|--------|-----|-------|
| postgres | 512M | 1.0 | postgis/postgis:16-3.4 |
| redis | 256M | 0.5 | redis:7-alpine |
| backend | 512M | 1.0 | ./backend/Dockerfile |
| chatbot | 2G | 2.0 | ./chatbot_service/Dockerfile |
| frontend | 512M | 1.0 | ./frontend/Dockerfile.frontend |

## Python Tool Configuration

### Ruff (pyproject.toml)
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "ARG", "C4", "EM", "G", "PIE", "T20"]
ignore = ["E501", "B008", "B904"]
[tool.ruff.format]
quote-style = "double"
```

### Pytest

**Backend:** `asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function`
**Chatbot:** `asyncio_mode = strict`

### Coverage

**Backend:** `fail_under = 100`, branch coverage enabled
**Chatbot:** `fail_under = 100`, branch coverage enabled
**Frontend (Jest):** lines 86, branches 72, functions 80, statements 85

### Jest (jest.config.js)
```javascript
coverageThreshold: {
  global: { lines: 86, branches: 72, functions: 80, statements: 85 }
}
```

## Redis Cache Key Patterns

| Key Pattern | TTL | Description |
|-------------|-----|-------------|
| `emergency:category:{cat}:lat:{lat}:lon:{lon}:radius:{r}` | 3600s | Emergency service results |
| `geocode:search:{query}` | 86400s | Forward geocoding |
| `geocode:reverse:{lat}:{lon}` | 86400s | Reverse geocode |
| `authority:lat:{lat}:lon:{lon}` | 3600s | Authority routing |
| `route:{start}:{end}:{profile}` | 900s | Route calculation |
| `ward:{ward_id}` | 3600s | Ward data |
| `chat_session:{session_id}` | 86400s | Conversation memory |
| `circuit_breaker:{name}` | INFINITY | Circuit breaker state |
| `jwks:public_keys` | 3600s | JWKS public keys |

## Rate Limits (slowapi — IP-based)

| Endpoint Group | Limit |
|----------------|-------|
| General API | 100 req/min |
| Auth (login, signup) | 5 req/min |
| SOS / Emergency | 3 req/min |
| Challan Calculate | 60 req/min |
| Chat (blocking + stream) | 30 req/min |
| Geocoding | 30 req/min |
