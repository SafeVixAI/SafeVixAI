# Troubleshooting Guide

> **Version:** 1.0
> **Last updated:** 2026-07-29

## Diagnosis Flowcharts

### Backend Won't Start

```mermaid
flowchart TD
    A[Backend fails to start] --> B{Virtual env active?}
    B -->|No| C[Activate .venv]
    C --> D[Retry]
    D --> A

    B -->|Yes| E{Dependencies installed?}
    E -->|No| F[pip install -r requirements.txt]
    F --> D

    E -->|Yes| G{Python version >= 3.11?}
    G -->|No| H[Install Python 3.11+]
    H --> D

    G -->|Yes| I{.env configured?}
    I -->|No| J[cp .env.example .env<br/>Fill required values]
    J --> D

    I -->|Yes| K[Check port 8000 availability]
    K -->|In Use| L[netstat / taskkill or<br/>use different port]
    L --> D

    K -->|Free| M[Run: uvicorn main:app<br/>--reload --port 8000]
    M --> N{Any error output?}
    N -->|Yes| O[Read error message<br/>Check module imports]
    N -->|No| P[Backend running]

    O --> D
```

### 401 Unauthorized

```mermaid
flowchart TD
    A[API returns 401] --> B{Token exists?}
    B -->|No| C[Login to get JWT<br/>POST /api/v1/auth/login]
    C --> D[Retry with Bearer token]

    B -->|Yes| E{Token expired?}
    E -->|Yes| F[Refresh token<br/>POST /api/v1/auth/refresh]
    F --> D

    E -->|No| G{Header format correct?}
    G -->|No| H[Ensure format:<br/>Authorization: Bearer <token>]
    H --> D

    G -->|Yes| I{JWKS cache stale?}
    I -->|Yes| J[Purge cache<br/>POST /api/v1/admin/cache/purge]
    J --> D

    I -->|No| K[Token invalid - re-login]
    K --> C
```

### Map Not Loading

```mermaid
flowchart TD
    A[Map shows blank/empty] --> B{maplibre-gl.css imported?}
    B -->|No| C[Add to layout.tsx:<br/>import 'maplibre-gl/dist/maplibre-gl.css']
    C --> D[Reload page]

    B -->|Yes| E{Component wrapped in<br/>dynamic({ssr:false})?}
    E -->|No| F[Use: dynamic(() => import('...'),<br/>{ ssr: false })]
    F --> D

    E -->|Yes| G{Tile provider API key set?}
    G -->|No| H[Set tile API key in env<br/>or use default tiles]
    H --> D

    G -->|Yes| I{Browser DevTools errors?}
    I -->|Yes| J[Check console for<br/>WebGL or CORS errors]
    I -->|No| K[Map should render]
```

---

## Installation

### Backend Won't Start

**Symptom:** `uvicorn main:app --reload` fails with module not found errors.

**Causes:**
1. Virtual environment not activated
2. Dependencies not installed
3. Python version < 3.11

**Solutions:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Chatbot Service Won't Start

**Symptom:** `uvicorn main:app --reload --port 8010` crashes on startup.

**Causes:**
1. PyTorch/torchaudio not installed properly
2. Missing `.env` file
3. ChromaDB persist directory permissions

**Solutions:**
```bash
cd chatbot_service
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env  # or create from AGENTS.md
python -c "from core.config import Settings; print('Config OK')"
```

### Frontend Build Fails

**Symptom:** `npm run dev` or `npm run build` fails with compilation errors.

**Causes:**
- Missing `node_modules` or `package-lock.json`
- Node.js version < 20

**Solutions:**
```bash
cd frontend
node --version  # Must be >= 20
npm ci          # Clean install from lockfile
npm run dev
```

For `npm run build` failures related to `.next/types/`:
```
npm run build 2>&1 | head -50  # Check exact error
# If "Cannot find namespace 'React'" - this is a Next.js generated-code bug
# Workaround: npx next build --no-lint
```

---

## Database

### Connection Failed

**Symptom:** Backend logs `could not connect to server: Connection refused`.

