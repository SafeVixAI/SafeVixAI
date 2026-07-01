# SafeVixAI v2.0 — Deployment Guide

## Infrastructure Overview (All Free Tier)

| Service | Provider | URL | Purpose |
|---|---|---|---|
| Frontend | Vercel | `safevixai.vercel.app` | Next.js 15 PWA, global CDN |
| Backend | Render.com | `safevixai-api.onrender.com` | FastAPI :8000, 750h/month free |
| Chatbot Service | Render.com | `safevixai-chatbot.onrender.com` | FastAPI :8010, Agentic RAG AI |
| Database | Supabase | `[project].supabase.co` | PostgreSQL + PostGIS |
| Cache | Upstash | `[host].upstash.io` | Redis, 10K commands/day |
| LLM APIs | 9-provider fallback chain (Groq, Cerebras, Gemini, GitHub Models, NVIDIA NIM, OpenRouter, Mistral, Together, Template) | Various | Auto-fallback on rate limit / failure |
| Model CDN | Hugging Face | `huggingface.co` | WebLLM weights |
| CI/CD | GitHub Actions (19 workflows) | | Auto-deploy on push |

---

## Step 1: Create Free Accounts

1. **Groq** — [console.groq.com](https://console.groq.com) → Create account → API Keys → Create Key (starts with `gsk_`)
2. **Supabase** — [supabase.com](https://supabase.com) → New project → Region: Singapore (closest to India) → Save password
3. **Upstash** — [upstash.com](https://upstash.com) → New Redis Database → Global → Copy `REDIS_URL`
4. **Vercel** — [vercel.com](https://vercel.com) → Connect GitHub account
5. **Render.com** — [render.com](https://render.com) → Connect GitHub account
6. **data.gov.in** — [data.gov.in](https://data.gov.in) → Register → Get API key (for NHAI data)

---

## Step 2: Database Setup (Supabase)

### Enable PostGIS (Run in Supabase SQL Editor)

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SELECT PostGIS_version(); -- verify: should return version string
```

### Get Connection String
Supabase → Settings → Database → Connection string → URI

Change `postgresql://` to `postgresql+asyncpg://` for async driver.

---

## Step 3: Backend Setup (Local Dev)

```bash
# 1. Navigate to backend directory
cd SafeVixAI/backend

# 2. Create and activate Python virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env
# Edit .env and fill in all values from Step 1-2

# 5. Run database migrations (creates all 6 tables)
alembic upgrade head

# 6. Verify tables were created
# Check Supabase Table Editor — should see 6 tables
```

### Download Required PDFs (for RAG)

```
Download to chatbot_service/data/legal/:
- motor_vehicles_act_1988.pdf     indiacode.nic.in
- mv_amendment_act_2019.pdf       morth.nic.in

Medical PDFs (who_trauma_care_guidelines.pdf, etc.):
Place in chatbot_service/data/medical/ (create dir if absent)
```

### Seed the Database

```bash
# Seed traffic violations and state overrides (~2 seconds)
python backend/scripts/data/seed_violations.py

# Seed emergency services for 25 Indian cities (~4 minutes via Overpass API)
# Also creates: frontend/public/offline-data/india-emergency.geojson
python backend/scripts/app/seed_emergency.py

# Build ChromaDB vector store from PDFs — RUN ONCE, takes 5-10 minutes
# Creates: chatbot_service/data/chroma_db/ directory (committed to git)
python chatbot_service/data/build_vectorstore.py
```

### Start Backend Dev Server

```bash
uvicorn main:app --reload --port 8000

# Verify at: http://localhost:8000/health
# Swagger docs: http://localhost:8000/docs
```

---

## Step 4: Frontend Setup (Local Dev)

```bash
# 1. Navigate to frontend directory
cd SafeVixAI/frontend

# 2. Install all npm packages
npm install

# 3. Copy environment template
cp .env.local.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# 4. Start development server
npm run dev
# Opens at: http://localhost:3000
```

### Standalone Production Build

```bash
# npm run build runs: next build && node scripts/copy-public.js
# copy-public.js removes stale .next/standalone/public/ and
# .next/standalone/.next/static/ directories, then re-copies
# all public assets and static chunks so the standalone server
# never serves 404s on JS/CSS/public files.
npm run build
```

### E2E Test Auth Bypass

When running Playwright E2E tests, set the following localStorage flag before navigating to any guarded route:

```js
await page.addInitScript(() => {
  localStorage.setItem('__E2E_SKIP_AUTH__', 'true');
});
```

This bypasses AuthGuard at the component level, preventing redirect loops while allowing tests to interact with authenticated pages. The backend still requires valid JWTs for API calls.

### Test Offline Mode (PWA)

```bash
# Note: Service Worker only registers in production build

# Build and start production server locally
npm run build && npm start

# Then in Chrome:
# 1. DevTools → Application → Service Workers — verify registered
# 2. DevTools → Network — check "Offline"
# 3. Navigate to /emergency — hospitals should still show
```

---

## Step 5: Deploy Backend to Render.com

### Via render.yaml (Recommended)

The `render.yaml` at the project root configures automatic deployment.

1. Go to Render.com → New → Blueprint
2. Connect GitHub repository
3. Render detects `render.yaml` automatically
4. Set environment variables (from Render dashboard):
   - `DATABASE_URL`
   - `REDIS_URL`
   - `GROQ_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `CORS_ORIGINS` (set to your Vercel frontend URL)
   - `CHATBOT_SERVICE_URL` (set to your chatbot Render URL)
   - `ADMIN_SECRET` (generate a random 32-char string)
   - `LOCAL_UPLOAD_BASE_URL` (your backend URL + `/uploads`)
   - `OPENROUTESERVICE_API_KEY` (optional, for routing)
   - `OPENWEATHER_API_KEY` (optional, for weather)

### Manual Setup (Alternative)

Render.com → New → Web Service:
- **Name:** `safevixai-api`
- **Root Directory:** `backend`
- **Runtime:** Python 3.11
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`
- **Health Check Path:** `/health`

### Run Migrations on Render

After first deploy, open Render Shell:
```bash
alembic upgrade head
python backend/scripts/data/seed_violations.py
python backend/scripts/app/seed_emergency.py  # 4 minutes
python chatbot_service/data/build_vectorstore.py  # 10 minutes
```

---

## Step 5b: Deploy Chatbot Service to Render.com

The chatbot service is a **separate** Render web service.

Render.com → New → Web Service:
- **Name:** `safevixai-chatbot`
- **Root Directory:** `chatbot_service`
- **Runtime:** Python 3.11
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`
- **Health Check Path:** `/health`

Set environment variables:
- `DEFAULT_LLM_PROVIDER`, `DEFAULT_LLM_MODEL`
- All LLM provider API keys (GROQ, GEMINI, SARVAM, CEREBRAS, OPENROUTER, MISTRAL, TOGETHER, NVIDIA_NIM, GITHUB_TOKEN)
- `MAIN_BACKEND_BASE_URL` = your Render backend URL
- `REDIS_URL` = Upstash Redis URL
- `CHROMA_PERSIST_DIR` = `./data/chroma_db`
- `CORS_ORIGINS` = your Vercel frontend URL
- `ADMIN_SECRET` = same as backend or generate separate
- `W3W_API_KEY` = What3Words API key (for SOS geolocation)
- `OPENCAGE_API_KEY` = OpenCage geocoding key (fallback)
- `OPENWEATHER_API_KEY` = OpenWeather key (for weather tool)
- `HF_TOKEN` = HuggingFace token (for Sarvam HF fallback)

> **Note:** `chatbot_service/data/chroma_db/` is committed to git, so Render gets the vectorstore automatically on deploy. No build-time vectorstore creation needed.

---

## Step 6: Deploy Frontend to Vercel

### Via GitHub Actions (Automated CI/CD Pipeline)

The repository is configured with a fully automated CI/CD pipeline. The frontend is automatically deployed to Vercel when changes are pushed to the `main` branch, *only* if the E2E and unit test suites pass successfully.

1. Add the following secrets to your GitHub repository (`Settings` → `Secrets and variables` → `Actions`):
   - `VERCEL_TOKEN`: Generate this at [vercel.com/account/tokens](https://vercel.com/account/tokens)
   - `VERCEL_ORG_ID`: Found in your Vercel project settings or `.vercel/project.json` after linking locally.
   - `VERCEL_PROJECT_ID`: Found in your Vercel project settings or `.vercel/project.json`.

2. The `.github/workflows/e2e.yml` workflow will automatically trigger on pushes to `main`. It will:
   - Run Jest unit tests
   - Run Playwright E2E tests against a production build
   - If (and only if) all tests pass, deploy the application to Vercel production

### Via CLI (Manual/Local Testing)

```bash
cd frontend
# Link the project to Vercel (required first time)
npx vercel link

# Deploy to production
npx vercel --prod
```

---

## Step 7: Verify Production Deployment

```bash
# Backend health check
curl https://safevixai-api.onrender.com/health
# Expected: {"status":"ok","chatbot_ready":true}

# Emergency API test
curl "https://safevixai-api.onrender.com/api/v1/emergency/nearby?lat=13.0827&lon=80.2707"
# Expected: {"services":[...],"count":N}

# Challan API test
curl "https://safevixai-api.onrender.com/api/v1/challan/calculate?violation_code=MVA_185"
# Expected: {"final_fine_inr":10000,"section":"185"}

# Frontend PWA check
# Chrome → visit safevixai.vercel.app → check "Add to Home Screen" prompt
```

---

## CI/CD (GitHub Actions)

Configured in `.github/workflows/` — 19 workflow files:

| Workflow | Trigger | Purpose |
|---|---|---|
| `backend.yml` | `backend/**` changes | `pytest tests/ -v` with Python 3.11 |
| `chatbot.yml` | `chatbot_service/**` changes | `pytest tests/ -v` with Python 3.11 |
| `frontend.yml` | `frontend/**` changes | `pnpm run lint` + `npx tsc --noEmit` with Node 20 |
| `e2e.yml` | Push to `main`, PR | Full-stack Playwright E2E tests + Vercel deploy |
| `security.yml` | Push, PR | Dependency auditing + security scanning |
| `system.yml` | Push to `main` | Cross-service system validation |
| `docker-build.yml` | Push, PR | Docker Compose build verification |
| `smoke-tests.yml` | Push to `main` | API smoke tests after deploy |
| `load-testing.yml` | Scheduled | Load/performance testing |
| `contract-tests.yml` | PR to `main` | Provider-driven contract tests |
| `chaos-tests.yml` | Scheduled | Chaos engineering resilience tests |
| `i18n-cron.yml` | Scheduled (daily) | i18n translation sync |
| `db-backup.yml` | Scheduled (daily) | Supabase database backup |
| `blue-green-deploy.yml` | Push to `main` | Zero-downtime frontend deploy |
| `branch-protection.yml` | PR | Branch protection policy checks |
| `codacy.yml` | PR | Codacy code quality analysis |
| `sync-wiki.yml` | `backend/**`, `chatbot_service/**` | LLM wiki generation |
| `update-master-doc.yml` | `docs/**`, root `.md` changes | Auto-generate DOCX master document |
| `deploy-docs.yml` | `docs/**` changes | Deploy documentation site |

---

## Environment Variables Reference

### Backend (`backend/.env`)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# Cache
REDIS_URL=rediss://default:[TOKEN]@[HOST].upstash.io:6379

# Chatbot
CHATBOT_SERVICE_URL=http://localhost:8010

# App
ENVIRONMENT=production
DEFAULT_RADIUS=5000
MAX_RADIUS=50000
CACHE_TTL=3600
```

### Chatbot Service (`chatbot_service/.env`)

```bash
# LLM
DEFAULT_LLM_PROVIDER=groq
DEFAULT_LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=gsk_...
CEREBRAS_API_KEY=...
GEMINI_API_KEY=...
SARVAM_API_KEY=...
GITHUB_TOKEN=ghp_...           # For GitHub Models provider
NVIDIA_NIM_API_KEY=...
OPENROUTER_API_KEY=...
MISTRAL_API_KEY=...
TOGETHER_API_KEY=...

# Backend connection
MAIN_BACKEND_BASE_URL=http://localhost:8000

# RAG
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=LocalHashEmbeddingFunction (zero-dependency)  # Config hint — runtime uses LocalHashEmbeddingFunction

# Cache
REDIS_URL=rediss://default:[TOKEN]@[HOST].upstash.io:6379
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_BACKEND_URL=https://safevixai-api.onrender.com
NEXT_PUBLIC_CHATBOT_URL=https://safevixai-chatbot.onrender.com
```

---

## Speech Translation Endpoints

Available in the chatbot service (no API key required beyond CORS):

| Method | Endpoint | Rate Limit | Description |
|--------|----------|------------|-------------|
| `POST` | `/speech/translate` | 20/min | Upload audio, returns translated text + language detection |
| `GET` | `/speech/status` | 30/min | Service status, supported languages, model health |

Audio formats: WAV, MP3, OGG, WebM, FLAC. Max upload: 10 MB.
Backed by IndicSeamlessService (SeamlessM4T for ASR + translation).

---

## Rate Limiting

| Category | Limit | Implementation |
|----------|-------|----------------|
| General | 100 requests/min | slowapi with Redis backend (in-memory fallback) |
| Auth | 5 requests/min | Login/signup/password-reset endpoints |
| SOS / Emergency | 3 requests/min | SOS activation and emergency reports |
| Challan | 60 requests/min | Fine calculation queries |
| Chat | 30 requests/min | Chat and streaming endpoints |
| Geocoding | 30 requests/min | Reverse and forward geocoding |

---

## Static Analysis Stats (v2.0)

| Metric | Count |
|--------|-------|
| Backend Python Tests | 1365 |
| Chatbot Python Tests | 892 |
| Frontend Jest Tests | 572 |
| **Total Unit Tests** | **2829** |
| Frontend Components | 91 |
| Frontend Routes | 28 |
| API Route Modules | 27 |
| CI/CD Workflows | 19 |

---

## Render.com Free Tier Limitations

- **512MB RAM** — sufficient for FastAPI + ChromaDB reads (build vectorstore before deploy)
- **750 hrs/month** — one service runs 24/7 for a month
- **Cold starts** — first request after inactivity takes ~30s (free tier sleeps after 15min)
  - Mitigation: Set up a `/health` ping every 14 minutes via UptimeRobot (free)

---

## Daily Development Commands

```bash
# Backend (in backend/ with venv active)
uvicorn main:app --reload --port 8000

# Frontend (in frontend/)
npm run dev

# Run all backend tests
cd backend && pytest tests/ -v

# Run specific test
pytest tests/test_challan.py::test_drunk_driving_first_offence -v

# Create new DB migration after model changes
alembic revision --autogenerate -m "add_crash_events_table"
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Rebuild ChromaDB (after adding PDFs)
python chatbot_service/data/build_vectorstore.py

# Test API manually
curl "http://localhost:8000/api/v1/emergency/nearby?lat=13.0827&lon=80.2707"
curl "http://localhost:8000/api/v1/challan/calculate?violation_code=MVA_185"
```

---

## Free Tier Cold Start Mitigation

Render free web services spin down after **15 minutes of inactivity** and take **30–60 seconds** to cold start. The app mitigates this with three layers:

### 1. cron-job.org (Automatic Keep-Alive)

Set up two free cron jobs at [cron-job.org](https://cron-job.org) (no signup cost):

| Job | URL to Ping | Interval |
|-----|-------------|----------|
| Backend | `https://safevixai-api.onrender.com/health` | Every 10 minutes |
| Chatbot | `https://safevixai-chatbot.onrender.com/health` | Every 10 minutes |

1. Create account at cron-job.org
2. Add new cron job → URL, 10-minute interval, GET request
3. Disable "Save Responses" to save their resources
4. Both jobs stay free forever (10 min interval = 6 jobs/day × 30 days = 180 requests/month ≈ free)

### 2. Client-Side Warm-Up (Automatic)

The frontend automatically pings both `/health` endpoints:

- **On page load** — immediately sends warm-up pings
- **Every 9 minutes** — interval timer keeps instances awake
- **On tab focus** — re-warms when user returns after idle
- **Emergency page** — pre-warms before user needs to act

This runs in `EnterpriseClientAppHooks.tsx` (keep-alive pings) and `app/emergency/page.tsx` (emergency pre-warm).

### 3. Server Warming Banner (Visual Feedback)

When a request takes >5 seconds (cold start signal), a "Connecting..." banner appears at the bottom of the screen. Controlled by `components/ui/ServerWarmingBanner.tsx` + warming interceptors in `lib/api.ts`.

### Expected Cold Start Behavior

| Scenario | Delay | User Sees |
|----------|-------|-----------|
| First visit (or after >15 min idle) | 30–60s warming + page load | "Connecting..." banner, then normal page |
| Active user (returning within 15 min) | ~1–2s | No delay, instant response |
| cron-job.org ping arrives | 30–60s warming (server wakes up) | No user impact (next user request is fast) |
| Emergency page visited | Immediate pre-warm ping | Minimal delay on SOS actions |

> **Note:** On free tier, the combined idle+startup time per month is ~750 hours per service. With 10-min keep-alive, expect ~744 hours/month uptime (99.9%).

---

*Document version: 2.0 | IIT Madras Road Safety Hackathon 2026 | Updated: June 2026*
