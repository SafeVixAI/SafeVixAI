# SafeVixAI — Tech Stack

## Overview

SafeVixAI uses a **three-service architecture** with in-browser AI inference as an offline fallback.

```mermaid
flowchart TB
    subgraph Frontend["Frontend Layer — Free (Vercel)"]
        F1[Next.js 15 + React 19 + Tailwind]
        F2[MapLibre GL - Maps]
        F3[DuckDB-Wasm - Edge SQL]
        F4[Transformers.js + YOLOv8 - Edge Vision]
        F5[WebLLM Phi-3 Mini - Offline LLM]
    end

    subgraph Backend["Backend Layer — Free (Render.com)"]
        B1[FastAPI + Python 3.11]
        B2[ChromaDB - Vector Store]
        B3[Redis - Cache via Upstash]
        B4[PostgreSQL 16 + PostGIS]
    end

    subgraph AI["AI Layer — Free (Multi-Provider)"]
        A1[Groq / Gemini / Sarvam AI]
        A2[LocalHashEmbeddingFunction]
    end

    subgraph Data["Data Sources — Free"]
        D1[Overpass API - POI Data]
        D2[Nominatim - Geocoding]
    end

    subgraph CI["CI/CD — Free (GitHub Actions)"]
        C1[2000 min/month]
    end

    F1 --> B1
    B1 --> B4
    B1 --> B3
    B1 --> D1
    B1 --> D2
    A1 --> B2
    F3 --> B1

    style Frontend fill:#1f6feb,color:#fff
    style Backend fill:#238636,color:#fff
    style AI fill:#9e6a03,color:#fff
    style Data fill:#6e5494,color:#fff
    style CI fill:#8957e5,color:#fff
```

---

## Frontend Stack

| Technology | Version | Purpose |
|---|---|---|
| **Next.js** | 15.5.18 | App Router, SSR, PWA, code splitting |
| **React** | 19.2.6 | UI framework |
| **TypeScript** | 6.0.3 | Type safety |
| **Tailwind CSS** | 3.4.x | Utility-first styling, dark navy theme |
| **clsx** | — | Conditional class joining |
| **tailwind-merge** | — | Tailwind class merging |
| **class-variance-authority** | — | Component variants |
| **MapLibre GL** | 5.22.0 | Vector map — `dynamic({ssr:false})` |
| **Zustand** | 4.5.4 | Global state: GPS, services, AI mode |
| **SWR** | 2.4.1 | Data fetching with stale-while-revalidate |
| **Axios** | 1.17.0 | HTTP client |
| **GSAP** | 3.15.0 | Animations (`@gsap/react`) |
| **@mlc-ai/web-llm** | — | Phi-3 Mini in-browser inference (WebGPU/Wasm) |
| **@huggingface/transformers** | 4.0.1 | YOLOv8n ONNX pothole detection |
| **@duckdb/duckdb-wasm** | 1.29.0 | Browser SQL engine for offline challan |
| **i18next** | 26.3.1 | Internationalization |
| **react-i18next** | 17.0.8 | React binding for i18next |
| **@supabase/supabase-js** | 2.107.0 | Supabase client for storage + auth |
| **idb** | 8.0.3 | IndexedDB wrapper |
| **lucide-react** | — | Icon set |
| **qrcode.react** | 4.2.0 | QR code generation |
| **three** | — | 3D rendering (landing page) |
| **@react-three/fiber** | — | React renderer for Three.js |
| **@react-three/drei** | — | Three.js helpers |
| **posthog-js** | — | Product analytics |
| **sonner** | — | Toast notifications |
| **cmdk** | — | Command palette |
| **use-debounce** | — | Debounced hooks |
| **lenis** | — | Smooth scrolling |

### Testing & Quality

| Technology | Version | Purpose |
|---|---|---|
| **Jest** | 30.3.0 | Unit testing |
| **Playwright** | 1.60.0 | E2E testing |
| **@axe-core/playwright** | — | Accessibility testing |
| **ESLint** | 8.57.1 | Linting |
| **eslint-config-next** | 15.5.18 | Next.js lint rules |

### Offline Browser APIs

| API | Purpose | Browser Support |
|---|---|---|
| `navigator.geolocation` | GPS location | All modern |
| `DeviceMotion API` | Crash detection (60Hz accelerometer) | Chrome, Safari, Edge |
| `Web Speech API` | Voice input transcription | Chrome, Edge, Samsung |
| `SpeechSynthesis API` | Voice output | All modern |
| `Service Worker` | Offline caching | Chrome, Edge, Firefox |
| `Cache Storage API` | Model weights + GeoJSON caching | All modern |
| `IndexedDB` | Offline profile, SOS queue, RAG index | All modern |
| `Background Sync API` | Auto-submit offline reports | Chrome, Edge |

---

## Backend Stack (Port 8000)

