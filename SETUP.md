# SafeVixAI — Setup & Installation Guide

Complete guide to install dependencies and run both backend and frontend locally.

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
# Go to your workspace folder
cd C:\Projects\SafeVixAI        # Windows
# cd ~/projects                 # Linux/Mac

# Clone the repository
git clone https://github.com/SafeVixAI/SafeVixAI.git

# Enter the project folder
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
# In chatbot_service/.env — add these for failure notifications:
ALERT_EMAIL=your-gmail@gmail.com
ALERT_EMAIL_PASSWORD=abcd efgh ijkl mnop   # Gmail App Password, NOT your regular password
ALERT_EMAIL_TO=team-lead@gmail.com         # Recipient (defaults to ALERT_EMAIL)
```
> **Get a Gmail App Password:** Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) → Select "Mail" → "Other" → Name it "SafeVixAI" → Copy the 16-char code.

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

> First install takes 2–4 minutes.

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
# DevTools → Application → Service Workers → verify "Activated"
# DevTools → Network → check "Offline"
# Navigate to /emergency → protocols should still load from cache
```

---

# Daily Quick-Start

Once installed, you only need:

```bash
# Terminal 1: Backend
cd SafeVixAI/backend
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # Linux/Mac
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
# Run server
uvicorn main:app --reload --port 8000

# Testing
pytest tests/ -q                                         # Run all tests (quiet mode)
pytest tests/test_challan.py -q                          # Run one test file
pytest tests/test_challan.py::test_drunk_driving_fine -v # Run single test (verbose)

# Test API endpoints
curl "http://localhost:8000/api/v1/emergency/nearby?lat=13.0827&lon=80.2707"
curl "http://localhost:8000/api/v1/challan/calculate?violation_code=MVA_185"
curl "http://localhost:8000/health"

# Virtual environment
.venv\Scripts\activate                                   # Activate (Windows)
source .venv/bin/activate                                # Activate (Linux/Mac)
deactivate                                               # Deactivate
```

## Chatbot Service Commands

```bash
# Run server
uvicorn main:app --reload --port 8010

# Testing
pytest tests/ -q                                         # Run all tests (quiet mode)
pytest tests/test_safety_checker.py -q                   # Run one test file

# Test API endpoints
curl "http://localhost:8010/health"
curl "http://localhost:8010/api/v1/chat/" -X POST -H "Content-Type: application/json" -d '{"message":"Hello"}'
```

## Frontend Commands

```bash
# Development
npm run dev                                              # Start dev server (hot reload)
npm run build                                            # Build for production
npm start                                                # Run production build

# Code quality
npm run lint                                             # Run ESLint

# Testing
npm test                                                 # Run tests (572 total)

# Packages
npm install                                              # Install all dependencies
npm install [package-name]                               # Add a new package
npm uninstall [package-name]                             # Remove a package
```

## E2E Testing

```bash
# From frontend/ directory
npx playwright test e2e/                                 # Run all E2E tests
npx playwright test e2e/ --grep-invert="Visual"          # Run excluding visual tests
npx playwright show-report                               # View last test report
```

---

# Troubleshooting

### `ModuleNotFoundError` in backend
```bash
# Make sure .venv is activated — check for (.venv) in terminal
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Map not displaying in browser
- MapLibre components must be loaded with `dynamic(() => import(...), { ssr: false })`
- Check that `maplibre-gl/dist/maplibre-gl.css` is imported in `layout.tsx`

### `GROQ_API_KEY` missing error
- Create a free account at [console.groq.com](https://console.groq.com)
- Go to API Keys → Create Key
- Copy the `gsk_...` key into `backend/.env`

### Port already in use
```bash
# Windows — find and kill the process
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F

# Run on a different port
npm run dev -- -p 3001
```

---

*For full deployment to Vercel + Render.com, see [`docs/Deployment.md`](docs/Deployment.md)*
*For the complete app overview, see [`docs/Agent.md`](docs/Agent.md)*

## Related

- [TESTING.md](TESTING.md) — Testing standards and coverage
- [OPERATIONS.md](OPERATIONS.md) — Day-to-day operations and scaling
- [docs/MONITORING_SETUP.md](docs/MONITORING_SETUP.md) — Prometheus/Grafana/Loki setup
