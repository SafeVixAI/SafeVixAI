# SafeVixAI — Setup & Installation Guide

Complete guide to install dependencies and run both backend and frontend locally.

## Architecture Overview

```mermaid
flowchart LR
    subgraph DevEnv[" Development Environment "]
        T1["Terminal 1<br/>Backend :8000"]
        T2["Terminal 2<br/>Chatbot :8010"]
        T3["Terminal 3<br/>Frontend :3000"]
    end

    subgraph Code[" Source Code "]
        BE_REPO["backend/<br/>FastAPI + SQLAlchemy"]
        CB_REPO["chatbot_service/<br/>FastAPI + ChromaDB"]
        FE_REPO["frontend/<br/>Next.js 15 + React 19"]
    end

    subgraph Data[" Data Layer "]
        PG["PostgreSQL 16 + PostGIS<br/>Supabase / Local"]
        RD["Redis 7<br/>Upstash / Local"]
    end

    T1 --> BE_REPO
    T2 --> CB_REPO
    T3 --> FE_REPO

    BE_REPO --> PG
    BE_REPO --> RD
    CB_REPO --> RD
    FE_REPO -->|"REST/WS"| BE_REPO
    FE_REPO -->|REST| CB_REPO


    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b
    classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#7c2d12
    classDef neutral fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b

    class DevEnv neutral
    class T1 control
    class T2 ai
    class T3 edge
    class Code neutral
    class BE_REPO data
    class CB_REPO data
    class FE_REPO edge
    class Data neutral
    class PG data
    class RD data```

## Setup Workflow

```mermaid
flowchart TD
    START[Start] --> CLONE[git clone]
    CLONE --> VERIFY{"Node >= 20<br/>Python >= 3.11"}

    VERIFY -->|No| INSTALL_PRE[Install Prerequisites]
    INSTALL_PRE --> VERIFY

    VERIFY -->|Yes| BE_SETUP[Backend Setup]
    BE_SETUP --> BE_VENV["Create .venv<br/>python -m venv .venv"]
    BE_VENV --> BE_ACTIVATE[Activate venv]
    BE_ACTIVATE --> BE_PIP["pip install -r requirements.txt"]
    BE_PIP --> BE_ENV["cp .env.example .env<br/>Configure API keys"]
    BE_ENV --> BE_DB["Run migrations<br/>alembic upgrade head"]
    BE_DB --> BE_RUN["uvicorn main:app<br/>--reload --port 8000"]

    VERIFY --> CB_SETUP[Chatbot Setup]
    CB_SETUP --> CB_VENV["Create .venv<br/>python -m venv .venv"]
    CB_VENV --> CB_ACTIVATE[Activate venv]
    CB_ACTIVATE --> CB_PIP["pip install -r requirements.txt"]
    CB_PIP --> CB_ENV["cp .env.example .env<br/>Configure LLM keys"]
    CB_ENV --> CB_RUN["uvicorn main:app<br/>--reload --port 8010"]

    VERIFY --> FE_SETUP[Frontend Setup]
    FE_SETUP --> FE_NPM[npm ci]
    FE_NPM --> FE_ENV["cp .env.example .env"]
    FE_ENV --> FE_RUN[npm run dev]

    BE_RUN --> DONE[All 3 services running]
    CB_RUN --> DONE
    FE_RUN --> DONE

    DONE --> VERIFY_HEALTH["Verify localhost:8000/health<br/>localhost:8010/health<br/>localhost:3000"]


    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b
    classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#7c2d12
    classDef neutral fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b

    class START neutral
    class CLONE neutral
    class VERIFY neutral
    class INSTALL_PRE edge
    class BE_SETUP control
    class BE_VENV action
    class BE_ACTIVATE neutral
    class BE_PIP edge
    class BE_ENV edge
    class BE_DB neutral
    class BE_RUN ai
    class CB_SETUP ai
    class CB_VENV action
    class CB_ACTIVATE neutral
    class CB_PIP edge
    class CB_ENV ai
    class CB_RUN ai
    class FE_SETUP edge
    class FE_NPM neutral
    class FE_ENV neutral
    class FE_RUN neutral
    class DONE control
    class VERIFY_HEALTH neutral```

## Estimated Setup Times