**Causes:**
- PostgreSQL not running
- Wrong `DATABASE_URL` in `.env`
- Firewall blocking port 5432

**Solutions:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify DATABASE_URL format
# postgresql+asyncpg://user:password@host:port/dbname
```
If using Supabase: check the connection string in Supabase dashboard to Settings to Database.

### Alembic Migration Fails

**Symptom:** `alembic upgrade head` fails with relation already exists or column not found.

**Solutions:**
```bash
cd backend
alembic current          # Check current migration
alembic history         # View migration history
alembic upgrade head    # Apply all pending migrations
alembic downgrade -1    # Roll back last migration
```

### Migration Pending Error

**Symptom:** Health check returns `database_migration_pending`.

**Solution:** Run `alembic upgrade head` and restart the backend.

---

## Redis

### Connection Failed

**Symptom:** Backend logs `Error connecting to Redis: -100`.

**Solutions:**
- Redis is **optional** - backend falls back to in-memory cache
- If using Redis: verify `REDIS_URL` and that Redis is running
- For Upstash: use `rediss://` URL format (TLS)

### TLS Connection Error

**Symptom:** `SSL: WRONG_VERSION_NUMBER` on `rediss://` URLs.

**Solution:** Ensure `redis_tls_enabled: true` in backend config and `ssl=True` in the Redis connection string.

---

## API

### CORS Errors

**Symptom:** Browser console shows CORS errors when frontend calls backend.

**Solutions:**
- Verify `CORS_ORIGINS` env var includes your frontend URL
- For local development: `http://localhost:3000` must be in CORS origins
- For production: use exact domain (no wildcards in production)

### 401 Unauthorized

**Symptom:** API returns 401 even with valid JWT.

**Causes:**
- Token expired (default: 1 hour)
- Wrong authorization header format
- JWKS cache stale

**Solutions:**
- Refresh the token: `POST /api/v1/auth/refresh`
- Ensure header format: `Authorization: Bearer <token>`
- Clear JWKS cache: `POST /api/v1/admin/cache/purge`

### 429 Rate Limited

**Symptom:** API returns 429 Too Many Requests.

**Solution:** Check `Retry-After` header and wait before retrying. Rate limits are per-endpoint and per-IP.

### WebSocket Disconnects

**Symptom:** Tracking session WebSocket disconnects unexpectedly.

**Causes:**
- JWT token expired during session
- Network interruption
- Session timeout

**Solutions:**
- Ensure token is valid for the expected session duration
- Implement WebSocket reconnection with exponential backoff
- Check `session_timeout_seconds` config

---

## LLM Providers

### All Providers Fail

**Symptom:** Chatbot returns error that all 9 LLM providers failed.

**Causes:**
- API keys not configured
- Rate limits exceeded on all providers
- Network connectivity issues

**Solutions:**
```bash
# Check which provider keys are set
grep -E "_(API_KEY|TOKEN)" chatbot_service/.env | grep -v "^#"

# Test a single provider
curl -X POST http://localhost:8010/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "provider_hint": "template"}'
```
If all providers fail, the TemplateProvider should always work (deterministic responses).

### Specific Provider Fails

**Symptom:** Chatbot logs `Provider X failed, falling back to Y`.

**Solutions:**
- Check the provider's API key and rate limits
- See `chatbot_service/providers/` for provider-specific error handling
- The fallback chain automatically tries the next provider

### ChromaDB Vector Search Returns No Results

**Symptom:** Legal search returns empty results.

**Solutions:**
- Ensure ChromaDB vectorstore is built: `cd chatbot_service && python data/build_vectorstore.py`
- Verify `CHROMA_PERSIST_DIR` points to the correct directory
- Check that `chatbot_service/data/chroma_db/` exists and is not empty

---

## Frontend

### Map Not Loading

**Symptom:** MapLibre map shows blank/empty.

**Causes:**
- MapLibre CSS not imported
- Component not wrapped in `dynamic({ssr:false})`
- API key missing for tile provider

**Solutions:**
- Verify `maplibre-gl/dist/maplibre-gl.css` is imported in `layout.tsx`
- Map components must use `dynamic(() => import('...'), { ssr: false })`
- If using a non-default tile provider, set the API URL in env

