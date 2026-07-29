# SafeVixAI — Features Specification

## Feature Overview

```mermaid
flowchart TB
    subgraph EMERGENCY["Module 1: Emergency Locator"]
        F1a[GPS Auto-Detection]
        F1b[Nearby Services Map]
        F1c[Tiered Radius Fallback]
        F1d[SOS WhatsApp Share]
        F1e[Emergency Numbers Bar]
        F1f[Crash Detection]
        F1g[Offline Map - 25 Cities]
        F1h[First Aid Guidance]
    end

    subgraph CHATBOT["Module 2: AI Chatbot"]
        F2a[Intent Detection - 9 Classes]
        F2b[Online RAG Chatbot]
        F2c[Offline WebLLM]
        F2d[Multilingual - 14 Languages]
        F2e[Voice Input/Output]
        F2f[LLM Fallback Chain - 10 Providers]
        F2g[Conversation Memory]
        F2h[Streaming Chat SSE]
    end

    subgraph CHALLAN["Module 3: Challan Calculator"]
        F3a[Fine Calculation Engine]
        F3b[MVA AI Assistant]
    end

    subgraph ROADWATCH["Module 4: RoadWatch Reporter"]
        F4a[Geotagged Issue Reporting]
        F4b[Automatic Authority Routing]
        F4c[Road Infrastructure Transparency]
        F4d[Community Issues Map Layer]
    end

    subgraph SAFETY["Module 5: Safety & Auth"]
        F5a[Safety Checker]
        F5b[JWT Authentication]
        F5c[Circuit Breakers]
    end

    subgraph OFFLINE["Module 6: Offline"]
        F6a[Offline SOS Queue]
        F6b[WebLLM Offline AI]
        F6c[PWA Share Target]
    end

    style EMERGENCY fill:#da3633,color:#fff
    style CHATBOT fill:#1f6feb,color:#fff
    style CHALLAN fill:#9e6a03,color:#fff
    style ROADWATCH fill:#238636,color:#fff
    style SAFETY fill:#6e5494,color:#fff
    style OFFLINE fill:#8957e5,color:#fff
```

## Feature Status (25/25 Complete)

| # | Feature | Status |
|---|---------|--------|
| 1 | Emergency Locator (radius expansion, nearby services) | ? COMPLETE |
| 2 | AI Chatbot RAG (traffic law + first aid) | ? COMPLETE |
| 3 | LLM Fallback Chain (10 providers) | ? COMPLETE |
| 4 | Challan Calculator (DuckDB, offline + online) | ? COMPLETE |
| 5 | RoadWatch Reporter (community issue reporting) | ? COMPLETE |
| 6 | Crash Detection (Accelerometer + CrashCountdown) | ? COMPLETE |
| 7 | Offline SOS Queue (IndexedDB, auto-flush) | ? COMPLETE |
| 8 | WebLLM Offline AI (Phi-3 Mini) | ? COMPLETE |
| 9 | What3Words Integration | ? COMPLETE |
| 10 | Voice/ASR (IndicSeamless, 14 languages) | ? COMPLETE |
| 11 | Indian Language Detection (14 languages) | ? COMPLETE |
| 12 | PWA Share Target | ? COMPLETE |
| 13 | QR Emergency Card | ? COMPLETE |
| 14 | MCP Server (Agent-to-Agent) | ? COMPLETE |
| 15 | Waze CIFS Feed Integration | ? COMPLETE |
| 16 | Circuit Breakers | ? COMPLETE |
| 17 | Streaming Chat (SSE) | ? COMPLETE |
| 18 | Conversation Summarization | ? COMPLETE |
| 19 | Multi-Turn Intent Refinement | ? COMPLETE |
| 20 | Safety Checker (Prompt Injection Defense) | ? COMPLETE |
| 21 | GSAP Animations | ? COMPLETE |
| 22 | Speech Language Mapping (4-code system) | ? COMPLETE |
| 23 | Assistant Voice Output | ? COMPLETE |
| 24 | Authentication (JWT + Service Auth) | ? COMPLETE |
| 25 | Family Live Tracking (WebSocket) | ? COMPLETE |

---

## Module 1: Emergency Locator

### F1.1 — GPS Auto-Detection
- `navigator.geolocation.getCurrentPosition` with `enableHighAccuracy: true`
- 10-second timeout, cached for 30 seconds (maximumAge)
- On deny: clear error screen with instructions to enable GPS
- `watchPosition` auto-refreshes nearby list when user moves > 500m

### F1.2 — Nearby Emergency Services Map
- MapLibre GL with dark vector tiles (free, no API key)
- Color-coded circle markers: hospitals (red), police (blue), ambulance (red+cross), fire (orange-red), towing (amber), puncture (green)
- Marker popups: name, distance, phone, Tap-to-Call, Directions (Google Maps deep link)
- Services sorted: has_trauma first ? is_24hr ? distance ASC

### F1.3 — Tiered Radius Fallback
- Sequence: 500m ? 1km ? 5km ? 10km ? 25km ? 50km
- If PostGIS < 3 results: expand radius automatically
- If DB still sparse at 50km: Overpass API live fallback
- UI badge shows actual search radius used

