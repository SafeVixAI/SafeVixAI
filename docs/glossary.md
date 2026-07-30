# Glossary

Key terms used across the SafeVixAI documentation.

## A

**ADR (Architecture Decision Record)** — Documented architectural decisions in `docs/adr/`. 12 ADRs cover CQRS, Redlock, DuckDB-Wasm, MapLibre, and more.

**AST Stub** — Auto-generated documentation skeleton created by parsing source code abstract syntax trees. Used as fallback when LLM generation fails.

**ASR (Automatic Speech Recognition)** — Speech-to-text conversion, used for voice input in Indian languages.

**Accessibility** — WCAG 2.1 AA compliance target. Tested with jest-axe and manual keyboard/screen reader testing.

## B

**Backend** — FastAPI service on port 8000. Handles API requests, database operations, and business logic for emergency locator, challan calculator, road reports, and live tracking.

## C

**Chatbot Service** — Separate FastAPI service on port 8010. Agentic RAG system with 10-provider LLM fallback chain.

**ChromaDB** — Vector database used for RAG (Retrieval-Augmented Generation) in the chatbot service. Stores embeddings of traffic law and first-aid documents.

**CIFS (Common Incident File Share)** — Waze data feed format for community traffic and hazard data.

**Circuit Breaker** — Pattern that prevents cascading failures by detecting repeated errors and opening the circuit (stopping requests) for a cooldown period. 3-failure threshold, 30s half-open.

**ContextAssembler** — Chatbot component that gathers context from tools and RAG before sending to LLM.

**CQRS (Command Query Responsibility Segregation)** — Pattern separating write operations (commands) from read operations (queries). Implemented via `core/cqrs.py`.

**Conventional Commits** — Standardized commit format: `type(scope): description`. Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore.

**Coverage** — Code coverage targets: Backend 100%, Chatbot 97%+, Frontend 86% lines.

**Cross-Site Request Forgery (CSRF)** — Security protection using CSRF tokens on all state-changing requests.

## D

**Docker Compose** — 5-service stack: postgres (PostGIS), redis, backend, chatbot, frontend.

**DuckDB-Wasm** — In-browser SQL engine for offline challan calculations. Runs in the frontend without a server.

**DPDP (Digital Personal Data Protection)** — Indian data protection law. SafeVixAI follows DPDP principles for user privacy.

## E

**Embeddings** — Vector representations of text. SafeVixAI uses `LocalHashEmbeddingFunction` (SHA-256 based, zero-dependency).

## F

**Fallback Chain** — Sequence of 10 LLM providers tried in order: Groq → Cerebras → Gemini → GitHub Models → NVIDIA NIM → OpenRouter → Mistral → Together → Template.

**FastAPI** — Python web framework used by both backend and chatbot service.

## G

**GeoAlchemy2** — SQLAlchemy extension for PostGIS spatial queries.

**GSAP (GreenSock Animation Platform)** — JavaScript animation library used for page transitions. Respects `prefers-reduced-motion`.

**GDPR (General Data Protection Regulation)** — EU data protection regulation. SafeVixAI respects GDPR with consent-based analytics, data minimization, and right to erasure.

## H

**HS256** — HMAC with SHA-256, the JWT signing algorithm used for auth tokens.

## I

**Idempotency** — Property where repeating an operation produces the same result. SafeVixAI uses idempotency keys (SHA-256) for critical POST endpoints.

**IndexedDB** — Browser database used for offline data persistence: user profile, SOS queue, road report queue.

**IntentDetector** — Chatbot component that classifies user messages into 9 intent classes: emergency, first_aid, challan, legal, road_weather, safe_route, road_infrastructure, road_issue, general.

**i18n** — Internationalization. 14 Indian language support in UI, speech, and chatbot.

## J

**JWT (JSON Web Token)** — Authentication tokens signed with HS256, used for API auth.

## L

**Live Tracking** — WebSocket-based real-time family member location sharing via `wss://host/api/v1/tracking/{session_id}`.

**LLM (Large Language Model)** — AI model used by the chatbot. SafeVixAI supports 10 providers in a cascading fallback chain.

**LocalHashEmbeddingFunction** — Zero-dependency embedding function using SHA-256 hashing for ChromaDB vector search.

**Loki** — Log aggregation system for structured JSON logs from all services.

## M

**MapLibre GL** — Open-source map rendering library, used instead of Google Maps.

**MCP (Model Context Protocol)** — Protocol for external agent integration. Exposed via `backend/api/v1/mcp_server.py`.

**Mermaid** — Diagram-as-code language used in wiki documentation for flowcharts, sequence diagrams, and ER diagrams.

**MkDocs** — Documentation site generator using Material theme. Site published to GitHub Pages at `safevixai.github.io/SafeVixAI`.

**Mutation Testing** — Testing technique that introduces bugs to verify tests catch them. mutmut configured for backend (CI informational).

## O

**OpenAPI** — Standard specification format for REST APIs. SafeVixAI generates `openapi.json` for both backend and chatbot service.

**Overpass API** — OpenStreetMap query API used for geocoding and POI lookup.

## P

**PostGIS** — Spatial database extension for PostgreSQL. All location queries use `ST_DWithin` with `::geography` for meter-based distance.

**Prometheus** — Metrics collection system. Backend exposes `/metrics` endpoint with custom metrics.

**PWA (Progressive Web App)** — Installable web application with offline support via Service Worker.

**Pydantic** — Data validation library used for API request/response schemas in FastAPI.

## R

**RAG (Retrieval-Augmented Generation)** — Pattern where LLM responses are augmented with retrieved context from a vector database.

**Rate Limiting** — API request throttling using `slowapi`. Limits: General 100/min, Auth 5/min, SOS 3/min, Challan 60/min, Chat 30/min.

**RoadWatch** — Road reporter module for submitting and tracking road damage reports.

## S

**Sarvam AI** — Indian language LLM provider. Sarvam-30B for general queries, Sarvam-105B for legal content.

**SBOM (Software Bill of Materials)** — CycloneDX + SPDX format, generated every build.

**Semantic Versioning** — Version format MAJOR.MINOR.PATCH (e.g., 1.0.0). See VERSIONING.md for full policy.

**SLSA (Supply-chain Levels for Software Artifacts)** — Level 3 provenance attestation per commit.

**slowapi** — Rate limiting library for FastAPI. Configured in `backend/core/limiter.py`.

**ST_MakePoint** — PostGIS function. Takes (longitude, latitude) — longitude FIRST.

**Supabase Auth** — Authentication provider. Manages user signup, login, and JWT token generation.

## T

**TTS (Text-to-Speech)** — Speech synthesis for assistant voice output.

## W

**WebLLM** — Client-side LLM inference via `@mlc-ai/web-llm`. Phi-3 Mini model (~2.2GB) downloaded on demand.

**WebSocket** — Protocol used for live tracking at `ws://<host>/api/v1/tracking/{group_id}`.

**What3Words** — Location resolution system that divides the world into 3m x 3m squares, each with a unique 3-word address.

## Z

**Zustand** — State management library for the frontend, used with IndexedDB persistence.
