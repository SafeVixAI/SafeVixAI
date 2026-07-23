# Introduction and Purpose

<cite>
**Referenced Files in This Document**
- [README.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/README.md)
- [DESIGN.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/DESIGN.md)
- [docs/PRD.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/PRD.md)
- [docs/Features.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Features.md)
- [docs/Architecture.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md)
- [docs/Database.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Database.md)
- [docs/Deployment.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Deployment.md)
- [docs/Contributing.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Contributing.md)
- [SETUP.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/SETUP.md)
- [backend/main.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/main.py)
- [backend/api/v1/emergency.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/api/v1/emergency.py)
- [backend/api/v1/challan.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/api/v1/challan.py)
- [backend/api/v1/roadwatch.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/api/v1/roadwatch.py)
- [chatbot_service/main.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py)
- [frontend/app/page.tsx](https://github.com/SafeVixAI/SafeVixAI/blob/main/frontend/app/page.tsx)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
SafeVixAI is an AI-powered road safety platform designed to address three critical road safety challenges in India: emergency response, legal assistance, and road infrastructure reporting. Built for the AI-powered road safety platform, the platform integrates a tactical, life-safety-focused UI with robust backend services, an agentic RAG chatbot, and a fully capable frontend PWA. Its mission is to reduce road accident mortality by dramatically improving response times, legal literacy, and transparency around road maintenance.

Key pillars:
- Zero infrastructure cost: 100% free and open source, leveraging free-tier cloud services and browser-based AI.
- Tactical UX: A dark, high-contrast, terminal-inspired interface optimized for emergency and operational tasks.
- Offline-first: Five independent offline layers ensure core features remain functional without connectivity.
- Open-source and community-driven: Transparent development, modular architecture, and contribution guidelines to foster collaboration.

Impact:
- Emergency response: Instant, accurate, and resilient emergency locator with SOS sharing and crash detection.
- Legal assistance: Deterministic challan calculator and a multilingual legal assistant grounded in the Motor Vehicles Act and WHO guidelines.
- Road infrastructure reporting: Intuitive, geotagged reporting with automatic authority routing and transparency into maintenance records.

Scalability:
- Modular microservices architecture supports independent scaling of backend, chatbot, and frontend.
- Free-tier deployment model demonstrates replicability across regions and contexts.
- Community-driven governance and documentation accelerate adoption and contributions.

**Section sources**
- [README.md:1-152](https://github.com/SafeVixAI/SafeVixAI/blob/main/README.md#L1-L152)
- [docs/PRD.md:1-118](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/PRD.md#L1-L118)
- [DESIGN.md:13-31](https://github.com/SafeVixAI/SafeVixAI/blob/main/DESIGN.md#L13-L31)

## Project Structure
SafeVixAI is organized as a three-service monorepo:
- Backend (FastAPI + PostGIS + Redis): Emergency locator, challan calculator, road reporting, routing, and geocoding.
- Chatbot Service (FastAPI + ChromaDB + 9 LLM providers): Agentic RAG chatbot with intent detection, safety checks, and multilingual routing.
- Frontend (Next.js 15 PWA): Map-centric UI with offline AI, crash detection, and emergency workflows.

```mermaid
graph TB
subgraph "Frontend (Next.js 15)"
FE["PWA Dashboard<br/>Map + Controls"]
end
subgraph "Backend (FastAPI)"
BE["Emergency Locator<br/>Challan Calculator<br/>RoadWatch"]
end
subgraph "Chatbot Service (FastAPI)"
CB["Agentic RAG Chatbot<br/>Intent Detection + Tools"]
end
subgraph "Infrastructure"
DB["PostgreSQL + PostGIS (Supabase)"]
RC["Redis (Upstash)"]
CDN["local model files (WebLLM weights)"]
end
FE --> BE
FE --> CB
BE --> DB
BE --> RC
CB --> DB
CB --> RC
FE --> CDN
```

**Diagram sources**
- [docs/Architecture.md:5-46](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L5-L46)
- [docs/Architecture.md:49-60](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L49-L60)

**Section sources**
- [docs/Architecture.md:208-224](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L208-L224)
- [docs/Deployment.md:3-16](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Deployment.md#L3-L16)

## Core Components
SafeVixAI’s modules are engineered to deliver immediate value in high-stakes scenarios:

- Emergency Locator (SafeVixAI Core)
  - GPS auto-detection, tiered radius fallback, SOS WhatsApp share, crash detection, offline emergency map, and first aid guidance.
  - Ensures responders reach victims within the critical first 10 minutes.

- AI Chatbot (DriveLegal + RoadWatch)
  - 9-class intent detection, online RAG with 9-provider fallback, offline WebLLM Phi-3 Mini, multilingual support, and voice I/O.
  - Provides legal answers grounded in the Motor Vehicles Act and WHO guidelines.

- Challan Calculator (DriveLegal)
  - Deterministic MVA 2019 fine calculation with state overrides, offline via DuckDB-Wasm, and citation of legal sections.

- Road Reporter (RoadWatch)
  - Geotagged reporting with severity, in-browser YOLOv8 pothole detection, automatic authority routing, and offline queue with background sync.

**Section sources**
- [docs/Features.md:3-54](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Features.md#L3-L54)
- [docs/Features.md:57-104](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Features.md#L57-L104)
- [docs/Features.md:106-122](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Features.md#L106-L122)
- [docs/Features.md:125-155](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Features.md#L125-L155)
- [docs/PRD.md:7-14](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/PRD.md#L7-L14)

## Architecture Overview
SafeVixAI employs a dual-layer AI architecture: online RAG with multi-provider fallback and a five-layer offline stack. The system is intentionally modular to maximize resilience and scalability.

```mermaid
flowchart TD
A["User Device"] --> B["Frontend PWA"]
B --> C["Backend API :8000"]
B --> D["Chatbot Service :8010"]
C --> C1["PostGIS + Overpass"]
C --> C2["DuckDB SQL"]
C --> C3["Authority Routing Matrix"]
D --> D1["IntentDetector"]
D --> D2["ContextAssembler"]
D --> D3["ChromaDB RAG"]
D --> D4["ProviderRouter (9 LLMs)"]
D --> D5["Sarvam AI (Indic)"]
B --> E["Offline Layer"]
E --> E1["WebLLM Phi-3 Mini"]
E --> E2["DuckDB-Wasm"]
E --> E3["HNSWlib.js + IndexedDB"]
E --> E4["GeoJSON + Turf.js"]
E --> E5["Service Worker + Background Sync"]
```

**Diagram sources**
- [docs/Architecture.md:67-91](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L67-L91)
- [docs/Architecture.md:128-137](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L128-L137)

**Section sources**
- [docs/Architecture.md:63-102](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L63-L102)
- [docs/Architecture.md:128-137](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L128-L137)

## Detailed Component Analysis

### Emergency Locator: Real-Time Response and Resilience
The Emergency Locator module powers instant, accurate emergency service discovery with offline resilience and crash detection.

```mermaid
sequenceDiagram
participant U as "User"
participant FE as "Frontend"
participant API as "Backend : 8000"
participant R as "Redis Cache"
participant DB as "PostGIS DB"
participant OP as "Overpass API"
U->>FE : "Enable GPS / View nearby services"
FE->>API : "GET /api/v1/emergency/nearby?lat&lon"
API->>R : "Check cache"
alt "Cache hit"
R-->>API : "Cached results"
else "Cache miss"
API->>DB : "ST_DWithin query (radius 5km)"
DB-->>API : "Nearby services"
API->>API : "Expand radius if < 3 results"
API->>OP : "Fallback via Overpass"
OP-->>API : "Additional POIs"
API->>R : "Cache results"
end
API-->>FE : "EmergencyResponse"
FE-->>U : "Map markers + service cards"
```

Practical example:
- Scenario: A car crashes on a remote highway with poor cell reception.
- Outcome: The app’s crash detection triggers an SOS with pre-filled GPS and emergency contacts, while the offline emergency map displays the nearest hospital and police station using cached GeoJSON and Turf.js.

**Diagram sources**
- [docs/Architecture.md:141-165](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L141-L165)
- [backend/api/v1/emergency.py:19-40](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/api/v1/emergency.py#L19-L40)

**Section sources**
- [docs/Features.md:3-54](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Features.md#L3-L54)
- [backend/api/v1/emergency.py:19-76](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/api/v1/emergency.py#L19-L76)
- [frontend/app/page.tsx:77-228](https://github.com/SafeVixAI/SafeVixAI/blob/main/frontend/app/page.tsx#L77-L228)

### AI Chatbot: Legal Grounding and Multilingual Assistance
The chatbot combines intent detection, RAG, and a 9-provider fallback chain to deliver accurate, contextual responses.

```mermaid
sequenceDiagram
participant U as "User"
participant FE as "Frontend"
participant CS as "Chatbot : 8010"
participant PR as "ProviderRouter"
participant C as "ChromaDB"
participant R as "Redis"
participant BE as "Backend : 8000"
U->>FE : "Message (voice/text)"
FE->>CS : "POST /api/v1/chat/"
CS->>CS : "SafetyChecker + IntentDetector"
CS->>CS : "ContextAssembler"
alt "Legal intent"
CS->>C : "Vector search (top-5 chunks)"
C-->>CS : "Relevant law text"
else "Emergency intent"
CS->>BE : "Call /api/v1/emergency/nearby"
BE-->>CS : "Nearby services"
end
CS->>R : "Load conversation history"
R-->>CS : "Previous messages"
CS->>PR : "Generate with provider chain"
PR-->>CS : "Response"
CS->>R : "Persist updated history"
CS-->>FE : "Formatted response"
FE-->>U : "Display answer + citations"
```

Practical example:
- Scenario: A driver receives a challan and is unsure about the fine amount and legal section.
- Outcome: The chatbot calculates the exact fine using DuckDB SQL and cites the relevant MVA section, enabling informed legal action.

**Diagram sources**
- [docs/Architecture.md:169-204](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L169-L204)
- [chatbot_service/main.py:106-142](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py#L106-L142)

**Section sources**
- [docs/Features.md:57-104](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Features.md#L57-L104)
- [chatbot_service/main.py:41-93](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py#L41-L93)

### Challan Calculator: Deterministic Legal Compliance
Deterministic calculations grounded in the Motor Vehicles Act ensure clarity and fairness.

```mermaid
flowchart TD
A["User submits violation_code, vehicle_class, state_code, repeat flag"] --> B["Backend validates payload"]
B --> C["DuckDB SQL join: national base fines + state overrides"]
C --> D{"Repeat offender?"}
D --> |Yes| E["Apply repeat_fine_inr"]
D --> |No| F["Use base_fine_inr"]
E --> G["Return ChallanResponse with citation"]
F --> G
```

Practical example:
- Scenario: A Tamil Nadu resident is charged under MVA_185 for drunk driving in a commercial vehicle.
- Outcome: The calculator returns the exact fine amount, the legal section cited, and state-specific adjustments.

**Diagram sources**
- [docs/Architecture.md:93-102](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L93-L102)
- [backend/api/v1/challan.py:17-26](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/api/v1/challan.py#L17-L26)

**Section sources**
- [docs/Features.md:106-122](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Features.md#L106-L122)
- [backend/api/v1/challan.py:17-26](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/api/v1/challan.py#L17-L26)

### Road Reporter: Transparent Infrastructure Accountability
The Road Reporter module enables citizens to report road issues with automatic authority routing and transparency into maintenance records.

```mermaid
flowchart TD
A["User captures GPS + photo + selects severity"] --> B["Submit report to Backend"]
B --> C["Overpass API identifies highway tag at GPS"]
C --> D["Authority routing matrix selects responsible agency"]
D --> E["Store in DB + return RoadReportResponse"]
E --> F["Optional: Offline queue + Background Sync"]
F --> G["Community issues map layer"]
```

Practical example:
- Scenario: A pothole on a state highway causes repeated damage to vehicles.
- Outcome: The report is routed to the appropriate PWD office with transparency into budget and maintenance history, and nearby users receive warnings.

**Diagram sources**
- [docs/Architecture.md:128-137](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L128-L137)
- [backend/api/v1/roadwatch.py:73-97](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/api/v1/roadwatch.py#L73-L97)

**Section sources**
- [docs/Features.md:125-155](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Features.md#L125-L155)
- [backend/api/v1/roadwatch.py:26-97](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/api/v1/roadwatch.py#L26-L97)

### Conceptual Overview
SafeVixAI’s conceptual design emphasizes a “life-safety command terminal” with two operational modes: Tactical Emergency (seconds count) and Operational Normal (research, compliance, reporting). The UI’s dark tactical palette, terminal aesthetics, and high-contrast typography reinforce urgency and clarity.

```mermaid
flowchart TD
A["User enters SafeVixAI"] --> B{"Task type?"}
B --> |Emergency| C["Tactical Emergency Mode"]
B --> |Legal/Challan| D["Operational Normal Mode"]
B --> |Report/Map| E["Operational Normal Mode"]
C --> F["SOS + Crash Detection + First Aid"]
D --> G["Challan Calculator + Legal Assistant"]
E --> H["Road Reporter + Authority Routing"]
```

[No sources needed since this diagram shows conceptual workflow, not actual code structure]

**Section sources**
- [DESIGN.md:13-31](https://github.com/SafeVixAI/SafeVixAI/blob/main/DESIGN.md#L13-L31)
- [DESIGN.md:367-555](https://github.com/SafeVixAI/SafeVixAI/blob/main/DESIGN.md#L367-L555)

## Dependency Analysis
SafeVixAI’s backend, chatbot, and frontend services depend on shared infrastructure and external datasets. The backend relies on PostGIS for spatial queries, Redis for caching, and Overpass/Nominatim for POI enrichment. The chatbot leverages ChromaDB for RAG and a 9-provider LLM fallback chain. The frontend consumes these services via HTTPS and operates offline through browser-based AI and cached assets.

```mermaid
graph TB
FE["Frontend"] --> BE["Backend API"]
FE --> CS["Chatbot Service"]
BE --> PG["PostgreSQL + PostGIS"]
BE --> RD["Redis"]
BE --> OS["Overpass/Nominatim"]
CS --> CH["ChromaDB"]
CS --> LL["9 LLM Providers"]
FE --> HF["local model files (WebLLM)"]
```

**Diagram sources**
- [docs/Architecture.md:49-60](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L49-L60)
- [docs/Architecture.md:40-45](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L40-L45)

**Section sources**
- [docs/Architecture.md:49-60](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L49-L60)
- [docs/Database.md:1-18](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Database.md#L1-L18)

## Performance Considerations
- Backend performance: PostGIS spatial queries (< 50 ms) with GIST indexing and Redis caching minimize latency for emergency services discovery.
- Offline performance: Five-layer offline stack ensures first-load functionality and minimal bandwidth usage.
- Chatbot performance: ProviderRouter auto-selects optimal LLMs; Sarvam AI handles Indian languages; fallback chain maintains reliability.
- Frontend performance: PWA with Service Worker caching, dynamic map loading, and offline AI reduces cold start and improves responsiveness.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Backend health: Verify the health endpoint to confirm database and cache availability.
- API testing: Use curl to test emergency and challan endpoints locally or in production.
- Environment variables: Ensure all keys are configured in .env files and reflected in deployment dashboards.
- Offline verification: Build and start the frontend in production mode, then simulate offline mode to confirm cached features.

**Section sources**
- [backend/main.py:103-125](https://github.com/SafeVixAI/SafeVixAI/blob/main/backend/main.py#L103-L125)
- [docs/Deployment.md:230-248](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Deployment.md#L230-L248)
- [SETUP.md:316-343](https://github.com/SafeVixAI/SafeVixAI/blob/main/SETUP.md#L316-L343)

## Conclusion
SafeVixAI advances road safety in India by combining tactical UX, AI-driven legal assistance, and transparent infrastructure reporting—without any infrastructure cost. Its modular architecture, offline-first design, and open-source philosophy enable rapid deployment, community-driven improvements, and scalable impact across diverse geographies and languages.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### initial context and Commitment
- Built for the AI-powered road safety platform.
- Total infrastructure cost: Rs. 0 using free-tier services and open-source stacks.

**Section sources**
- [README.md:5-6](https://github.com/SafeVixAI/SafeVixAI/blob/main/README.md#L5-L6)
- [docs/PRD.md:14](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/PRD.md#L14)

### Open-Source Philosophy and Community Approach
- Free-tier deployment model demonstrates replicability and sustainability.
- Comprehensive documentation, contribution guidelines, and CI/CD workflows encourage collaboration.
- Modular services and standardized tooling lower barriers to entry for contributors.

**Section sources**
- [docs/Deployment.md:3-16](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Deployment.md#L3-L16)
- [docs/Contributing.md:1-208](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Contributing.md#L1-L208)
- [docs/Architecture.md:49-60](https://github.com/SafeVixAI/SafeVixAI/blob/main/docs/Architecture.md#L49-L60)