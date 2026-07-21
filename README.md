# SafeVixAI

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="CODE_OF_CONDUCT.md"><img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg" alt="Code of Conduct" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/issues"><img src="https://img.shields.io/github/issues/SafeVixAI/SafeVixAI" alt="Issues" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/stargazers"><img src="https://img.shields.io/github/stars/SafeVixAI/SafeVixAI" alt="Stars" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/releases"><img src="https://img.shields.io/github/v/release/SafeVixAI/SafeVixAI" alt="Release" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/actions/workflows/backend.yml"><img src="https://img.shields.io/github/actions/workflow/status/SafeVixAI/SafeVixAI/backend.yml?label=tests" alt="Tests" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/security"><img src="https://img.shields.io/badge/SBOM-available-brightgreen" alt="SBOM" /></a>
  <a href="ROADMAP.md"><img src="https://img.shields.io/badge/roadmap-available-brightgreen" alt="Roadmap" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/SafeVixAI/SafeVixAI"><img src="https://img.shields.io/badge/Scorecard-Passing-brightgreen" alt="OpenSSF Scorecard" /></a>
  <a href="https://github.com/SafeVixAI/SafeVixAI/actions/workflows/codeql.yml"><img src="https://img.shields.io/badge/CodeQL-Analysis-blue" alt="CodeQL" /></a>
</p>

**AI Emergency Response + DriveLegal + RoadWatch — Three Problem Statements, One App**

> IIT Madras Road Safety Hackathon 2026 | Team Submission
> Total infrastructure cost: Rs. 0 — 100% free and open source

| Metric | Value |
|--------|-------|
| Features | **25/25 COMPLETE** |
| Unit Tests | **7,160+ passing** — Frontend 2,956 / Backend 2,750 / Chatbot 1,613 |
| E2E Tests | 55/55 passing |
| LLM Providers | 9-provider fallback chain |
| Services | 3 (frontend :3000, backend :8000, chatbot :8010) |
| Coverage | Frontend 86% lines / 72% branches / 81% functions |
| CI Workflows | 40 (security, load, chaos, E2E, migration, benchmark, more) |

---

## What SafeVixAI Does

| Module | What it does | Works Offline? |
|---|---|---|
| Emergency Locator | Find nearest hospital/police/ambulance using GPS | Yes — 25 Indian cities |
| AI Chatbot | Answer traffic law + first aid questions | Yes — Phi-3 Mini in browser |
| Challan Calculator | Exact MVA 2019 fines with state overrides | Yes — DuckDB-Wasm |
| Road Reporter | Report potholes, auto-routes to NHAI/PWD/PMGSY | Yes — offline queue |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
cp .env.example .env            # Fill in your keys
uvicorn main:app --reload --port 8000
```

Verify: http://localhost:8000/health

### Chatbot Service

```bash
cd chatbot_service
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
cp .env.example .env            # Fill in your LLM keys
uvicorn main:app --reload --port 8010
```

Verify: http://localhost:8010/health

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # Fill in your keys
npm run dev
```

Verify: http://localhost:3000

---

## Project Structure

```
SafeVixAI/
├── backend/           FastAPI Python 3.11 + PostgreSQL/PostGIS (port 8000)
├── chatbot_service/   FastAPI Agentic RAG Chatbot + 9 LLM providers (port 8010)
├── frontend/          Next.js 15 + React 19 TypeScript PWA (port 3000)
├── docs/              Complete technical documentation
├── chatbot_docs/      Documentation specifically for Chatbot Service
├── scripts/           Global data pipeline scripts
│   ├── app/           DB-dependent scripts (seed_emergency, seed_nhp_hospitals)
│   └── data/          Pure Python scripts — no DB needed (fetchers, extractors)
└── .github/           GitHub Actions CI/CD
```

---

## Data Intelligence

The "Intelligence Layer" of SafeVixAI (3.3GB of pre-trained models, road damage datasets, and legal archives) is hosted on the **Hugging Face Dataset Hub** for high-performance delivery.

**[Explore the SafeVixAI Dataset Hub](https://huggingface.co/datasets/SafeVixAI/SafeVixAI-Dataset-Hub)**

### Research Notebooks — Open in Colab

> Run all notebooks through **Google Colab** for the easiest setup — free T4 GPU, no local install needed.

| # | Notebook | What It Produces | Open in Colab |
|---|---|---|---|
| 1 | **YOLOv8 Pothole Detector Training** | ONNX road damage model | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1oe4Gk899lFB_vbRMUuOh4dqpsa3bbycI) |
| 2 | **ChromaDB RAG Vectorstore Build** | ChromaDB index for legal RAG | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1AzPdN9xjcjW20ko0shTYn0mvbxTUw57Q) |
| 3 | **Accident EDA & Hotspot Generator** | Blackspot seed CSV + heatmap | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1xh_lwv_B_jc0_83dvuNppWQRtVhqExTS) |
| 4 | **Roads Data Processing** | Sampled PMGSY GeoJSON | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/10_WfTlbbxW9A7ceQBZGaKF5UkydlUDin#scrollTo=z4XxGZmx0ymX) |
| 5 | **Risk Model ONNX Training** | Risk scoring ONNX model | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/16IH-rn3CedYtfIpJP4iLa_KUjvfy8hAY) |

---

## Scripts Architecture

All script folders follow the same `app/` vs `data/` split:

