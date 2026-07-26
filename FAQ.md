# Frequently Asked Questions

> **SafeVixAI** — AI-Powered Road Safety Platform  
> MIT License — IIT Madras Road Safety Hackathon 2026

---

## About SafeVixAI

### What is SafeVixAI?
SafeVixAI is an open-source, AI-powered road safety Progressive Web Application (PWA) built for the IIT Madras Road Safety Hackathon 2026. It solves three problem statements: Emergency Locator, AI Chatbot (traffic law + first aid), Challan Calculator, and Road Reporter.

### Who built SafeVixAI?
SafeVixAI was built by a team participating in the National Road Safety Hackathon 2026 organized by the Centre of Excellence for Road Safety (CoERS), IIT Madras. It is now maintained as an open-source project by the community.

### What problem does SafeVixAI solve?
SafeVixAI addresses road safety through four pillars: (1) instant emergency response with SOS and family tracking, (2) an AI chatbot for traffic law and first-aid guidance, (3) a challan/fine calculator using DuckDB, and (4) a road reporter for citizen infrastructure issue tracking.

### What is the license?
SafeVixAI is released under the MIT License. See [LICENSE](./LICENSE) for full terms.

### Is SafeVixAI free?
Yes. SafeVixAI is 100% free and open source. Total infrastructure cost is ₹0 — it runs entirely on free tiers (Vercel, Render, Supabase, Upstash).

---

## Features

### What are the main features?
Key features include: SOS emergency with hold-to-activate and family tracking, AI chatbot with 9-provider LLM fallback, offline-first challan calculator using DuckDB-Wasm, road issue reporting with photo upload, bystander mode, crash detection via device motion sensors, and voice/speech translation in 14 Indian languages.

### Does SafeVixAI work offline?
Yes. SafeVixAI is offline-first. The service worker caches core assets, DuckDB-Wasm enables offline challan calculation, IndexedDB queues SOS and road reports for sync when connectivity returns, and the WebLLM Phi-3 model provides offline AI assistance when downloaded.

### What is the AI chatbot?
The AI chatbot is an agentic RAG system with 9 LLM providers in a fallback chain (Groq, Cerebras, Gemini, GitHub Models, NVIDIA NIM, OpenRouter, Mistral, Together, Template). It uses 13 tools for tasks like emergency lookup, challan calculation, legal search, first-aid guidance, weather, geocoding, and more.

### Does SafeVixAI support Indian languages?
Yes. The chatbot auto-detects languages via Unicode script ranges and routes to Sarvam AI (30B or 105B) for Indian languages. The speech translation endpoint supports 14 Indian languages with ASR/TTS.

### How does the SOS feature work?
Users press and hold a button for 2 seconds to activate SOS. The app captures geolocation, sends SMS/WhatsApp alerts to emergency contacts, and starts real-time family tracking via WebSocket. If offline, the SOS is queued in IndexedDB and flushed when connectivity returns.

### What is bystander mode?
Bystander mode allows witnesses to report accidents, capture GPS coordinates, provide first-aid guidance, and call emergency services — all without needing to be logged in.

---

## Tech Stack

### What is the technology stack?
Frontend: Next.js 15 + React 19 + TypeScript + Tailwind CSS 3 + MapLibre GL. Backend: FastAPI + PostgreSQL/PostGIS + Redis. Chatbot Service: FastAPI + ChromaDB + 9 LLM providers. Infrastructure: Docker Compose, Kubernetes (k8s), GitHub Actions CI/CD.

### Why two separate FastAPI services?
The chatbot service has heavy ML dependencies (torch ~2GB). Keeping it separate from the lightweight backend ensures clean dependency management and independent scaling.

### What database does SafeVixAI use?
PostgreSQL with PostGIS extension for geospatial queries. Redis is used for caching and conversation memory. DuckDB-Wasm runs in the browser for offline challan calculations.

### What mapping library is used?
MapLibre GL — an open-source alternative to Google Maps. Map components are loaded with `dynamic({ssr:false})` to avoid server-side rendering issues.

---

## Installation

### How do I set up SafeVixAI locally?
See [SETUP.md](./SETUP.md) for step-by-step instructions. In short: clone the repo, set up Python virtual environments for `backend/` and `chatbot_service/`, add `.env` files, and run `npm install && npm run dev` in `frontend/`.