| Technology | Purpose |
|---|---|
| **FastAPI** | Async REST API framework |
| **Python 3.11+** | Runtime |
| **SQLAlchemy 2.x** (async) | ORM |
| **GeoAlchemy2** | PostGIS geometry column types |
| **asyncpg** | Async PostgreSQL driver |
| **Alembic** | Database migrations |
| **Pydantic** + **pydantic-settings** | Request validation + config |
| **PyJWT** (HS256) + **passlib** (bcrypt) | Authentication |
| **redis** + **hiredis** | Async cache (graceful fallback) |
| **PostGIS 16** | Spatial queries |
| **duckdb** (Python) | Offline SQL computation |
| **httpx** | Async HTTP client |
| **Overpass API** / **Nominatim** / **Photon** / **OpenRouteService** | Maps & geocoding |
| **slowapi** | Rate limiting |
| **uvicorn** | ASGI server |
| **python-multipart** | File upload parsing |
| **Pillow** | Image validation |
| **Prometheus client** | Metrics |
| **Sentry SDK** | Error monitoring |

### Testing

| Technology | Configuration |
|---|---|
| **pytest** | `asyncio_mode = auto` — async tests run automatically |
| **pytest-cov** | Coverage reporting |
| **httpx** | Async test client |

---

## Chatbot Service Stack (Port 8010)

A **separate FastAPI service** with its own Python environment & heavy ML dependencies.

| Technology | Purpose |
|---|---|
| **FastAPI** | Async REST API |
| **Python 3.11+** | Runtime |
| **torch / torchaudio** | PyTorch runtime for speech models |
| **transformers** | Hugging Face model loading |
| **datasets** | Dataset loaders |
| **ChromaDB 0.5.x** | Local vector store for RAG |
| **LocalHashEmbeddingFunction** | Hash-based 384-dim embeddings (SHA-256, zero ML dep) |
| **redis** | Conversation memory |
| **httpx / requests** | HTTP API clients |

### 10-provider LLM Fallback Chain

| Provider | Model | Speed | Use Case |
|----------|-------|-------|----------|
| **Groq** | llama3-70b-8192 | 300+ tok/s | Primary English |
| **Cerebras** | llama-3.3-70b | 2000+ tok/s | Speed overflow |
| **Gemini** | 1.5 Flash | Varies | Large context (1M tokens) |
| **GitHub Models** | Various | Varies | Free with GitHub account |
| **NVIDIA NIM** | Various | Varies | GPU-optimized |
| **OpenRouter** | 20+ models | Varies | Multi-provider gateway |
| **Mistral** | Various | Varies | 1B tok/month free |
| **Together** | Various | Varies | $25 credit |
| **Sarvam AI** | sarvam-30b / 105b | Varies | Indian languages (auto-routed) |
| **Template** | Deterministic | Instant | Always-works fallback |

### Testing

| Technology | Configuration |
|---|---|
| **pytest** | `asyncio_mode = strict` — async tests **require** `@pytest.mark.asyncio` |

### Config Note
- Config uses **dataclass + os.getenv** — NOT pydantic-settings (despite pydantic-settings being in requirements.txt)

---

## AI Models

| Model | Parameters | Size | Runtime | Use Case |
|---|---|---|---|---|
| Groq llama3-70b-8192 | 70B | Cloud | Groq API | Online chatbot — max intelligence |
| Gemini 1.5 Flash | — | Cloud | Gemini API | Large context |
| Sarvam-30B | 30B | Cloud | Sarvam API | Indian languages |
| Sarvam-105B | 105B | Cloud | Sarvam API | Legal Indic queries |
| Phi-3-mini-4k-instruct-q4f16_1-MLC | 3.8B | ~2.2GB | WebGPU | Offline chatbot — primary |
| gemma-2b-it-q4f16_1-MLC | 2B | ~1.4GB | WebAssembly | Offline chatbot — CPU fallback |
| LocalHashEmbeddingFunction | N/A | 0 MB | CPU | Hash-based 384-dim embeddings |
| Xenova/yolov8n | ~6M | ~15MB | Browser Wasm | Pothole detection |
| ai4bharat/indic-seamless | Large | ~7GB | Server GPU/CPU | Indian language speech (ASR/TTS) |

---

## Database

| Store | Technology | Use |
|---|---|---|
| **Primary DB** | Supabase PostgreSQL 16 + PostGIS 3.4 | All tables + spatial queries |
| **Cache** | Upstash Redis | API cache, chat history, rate limits |
| **Vector Store** | ChromaDB (local persistent) | RAG chunks from MV Act + WHO PDFs |
| **Browser Store** | IndexedDB (via `idb`) | Offline profile, SOS queue, HNSWlib index |

---

## Infrastructure

| Service | Provider | Free Tier | Use |
|---|---|---|---|
| Frontend hosting | Vercel | 100GB/month CDN | Next.js PWA |
| Backend hosting | Render.com | 750 hrs/month (512MB RAM) | FastAPI :8000 |
| Chatbot hosting | Render.com | 750 hrs/month (2GB RAM) | FastAPI :8010 |
| Database | Supabase | 500MB PostgreSQL | All tables |
| Cache | Upstash | 10K commands/day | Redis |
| LLM APIs | Groq + 9 more | Free tiers | Provider chain |
| Model CDN | Hugging Face | Unlimited public | WebLLM weights |
| Maps | MapLibre GL + OSM | Free (open source) | Vector tiles |
| Geocoding | Nominatim | 1 req/sec | Address lookup |
| POI data | Overpass API | Fair use | Emergency services |
| CI/CD | GitHub Actions | 2,000 min/month | 40 workflows |
| Container | Docker + docker-compose | Free | 5 services |

---

*Document version: 2.0 | AI-powered road safety platform | Updated: June 2026*