### Service Worker Not Registering

**Symptom:** PWA features not working (offline mode, install prompt).

**Causes:**
- Running in `npm run dev` (Service Worker only works in production build)
- Service worker file not found

**Solutions:**
```bash
npm run build && npm start  # Production mode enables SW
```
Check DevTools to Application to Service Workers for registration status.

### PWA Install Prompt Not Showing

**Symptom:** Browser doesn't prompt to install the app.

**Solutions:**
- Must be served over HTTPS (or localhost)
- Must meet PWA criteria (manifest, SW, icons)
- In Chrome DevTools to Application to Manifest to "Add to homescreen"

### `crypto.randomUUID` Not Supported

**Symptom:** Frontend test fails with `crypto.randomUUID is not a function`.

**Solution:** This is a JSDOM limitation - ignored via Istanbul comments in the source code. Does not affect production (browsers support it).

### Speech Recognition Fails

**Symptom:** Voice input button does not capture speech.

**Solutions:**
- Chrome/Edge only (Firefox and Safari lack SpeechRecognition API)
- Ensure microphone permission is granted
- Check `window.SpeechRecognition || window.webkitSpeechRecognition`

### Geolocation Errors

**Symptom:** Location features show "Geolocation not supported".

**Solutions:**
- Browser must support `navigator.geolocation` (all modern browsers)
- User must grant location permission
- In JSDOM tests, navigator.geolocation is unavailable (expected)

---

## Docker

### Docker Compose Fails

**Symptom:** `docker compose up --build` fails on service startup.

**Solutions:**
```bash
# Check service logs
docker compose logs backend
docker compose logs chatbot_service
docker compose logs frontend

# Rebuild from scratch
docker compose down --volumes  # WARNING: deletes DB data
docker compose up --build
```

### PostgreSQL in Docker Fails

**Symptom:** PostGIS extension not available.

**Solution:** Use `postgis/postgis:16-3.4` image (not plain `postgres`).

### Memory Issues

**Symptom:** Container OOM-killed during build.

**Solutions:**
- Increase Docker memory limit: Docker Desktop to Settings to Resources
- For chatbot service (torch): allocate at least 2GB RAM

---

## Testing

### Tests Fail with Import Errors

**Symptom:** `pytest tests/` fails with `ModuleNotFoundError`.

**Solutions:**
- Ensure virtual environment is activated
- Install dev dependencies: `pip install -r requirements-dev.txt`
- For frontend: `npm ci`

### Frontend Tests Fail in CI

**Symptom:** Tests pass locally but fail in GitHub Actions.

**Solutions:**
- Check Node.js version matches (20.x)
- Ensure `package-lock.json` is up to date
- Increase Node memory: `NODE_OPTIONS=--max-old-space-size=4096`

### Test Coverage Below Threshold

**Symptom:** CI fails with coverage below threshold.

**Solutions:**
```bash
# Backend
cd backend && pytest --cov --cov-report=term-missing

# Chatbot
cd chatbot_service && pytest --cov --cov-report=term-missing

# Frontend
cd frontend && npx jest --coverage
```
Add tests for uncovered lines identified in the report.

---

## Email Alerts

### Alert Emails Not Sending

**Symptom:** `core/alert.py` reports success but no email received.

**Solutions:**
- Check `ALERT_EMAIL` and `ALERT_EMAIL_PASSWORD` env vars are set
- Check spam folder
- Verify SMTP server configuration in `alert.py`

---

## Getting Help

If the above doesn't solve your issue:
- Search [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues)
- Ask in [GitHub Discussions](https://github.com/SafeVixAI/SafeVixAI/discussions)
- See [SUPPORT.md](../../SUPPORT.md) for all support channels

## Related

- [RUNBOOKS.md](RUNBOOKS.md) — Incident response runbooks
- [OBSERVABILITY.md](OBSERVABILITY.md) — Logging, metrics, traces, alerting
- [SUPPORT.md](../../SUPPORT.md) — Support channels and response times
- [FAQ.md](../product-and-planning/FAQ.md) — Frequently asked questions