### What are the system requirements?
Node.js 20+, Python 3.11+, PostgreSQL 16 with PostGIS, Redis 7 (optional, falls back to in-memory), and a modern browser with PWA support.

### Do I need API keys?
Yes. You need keys for LLM providers (Groq, Gemini, etc.), optionally OpenWeather, and Data.gov.in. See the `.env.example` files in each service directory.

### How do I run with Docker?
Run `docker compose up --build` from the project root. This starts all 5 services: PostgreSQL, Redis, backend, chatbot, and frontend.

---

## Configuration

### Where are environment variables configured?
Each service has its own `.env` file. Backend uses `backend/.env`, chatbot uses `chatbot_service/.env`, frontend uses `frontend/.env.local`. See [AGENTS.md](./AGENTS.md) for the full variable reference.

### How do I configure the chatbot provider?
Set `DEFAULT_LLM_PROVIDER` and `DEFAULT_LLM_MODEL` in `chatbot_service/.env`. The fallback chain is: Groq → Cerebras → Gemini → GitHub Models → NVIDIA NIM → OpenRouter → Mistral → Together → Template.

### How do I change the language?
The app supports 14 Indian languages. Users can switch languages from the settings page. Language detection is automatic for chatbot queries.

---

## Deployment

### Where is SafeVixAI deployed?
Frontend on Vercel, Backend on Render.com, Chatbot Service on Render.com, Database on Supabase (PostgreSQL + PostGIS), Redis on Upstash.

### How do I deploy my own instance?
Fork the repository, connect each service to its respective platform (Vercel for frontend, Render for backend/chatbot), set environment variables, and configure the database. See [docs/Deployment.md](./docs/Deployment.md).

### Is there a Kubernetes deployment?
Yes. See `k8s/` directory for namespace, ingress, and deployment manifests.

---

## Security & Privacy

### How is user data protected?
Blood group, emergency contacts, and medical info never leave the device — stored in IndexedDB only. JWT authentication uses RS256 signatures. API requests use CSRF tokens. All communications are HTTPS.

### Is there GDPR compliance?
Yes. The app respects GDPR/DPDP principles. See [PRIVACY.md](./docs/PRIVACY.md) for details on data collection, retention, and erasure policies.

### How are API keys secured?
All secrets go in `.env` files (gitignored). The CI pipeline uses GitHub secrets. The security workflow runs gitleaks to detect committed secrets.

---

## Offline Mode

### What works offline?
Offline challan calculation (DuckDB-Wasm), cached emergency numbers, PWA app shell, IndexedDB SOS/road report queue, and (after download) WebLLM Phi-3 AI assistant.

### How do I enable offline AI?
Click "Use Offline AI" on the assistant page. This downloads the Phi-3 Mini model (2.2GB) via WebLLM. Once downloaded, the chatbot works without internet.

### What happens to SOS when offline?
The SOS is queued in IndexedDB via `offline-sos-queue.ts`. It auto-flushes when the browser fires the `online` event.

---

## Integration

### Does SafeVixAI have an API?
Yes. The backend exposes REST APIs at `/api/v1/` and WebSocket endpoints for tracking. The chatbot service has its own API at `/api/v1/chat/`. See [docs/API.md](./docs/API.md) and [docs/SDK_GUIDE.md](./docs/SDK_GUIDE.md).

### What is the MCP server?
The backend includes an MCP (Model Context Protocol) server at `api/v1/mcp_server.py` for external agent integration.

### Can I integrate SafeVixAI with my app?
Yes. See the [Integration Guide](./docs/INTEGRATION_GUIDE.md) for REST API documentation, authentication, WebSocket connections, rate limits, and SDK examples.

---

## Contributing

### How can I contribute?
See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines. We welcome bug fixes, features, documentation, tests, and translations.

### How do I report a bug?
Open a GitHub Issue with the bug report template. Include environment details, reproduction steps, and expected vs actual behavior.

### How do I request a feature?
Open a GitHub Issue using the feature request template. Describe the problem, proposed solution, and alternatives considered.

---

## Support

### Where do I get help?
- [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues) for bug reports and feature requests
- [GitHub Discussions](https://github.com/SafeVixAI/SafeVixAI/discussions) for Q&A
- [SUPPORT.md](./SUPPORT.md) for support channels and response times

### How do I report a security vulnerability?
Email **security@safevixai.gov.in**. Do not file a public issue. See [SECURITY.md](./SECURITY.md) for the disclosure policy.

---

*Last updated: 2026-07-26*
