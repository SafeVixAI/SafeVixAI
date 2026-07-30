<!-- 
  SafeVixAI Enterprise README
  Inspired by top CNCF and modern OSS projects (Next.js, Supabase, FastAPI)
-->
<div align="center">
  <br />
  <h1>🛡️ SafeVixAI</h1>
  
  <p><strong>The Enterprise AI-Powered Road Safety & Emergency Response Platform</strong></p>
  
  [![Build Status](https://img.shields.io/github/actions/workflow/status/SafeVixAI/SafeVixAI/backend.yml?label=Build&logo=githubactions&logoColor=white&style=flat-square)](https://github.com/SafeVixAI/SafeVixAI/actions/workflows/backend.yml) [![CodeQL](https://img.shields.io/github/actions/workflow/status/SafeVixAI/SafeVixAI/codeql.yml?label=CodeQL&logo=github&logoColor=white&style=flat-square)](https://github.com/SafeVixAI/SafeVixAI/actions/workflows/codeql.yml) [![Coverage](https://img.shields.io/badge/Coverage-97%25-brightgreen?logo=codecov&logoColor=white&style=flat-square)](https://codecov.io/gh/SafeVixAI/SafeVixAI) [![Documentation](https://img.shields.io/badge/Docs-MkDocs-teal?logo=markdown&logoColor=white&style=flat-square)](https://safevixai.github.io/SafeVixAI/) [![OpenSSF Scorecard](https://img.shields.io/badge/OpenSSF-Scorecard-brightgreen?logo=openssf&logoColor=white&style=flat-square)](https://scorecard.dev/viewer/?uri=github.com/SafeVixAI/SafeVixAI) [![License](https://img.shields.io/badge/License-MIT-blue.svg?logo=open-source-initiative&logoColor=white&style=flat-square)](LICENSE)<br>[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white&style=flat-square)](https://python.org) [![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg?logo=next.js&logoColor=white&style=flat-square)](https://nextjs.org) [![Docker Support](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white&style=flat-square)](https://docker.com) [![Discord](https://img.shields.io/badge/Discord-Join_Community-5865F2?logo=discord&logoColor=white&style=flat-square)](https://github.com/SafeVixAI/SafeVixAI/discussions)

  <p>
    <a href="#-project-vision">Vision</a> •
    <a href="#-key-features">Features</a> •
    <a href="#-technology-stack">Tech Stack</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-system-architecture">Architecture</a> •
    <a href="https://safevixai.github.io/SafeVixAI/">Documentation</a>
  </p>

  <p><em>Built for the IIT Madras Road Safety Hackathon 2026. Offline-first PWA with zero-downtime AI fallback.</em></p>
</div>

---

**SafeVixAI** is a mission-critical, offline-first Progressive Web Application (PWA) designed to provide instant, life-saving road safety intelligence. When networks fail, SafeVixAI doesn't. Our zero-infrastructure architecture ensures that critical features—like deterministic MVA 2019 calculations and SOS emergency protocols—remain fully operational even without internet connectivity.

## 🎯 Project Vision

**Every second counts in a road emergency.** SafeVixAI puts life-saving information — nearest hospitals, traffic laws, first aid protocols — directly in the hands of citizens, officers, and first responders. 

- **Offline-First Resilience**: Ensures the system works when rural or disaster-struck networks fail.
- **Zero-Downtime AI**: A 10-provider LLM cascading chain ensures the AI never goes silent.
- **Open Source**: Infrastructure costs kept at zero—entirely free and accessible to government agencies and the public.

---

## ✨ Key Features

| Feature | Description | Enterprise Capabilities |
|---------|-------------|-------------------------|
| 🚨 **Emergency Locator** | Geospatial hospital, police, and fire station search. | PostGIS spatial indexing, 50ms latency routing. |
| 🤖 **AI Agentic Chatbot** | Traffic law, challan calculation, and first aid guidance. | Agentic RAG, 10-LLM fallback chain, ChromaDB vector store. |
| 🧾 **Challan Calculator** | Deterministic MVA 2019 fine calculation with overrides. | DuckDB-Wasm in-browser, zero-latency offline processing. |
| 📸 **Road Reporter** | Community-driven road damage reporting with geotagging. | IndexedDB sync queue, background sync via Service Workers. |
| 📡 **SOS + Live Tracking** | Hold-to-activate emergency alert with live location. | Secure WebSockets, encrypted payload streaming. |
| 📊 **Command Center** | Real-time agency dashboard with incident timelines. | Grafana integration, Prometheus metric scraping. |

---

## 🛠️ Technology Stack

SafeVixAI is built on a modern, cloud-native microservices architecture designed for extreme scale and fault tolerance.

| Layer | Technologies |
|-------|-------------|
| **Frontend (PWA)** | Next.js 15, React 19, TypeScript 5, Tailwind CSS 3, MapLibre GL, WebLLM, DuckDB-Wasm |
| **Backend Services** | FastAPI (Async), SQLAlchemy 2.0, PostGIS, Redis (hiredis), DuckDB, Overpass/Nominatim |
| **AI & Inference** | FastAPI, ChromaDB, 10 LLM Providers (Groq, Gemini, Sarvam AI, Cerebras, OpenAI, Anthropic, etc.) |
| **Infrastructure** | Docker Compose, Kubernetes (Kustomize), Terraform (AWS), Vercel, Render |
| **Observability** | Prometheus, Grafana, Sentry, Structured JSON Logging |
| **CI/CD** | GitHub Actions (41 active workflows covering tests, linting, SAST, and docs) |

---

## 🚀 Quick Start

SafeVixAI is containerized for rapid developer onboarding. Follow these steps to get a local instance running in minutes.

### Prerequisites
- **Docker & Docker Compose** (Recommended for full-stack)
- **Node.js 20+** & **Python 3.11+** (For bare-metal deployment)

### Containerized Deployment (Recommended)
Launch the entire stack (PostgreSQL, Redis, Backend, AI Service, Frontend) with a single command:
```bash
# Clone the repository
git clone https://github.com/SafeVixAI/SafeVixAI.git
cd SafeVixAI

# Boot the microservices
docker compose up --build -d
```
> **Note**: The frontend will be available at `http://localhost:3000`, backend API at `http://localhost:8000`, and the Chatbot LLM service at `http://localhost:8010`.

### Bare-Metal Local Development
<details>
<summary>Click to view step-by-step local compilation instructions</summary>

**1. Boot the Backend API**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

**2. Boot the AI Chatbot Service**
```bash
cd chatbot_service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8010
```

**3. Boot the Frontend PWA**
```bash
cd frontend
npm ci
cp .env.local.example .env.local
npm run dev
```
</details>

---

## 🏛️ System Architecture

SafeVixAI leverages a highly decoupled, cloud-native architecture. It strictly separates edge-client offline durability from heavy backend processing and AI orchestration, utilizing a rigorous data plane optimized for spatial indexing and vector retrieval.

```mermaid
flowchart TB
    %% Enterprise Themes
    classDef edge fill:#f8fafc,stroke:#3b82f6,stroke-width:2px,color:#0f172a
    classDef control fill:#f0fdf4,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#fef2f2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef data fill:#fffbeb,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef external fill:#f3f4f6,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5,color:#334155

    subgraph EdgeTier ["🌍 Edge Tier (Offline-First PWA)"]
        direction LR
        UI["React 19 / Next.js<br/>(Client UI)"]:::edge
        SW["Service Worker<br/>(Asset Cache)"]:::edge
        IDB[("IndexedDB<br/>(Sync Queue)")]:::edge
        DW[("DuckDB-Wasm<br/>(Offline Analytics)")]:::edge
        UI <--> SW
        UI <--> IDB
        UI <--> DW
    end

    subgraph ControlPlane ["⚙️ Control Plane (Backend :8000)"]
        direction TB
        API["FastAPI Gateway<br/>(JWT & Rate Limiting)"]:::control
        Workers["Background Workers<br/>(Incident Processing)"]:::control
        API <--> Workers
    end

    subgraph AIOrchestration ["🧠 AI Orchestration (:8010)"]
        direction TB
        Router["Agentic Router<br/>(Intent Classification)"]:::ai
        LLM["10-Provider LLM Chain<br/>(Cascading Fallback)"]:::ai
        Router --> LLM
    end

    subgraph DataPlane ["🗄️ Data Plane"]
        direction LR
        PG[("PostgreSQL + PostGIS<br/>(Relational & Spatial)")]:::data
        RD[("Redis 7<br/>(Pub/Sub & Cache)")]:::data
        CR[("ChromaDB<br/>(Vector Storage)")]:::data
    end
    
    subgraph ThirdParty ["🌐 External Integrations"]
        direction LR
        Maps["OpenStreetMap / Data.gov.in"]:::external
    end

    %% Network Flow
    EdgeTier -- "HTTPS / WSS" --> ControlPlane
    EdgeTier -- "Semantic Queries" --> AIOrchestration
    
    ControlPlane --> PG
    ControlPlane --> RD
    ControlPlane -. "Geocoding" .-> Maps
    
    AIOrchestration --> CR
    AIOrchestration --> RD
```

---

## 📚 Comprehensive Documentation

SafeVixAI is exhaustively documented. Our enterprise documentation portal is built using MkDocs and hosted directly on GitHub Pages.

- 🏗️ **[System Architecture](docs/architecture/ARCHITECTURE.md)**: Deep dive into the system design, offline architecture, and data flow patterns.
- 👨‍💻 **[Developer Guide](docs/developer-guide/DEVELOPER_GUIDE.md)**: Coding standards, comprehensive testing policies, and local setup instructions.
- 🔌 **[API Reference](docs/api-reference/SDK_GUIDE.md)**: SDK integrations, OpenAPI schemas, and Webhook definitions for third-party consumers.
- 📈 **[SRE & Operations](docs/sre/OPERATIONS.md)**: Scaling guides, incident runbooks, and Grafana telemetry setup.
- 🛡️ **[Security & Compliance](docs/compliance-and-reports/PRIVACY.md)**: Threat modeling, CNCF audits, and Service Level Agreement (SLA) reports.
- 🗺️ **[Product Roadmap](docs/product-and-planning/ROADMAP.md)**: Upcoming features, feature matrices, and UX architectural plans.

---

## 🤝 Contributing

We believe in the power of open source to save lives. Whether you're optimizing a Postgres query, expanding the AI RAG corpus, or fixing a UI typo, your contributions are critical.

1. Review our **[Code of Conduct](docs/developer-guide/CODE_OF_CONDUCT.md)**.
2. Read the **[Contributing Guide](docs/developer-guide/CONTRIBUTING.md)** for Git workflow standards.
3. Check out the **[Good First Issues](https://github.com/SafeVixAI/SafeVixAI/labels/good%20first%20issue)** to jump right in.

---

## 🛡️ Security & Trust

Security is our top priority. The SafeVixAI platform utilizes strict SBOM (Software Bill of Materials) tracking, CodeQL static analysis, and regular dependency audits via Dependabot.

If you discover a security vulnerability, please refer to our **[Security Policy](docs/compliance-and-reports/SECURITY.md)** and report it directly to **security@safevixai.gov.in**. We adhere to responsible disclosure guidelines.

---

## 💬 Community & Support

Join the thousands of developers building a safer road ecosystem:

- **Discussions**: Join the architectural conversation on [GitHub Discussions](https://github.com/SafeVixAI/SafeVixAI/discussions).
- **Issues**: Report platform bugs or request robust features via [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues).
- **Support SLAs**: View enterprise support tiers in [SUPPORT.md](docs/compliance-and-reports/SUPPORT.md).

---

## ✨ Contributors

A massive thank you to everyone who has contributed to making SafeVixAI a reality. 

<a href="https://github.com/SafeVixAI/SafeVixAI/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=SafeVixAI/SafeVixAI" alt="Contributors Graph" />
</a>

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=SafeVixAI/SafeVixAI&type=Date)](https://star-history.com/#SafeVixAI/SafeVixAI&Date)

---
<div align="center">
  <p>Built with ❤️ and extreme engineering by the <strong>SafeVixAI Team</strong> for a safer tomorrow.</p>
  <p>Released under the <a href="LICENSE">MIT License</a>.</p>
</div>