| Folder | `app/` | `data/` |
|---|---|---|
| `scripts/` | 5 files (DB seeders) | 16 files (fetchers, extractors, verifiers) |
| `backend/scripts/` | 12 files (DB/Redis/PostGIS loaders) | 22 files (pure data transforms) |
| `chatbot_service/scripts/` | 2 files (DB wrapper) | 7 files (Pro Overpass fetchers) |

> **`data/`** scripts run standalone with no database. **`app/`** scripts require a live backend stack.

The `data/` scripts are also mirrored on the **[Hugging Face Dataset Hub](https://huggingface.co/datasets/SafeVixAI/SafeVixAI-Dataset-Hub)** so researchers can reproduce the dataset without cloning the full app.

Read `docs/NEW_CONTRIBUTOR_GUIDE.md` first (humans) or `docs/Agent.md` (AI agents) — each gives a complete overview tailored to the reader.

---

## Tech Stack

**Backend:** FastAPI, SQLAlchemy, PostGIS, Redis, DuckDB, Overpass/Nominatim

**Chatbot Service:** FastAPI, ChromaDB, LangChain, 9 LLM providers (Groq, Gemini, Sarvam AI, etc.), IndicSeamless Speech

**Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS, MapLibre GL, WebLLM, DuckDB-Wasm, Transformers.js

**Infra:** Vercel, Render.com, Supabase, Upstash, GitHub Actions — all free tier

---

## Security Hardening

| Layer | Protection | File |
|---|---|---|
| CORS | Fail-fast `RuntimeError` if wildcard `*` in production | `backend/core/config.py`, `chatbot_service/config.py` |
| Auth | JWT Bearer tokens + guest auth + service-to-service API key | `backend/api/v1/auth.py`, `frontend/lib/store.ts` |
| LLM Safety | 12-pattern prompt injection guard + SafetyChecker | `chatbot_service/providers/base.py`, `agent/safety_checker.py` |
| LLM Timeout | `asyncio.wait_for()` on every provider call | `chatbot_service/providers/router.py` |
| Error Boundary | Global React error boundary prevents white-screen crashes | `frontend/app/error.tsx` |
| Env Validation | Frontend throws at import if any `NEXT_PUBLIC_*` URL is missing | `frontend/lib/public-env.ts` |
| Theme | External script (no `dangerouslySetInnerHTML`) | `frontend/public/theme-init.js` |
| ALLOWED_HOSTS | Host header validation middleware | `backend/middleware/allowed_hosts.py` |

---

## Documentation

| File | Contents |
|---|---|
| [docs/Agent.md](docs/Agent.md) | START HERE — complete app overview for new developers |
| [docs/PRD.md](docs/PRD.md) | Product requirements and evaluation criteria |
| [docs/Features.md](docs/Features.md) | Every feature with technical details |
| [docs/Architecture.md](docs/Architecture.md) | System diagrams and data flows |
| [docs/Database.md](docs/Database.md) | All 7 tables with column definitions |
| [docs/API.md](docs/API.md) | All 30 endpoints with request/response examples |
| [docs/TechStack.md](docs/TechStack.md) | All technologies with versions and purposes |
| [docs/UIUX.md](docs/UIUX.md) | Design system, colors, component specs |
| [docs/AI_Instructions.md](docs/AI_Instructions.md) | How each AI layer works |
| [docs/Security.md](docs/Security.md) | Auth, privacy, API security, rate limiting |
| [docs/OpenSSF_Audit_Report.md](docs/OpenSSF_Audit_Report.md) | OpenSSF Best Practices compliance audit |
| [docs/Deployment.md](docs/Deployment.md) | Step-by-step deployment guide |
| [Hugging Face Hub](https://huggingface.co/datasets/SafeVixAI/SafeVixAI-Dataset-Hub) | **Intelligence Layer** (Models, Data, Notebooks) |
| [SETUP.md](SETUP.md) | Full installation and run guide |
| [RELEASE.md](RELEASE.md) | Release process, versioning, rollback |
| [MAINTAINERS.md](MAINTAINERS.md) | Maintainer list and responsibilities |

---

## Live Demo

- Frontend: https://safevixai.vercel.app
- Backend API: https://safevixai-api.onrender.com/docs

---

## OpenSSF Best Practices

SafeVixAI is pursuing [OpenSSF Best Practices Badge](https://www.bestpractices.dev) compliance.

**Supply chain security controls:**
- ✅ Software Bill of Materials (CycloneDX + SPDX) generated every build
- ✅ Docker images signed with cosign (keyless signing via GitHub OIDC)
- ✅ CodeQL static analysis (Python + JavaScript/TypeScript)
- ✅ OpenSSF Scorecard analysis (weekly)
- ✅ Dependency review on every PR
- ✅ Gitleaks secret scanning (18 custom provider patterns)
- ✅ Trivy filesystem + container vulnerability scanning
- ✅ Dependabot automated dependency updates (weekly, 4 ecosystems)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

- Report bugs via [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues)
- Feature requests: see [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.yml)
- Security vulnerabilities: see [SECURITY.md](SECURITY.md)
- Governance: see [GOVERNANCE.md](GOVERNANCE.md)
- Roadmap: see [ROADMAP.md](ROADMAP.md)
- Support: see [SUPPORT.md](SUPPORT.md)
- All contributions under MIT license

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*IIT Madras Road Safety Hackathon 2026*