### F1.4 — SOS WhatsApp Share
- Fixed red SOS button (bottom-right, always visible)
- Generated message: Google Maps link, GPS, nearest hospital + phone, nearest police + phone, 112/102 numbers
- Optional: blood group, vehicle number from user profile
- Opens via `wa.me` deep link — no WhatsApp API key needed

### F1.5 — Emergency Numbers Bar
- Fixed bottom bar on every page: 112, 102, 100, 1033
- Standard `tel:` href — opens phone dialer
- Long-press 3-second confirmation with countdown animation

### F1.6 — Crash Detection (Accelerometer + CrashCountdown UI)
- DeviceMotion API at ~60Hz
- Thresholds: Minor 6G, Moderate 15G, Severe 30G
- Speed gate: GPS speed > 15 km/h (prevents phone-drop false positives)
- Duration gate: high-G < 500ms
- 20-second "Are you okay?" countdown with progress circle + haptic vibration
- If no cancel: auto-sends SOS + opens emergency page

### F1.7 — Offline Emergency Map (25 Cities)
- `india-emergency.geojson` cached by Service Worker
- Turf.js `nearestPoint()` for haversine distance filtering
- Orange "Offline — Cached Data" banner
- Cities: Chennai, Mumbai, Delhi, Bengaluru, Hyderabad, Kolkata, Pune, Ahmedabad, Jaipur, Lucknow, Chandigarh, Bhopal, Patna, Kochi, Coimbatore, Nagpur, Visakhapatnam, Surat, Indore, Bhubaneswar, Thiruvananthapuram, Madurai, Vadodara, Agra, Varanasi

### F1.8 — First Aid Guidance
- Dedicated `/first-aid` page with 8 static scenario cards (no AI needed)
- Scenarios: Severe Bleeding, Unconscious, Fracture, Burn, Choking, Cardiac Arrest, Head Injury, Snake Bite
- WHO-based steps — works fully offline

---

## Module 2: AI Chatbot

### F2.1 — Intent Detection (9 Classes)
| Intent | Trigger Examples | Tools Called |
|--------|-----------------|-------------|
| EMERGENCY | "nearest hospital", "accident injury" | SOS/Emergency tools |
| FIRST_AID | "bleeding", "unconscious", "fracture" | FirstAid tool |
| CHALLAN | "fine", "penalty", "drunk driving cost" | Challan tool |
| LEGAL | "speed limit", "Section 184" | LegalSearch tool |
| ROAD_WEATHER | "weather near me", "road conditions" | WeatherTool + OpenMeteo |
| SAFE_ROUTE | "safe route to..." | Geocoding tool |
| ROAD_INFRASTRUCTURE | "who maintains this road" | RoadInfra tool |
| ROAD_ISSUE | "pothole near", "broken road" | RoadIssues tool |
| GENERAL | "hello", "what can you do" | Direct LLM |

### F2.2 — Online RAG Chatbot
- ChatEngine with ContextAssembler + ProviderRouter
- 10-provider fallback chain (Groq primary, 300+ tok/s)
- Indian languages auto-routed to Sarvam AI (30B general, 105B legal)
- ChromaDB MMR search, top-5 chunks
- Knowledge base: MV Act 1988 + MV Amendment 2019 + WHO Trauma Care Guidelines
- Embeddings: LocalHashEmbeddingFunction (hash-based 384-dim)

### F2.3 — Offline Chatbot (WebLLM)
- Primary: `Phi-3-mini-4k-instruct-q4f16_1-MLC` (3.8B, ~2.2GB, WebGPU)
- Fallback: `gemma-2b-it-q4f16_1-MLC` (2B, ~1.4GB, WebAssembly CPU)
- Runtime detection: `navigator.gpu.requestAdapter()`
- Response time: 3-5s (WebGPU) or 8-15s (WebAssembly)

### F2.4 — Multilingual Support (14 Languages)
- Auto-detect input language (regex-based Unicode script ranges)
- Indian language queries ? Sarvam AI (4 trillion Indic tokens)
- English ? default provider
- Supported: English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Assamese, Urdu, Sanskrit

### F2.5 — Voice Input/Output
- Input: Web Speech API (Chrome, Edge, Samsung Internet)
- Mic button turns red + pulses when recording, auto-stops after 5s silence
- Output: SpeechSynthesis API (speaker icon per bot message)
- Graceful degradation on Safari/Firefox

### F2.6 — LLM Fallback Chain (10 providers)
- **Order**: Groq ? Cerebras ? Gemini ? GitHub Models ? NVIDIA NIM ? OpenRouter ? Mistral ? Together ? Template (deterministic)
- Indian language queries bypass the chain: routed directly to Sarvam AI
- Email alert sent when all providers fail (via `alert_service.py` at project root)

### F2.7 — Conversation Memory
- Redis-backed `ConversationMemoryStore` with configurable window
- Session TTL: 24 hours, key: `chat:memory:{session_id}`

### F2.8 — Streaming Chat (SSE)
- `POST /api/v1/chat/stream` — Server-Sent Events for real-time token streaming
- Works across all providers in the fallback chain