```mermaid
gantt
    title SafeVixAI Estimated Setup Timeline
    dateFormat  HH:mm
    axisFormat  %M min

    section Prerequisites
    Git Clone                 :00:00, 00:02
    Check Versions            :00:02, 00:03

    section Backend
    Create Virtual Env        :00:03, 00:05
    pip install dependencies  :00:05, 00:15
    Configure env             :00:15, 00:18
    Database Migrations       :00:18, 00:21

    section Chatbot Service
    Create Chatbot venv       :00:03, 00:05
    pip install ML libs       :00:05, 00:20
    Configure Chatbot env     :00:20, 00:23

    section Frontend
    npm ci dependencies       :00:03, 00:08
    Configure Frontend env    :00:08, 00:10

    section Verification
    Run all 3 services        :00:25, 00:28
    Smoke tests               :00:28, 00:30
```

---

## Prerequisites

| Tool    | Version | Check              | Download                             |
|---------|---------|--------------------|--------------------------------------|
| Python  | 3.11+   | `python --version` | [python.org](https://python.org)     |
| pip     | latest  | `pip --version`    | bundled with Python                  |
| Node.js | 20+     | `node --version`   | [nodejs.org](https://nodejs.org)     |
| npm     | 9+      | `npm --version`    | bundled with Node.js                 |
| Git     | any     | `git --version`    | [git-scm.com](https://git-scm.com)  |

---

## Step 1 — Clone the Repository

```bash
cd C:\Projects\SafeVixAI        # Windows
# cd ~/projects                 # Linux/Mac
git clone https://github.com/SafeVixAI/SafeVixAI.git
cd SafeVixAI
```

After cloning, verify the structure:
```bash
ls -la
# You should see: backend/, chatbot_service/, frontend/, docs/, README.md, SETUP.md
```

---

# BACKEND SETUP

---

## Step 2 — Create a Python Virtual Environment

```bash
cd backend
python -m venv .venv
```

### Activate the Virtual Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` at the start of your terminal line.

---

## Step 3 — Install Backend Dependencies

```bash
pip install -r requirements.txt
```

**Key packages installed:**
- **FastAPI + Uvicorn** — web framework and server
- **LangChain + Groq** — AI chatbot pipeline
- **ChromaDB** — vector store for RAG
- **SQLAlchemy + asyncpg** — async database ORM
- **GeoAlchemy2** — PostGIS geometry support
- **hash-based embeddings** - embeddings config (runtime uses hash-based `LocalHashEmbeddingFunction`)
- **DuckDB** — SQL engine for offline challan calculator
- **Redis (hiredis)** — cache client
- **httpx** — async HTTP for Overpass/Nominatim
- **Pydantic** — request/response validation

> First install takes 3-5 minutes (torch/torchaudio are large).

Verify:
```bash
python -c "import fastapi, langchain, chromadb; print('All packages OK')"
```

---

## Step 4 — Configure Environment Variables

```bash
cp .env.example .env
```

Edit `backend/.env` and fill in all required values (GROQ_API_KEY, database URLs, etc.).

---

## Step 5 — Run the Backend

```bash
uvicorn main:app --reload --port 8000
```

**Verify:**
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- Swagger API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

# CHATBOT SERVICE SETUP

---

## Step 5.1 — Create a Python Virtual Environment for Chatbot

```bash
cd chatbot_service
python -m venv .venv
```

### Activate the Virtual Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

---

## Step 5.2 — Install dependencies & Configure

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `chatbot_service/.env` with your API keys (Gemini, Groq, etc.).

**Optional but recommended — Email alerts for production failures:**
```bash
ALERT_EMAIL=your-gmail@gmail.com
ALERT_EMAIL_PASSWORD=abcd efgh ijkl mnop   # Gmail App Password, NOT your regular password
ALERT_EMAIL_TO=team-lead@gmail.com
```
> **Get a Gmail App Password:** Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) to Mail to Other to Name it "SafeVixAI" to Copy the 16-char code.

---

## Step 5.3 — Run the Chatbot Service

```bash
uvicorn main:app --reload --port 8010
```

**Verify:**
- Health check: [http://localhost:8010/health](http://localhost:8010/health)
- Swagger API docs: [http://localhost:8010/docs](http://localhost:8010/docs)

---

# FRONTEND SETUP

---

## Step 6 — Install Frontend Dependencies

Open a **new terminal** (keep backend running):

```bash
cd frontend
npm install
```

**Key packages installed:**
- **Next.js 15** — React framework with App Router
- **React 19** — UI library
- **TypeScript 5** — type-safe JavaScript
- **Tailwind CSS 3** — utility-first CSS
- **MapLibre GL** — vector map rendering
- **GSAP** — animations (Framer Motion removed; GSAP used via `useGSAP` hook)
- **zustand** — global state management
- **lucide-react** — icon library
- **@mlc-ai/web-llm** — offline AI (browser-based LLM)
- **@turf/turf** — geospatial analysis utilities

> First install takes 2-4 minutes.

Verify:
```bash
npx next --version
# Should print: 15.x.x
```

---

## Step 7 — Configure Frontend Environment

```bash
cp .env.example .env
```

Edit `frontend/.env` and set:
- `NEXT_PUBLIC_BACKEND_URL` — backend API URL (default: `http://localhost:8000`)
- `NEXT_PUBLIC_CHATBOT_URL` — chatbot service URL (default: `http://localhost:8010`)
- Any map tile API keys if using premium tiles

---

## Step 8 — Run the Frontend

```bash
npm run dev
```

App opens at: [http://localhost:3000](http://localhost:3000)

You should see the SafeVixAI tactical dashboard with the map, search bar, and bottom navigation.

---

## Step 9 — Test Offline / PWA Mode

> **Note:** Service Worker only activates in production builds.

```bash
npm run build
npm start

# Visit http://localhost:3000 in Chrome
# DevTools to Application to Service Workers to verify "Activated"
# DevTools to Network to check "Offline"
# Navigate to /emergency to protocols should still load from cache
```

---

# Daily Quick-Start

Once installed, you only need:

```bash
# Terminal 1: Backend
cd SafeVixAI/backend
.venv\Scripts\activate         # Windows
uvicorn main:app --reload --port 8000

# Terminal 2: Chatbot Service
cd SafeVixAI/chatbot_service
.venv\Scripts\activate         # Windows
uvicorn main:app --reload --port 8010

# Terminal 3: Frontend
cd SafeVixAI/frontend
npm run dev

# All running:
# Backend:  http://localhost:8000
# Chatbot:  http://localhost:8010
# API Docs: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

---

# All Useful Commands

## Backend Commands

```bash
uvicorn main:app --reload --port 8000
pytest tests/ -q
pytest tests/test_challan.py -q
pytest tests/test_challan.py::test_drunk_driving_fine -v
curl "http://localhost:8000/api/v1/emergency/nearby?lat=13.0827&lon=80.2707"
curl "http://localhost:8000/api/v1/challan/calculate?violation_code=MVA_185"
curl "http://localhost:8000/health"
.venv\Scripts\activate
deactivate
```

## Chatbot Service Commands

```bash
uvicorn main:app --reload --port 8010
pytest tests/ -q
pytest tests/test_safety_checker.py -q
curl "http://localhost:8010/health"
curl "http://localhost:8010/api/v1/chat/" -X POST -H "Content-Type: application/json" -d '{"message":"Hello"}'
```

## Frontend Commands

```bash
npm run dev
npm run build
npm start
npm run lint
npm test
npm install
npm install [package-name]
npm uninstall [package-name]
```

## E2E Testing

```bash
# From frontend/ directory
npx playwright test e2e/
npx playwright test e2e/ --grep-invert="Visual"
npx playwright show-report
```

---

# Troubleshooting

### `ModuleNotFoundError` in backend
```bash
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Map not displaying in browser
- MapLibre components must be loaded with `dynamic(() => import(...), { ssr: false })`
- Check that `maplibre-gl/dist/maplibre-gl.css` is imported in `layout.tsx`

### `GROQ_API_KEY` missing error
- Create a free account at [console.groq.com](https://console.groq.com)
- Go to API Keys to Create Key
- Copy the `gsk_...` key into `backend/.env`

### Port already in use
```bash
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F
npm run dev -- -p 3001
```

---

*For full deployment to Vercel + Render.com, see [`docs/Deployment.md`](chatbot/deployment.md)*
*For the complete app overview, see [`docs/Agent.md`](Agent.md)*

## Related

- [TESTING.md](TESTING.md) — Testing standards and coverage
- [OPERATIONS.md](../sre/OPERATIONS.md) — Day-to-day operations and scaling
- [docs/MONITORING_SETUP.md](../sre/observability/MONITORING_SETUP.md) — Prometheus/Grafana/Loki setup