### F2.9 — Conversation Summarization
- Historical conversations summarized for context injection
- Reduces token usage while maintaining conversation coherence

### F2.10 — Multi-Turn Intent Refinement
- Intent is refined across multiple turns
- Allows clarification without restarting conversation

---

## Module 3: Challan Calculator

### F3.1 — Fine Calculation Engine
- DuckDB SQL with LEFT JOIN: national fines + state overrides
- `COALESCE(state_overrides.override_fine, violations.base_fine_inr)`
- 22+ MVA sections, 5 vehicle types: 2-Wheeler, LMV, Auto, Commercial, Bus
- Online: `GET /api/v1/challan/calculate`
- Offline: DuckDB-Wasm in browser against cached `violations.csv`

### F3.2 — MVA AI Assistant
- RAG grounded in full MV Act text — section numbers always in answer
- Common queries: speed limits, BAC limits, documents required, helmet rules

---

## Module 4: RoadWatch Reporter

### F4.1 — Geotagged Issue Reporting
- Issue types: pothole, flooding, broken road, accident-prone zone, missing signage, no lighting
- Severity: 1 (minor crack) to 5 (road impassable)
- GPS mandatory, auto-filled; photo optional

### F4.2 — Automatic Authority Routing
- Overpass API identifies `highway` OSM tag at report GPS coordinates
- Deterministic routing: NH ? NHAI, SH ? State PWD, MDR ? District Collector, village ? PMGSY, urban ? Municipal Corporation

### F4.3 — Road Infrastructure Transparency
- Shows: contractor name, budget sanctioned/spent, exec engineer + phone, last relayed date, next maintenance
- Sources: data.gov.in NHAI + PMGSY OMMAS

### F4.4 — Community Issues Map Layer
- Toggle: shows all open/acknowledged road issues near user
- Yellow = open, Orange = acknowledged, Grey = resolved

---

## Module 5: Safety & Authentication

### F5.1 — Safety Checker (Prompt Injection Defense)
- 12-pattern guard in SafetyChecker blocks harmful queries
- Always prepends "Call 112 immediately" for injury queries
- Intent detection runs before RAG

### F5.2 — Authentication (JWT + Service Auth)
- JWT Bearer tokens (HS256) with 24h access, 30d refresh
- Supabase JWT validation
- Guest auth (anonymous UUID-based)
- Service-to-service auth via `X-Internal-Api-Key`
- AuthGuard bypass via `localStorage.__E2E_SKIP_AUTH__`

### F5.3 — Circuit Breakers
- Prevents cascading failures across service calls
- Automatic retry with exponential backoff

---

## Module 6: Offline Capabilities

### F6.1 — Offline SOS Queue
- SOS queued to IndexedDB when offline
- Auto-flushed on `online` event via `offline-sos-queue.ts`

### F6.2 — WebLLM Offline AI
- Phi-3 Mini (2.2GB) downloads on-demand via `@mlc-ai/web-llm`
- WebGPU primary, WebAssembly CPU fallback

### F6.3 — PWA Share Target
- Registers as a share target in the OS share sheet
- Accepts URLs, text, and files

---

## Module 7: Integration Features

### F7.1 — What3Words Integration
- 3-meter precision location resolution
- Accepts `///word.word.word` format
- Used in emergency dispatch context

### F7.2 — Voice/ASR (IndicSeamless, 14 Languages)
- `POST /speech/translate` — Indian language speech translation
- `GET /speech/status` — service health
- 14+ Indian languages supported

### F7.3 — Indian Language Detection
- Regex-based Unicode script range detection
- No NLTK dependency
- Maps to 4-code system for speech pipeline

### F7.4 — Waze CIFS Feed
- Full CIFS spec compliance (Closure and Incident Feed Specification)
- Maps RoadWatch issue types to CIFS types (HAZARD_ON_ROAD, ACCIDENT, ROAD_CLOSED, CONSTRUCTION)
- Waze polls every 2 minutes

### F7.5 — MCP Server
- `backend/api/v1/mcp_server.py` — exposes tools for external AI agents
- MCP-compatible agents can query emergency services, submit reports, calculate fines

### F7.6 — QR Emergency Card
- Route: `/emergency-card/[userId]`
- QR code with user's emergency info
- Accessible without login

### F7.7 — Speech Language Mapping (4-code system)
- `lib/languages.ts` — 14 languages with 4-code mapping
- UI code ? recognitionCode ? speechTargetCode ? synthesisCode

### F7.8 — GSAP Animations
- Page entry transitions via `usePageEntry.ts`
- GSAP-powered animations with try-catch to prevent hydration blocking
- Used across 28 routes

### F7.9 — Assistant Voice Output
- SpeechSynthesis for bot responses
- Language-matched voice selection

### F7.10 — Family Live Tracking (WebSocket)
- Route: `/track/[sessionId]`
- Backend: `live_tracking` table with WebSocket updates
- GPS updates every 5 seconds
- Family sees: live map, speed, battery %, blood group, vehicle number
- Auto-expires after 4 hours

---

*Document version: 2.0 | AI-powered road safety platform | Updated: June 2026*
