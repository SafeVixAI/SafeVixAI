# SafeVixAI — Master Implementation Plan

> Generated: 2026-06-09 | Based on comprehensive analysis of all 3 services
> Sources: `docs/analysis/*.md` (10 documents), AGENTS.md

---

## System Summary

### Architecture
**3 services** — Frontend (Next.js 15 + React 19 PWA, Vercel), Backend (FastAPI + PostGIS, Render), Chatbot (FastAPI + 10 LLM providers, Render). Current target cost: ₹0 using free tiers.

### Current Test Status
| Service | Tests Passing | Coverage |
|---------|--------------|----------|
| Backend | 1365/1365 | 90%+ (local_emergency_catalog 97%, roadwatch 90%+, geocoding 100%, emergency_locator 99%) |
| Chatbot | 892/892 | 95% |
| Frontend | 572/572 | 0 lint warnings, 0 type errors |
| E2E | 45/55 | Visual regression excluded |
| **Total** | **2829** | |

### Critical Production Systems
1. **SOS/Emergency** — Multi-layered: button → double-tap → API → nearby services → family tracking → offline queue
2. **Chatbot Safety** — 7-layer defense: SafetyChecker → prompt injection → RAG trust boundary → token budget → provider check → Groq guard → HTML sanitization
3. **LLM Fallback** — 10 providers: Groq→Cerebras→Gemini→GitHub→NVIDIA→OpenRouter→Mistral→Together→Template
4. **Emergency Locator** — 3-tier: PostGIS DB → CSV catalog → Overpass API, radius stepping 500m→50km

### Features Completeness (25 Features)
| Status | Count | Details |
|--------|-------|---------|
| COMPLETE | 25 | Emergency Locator, Family Live Tracking, Challan Calculator, RoadWatch Reporter, AI Chatbot RAG, LLM Fallback Chain (10 providers), Offline SOS Queue, WebLLM Offline AI, What3Words, Voice/ASR, Indian Language Detection, PWA Share Target, QR Emergency Card, MCP Server, Waze CIFS Feed, Circuit Breakers, Streaming Chat, Conversation Summarization, Multi-Turn Intent Refinement, Safety Checker, GSAP Animations, Speech Language Mapping, Assistant Voice Output, Crash Detection (Accelerometer + CrashCountdown UI integrated), Authentication (Production JWT + Secure Service-to-Service Auth Bypass fully implemented) |
| PARTIAL | 0 | — |
| BROKEN | 0 | — |
| MISSING | 0 | — |

---

## Phase 1 — Security & Auth Hardening

**Status: COMPLETE ✅**
- [x] Implement RBAC Enforcement (backend/core/security.py, backend/core/rbac.py)
- [x] Add Chatbot API Authentication (chatbot_service/ — JWT verification shared between services)
- [x] Secure Offline SOS Queue (frontend/lib/offline-sos-queue.ts — no PII stored, only {lat, lon, timestamp, userId?})
- [x] Add JWT Refresh & Revocation (backend/core/security.py, backend/api/v1/auth.py)
- [x] Add Rate Limiting to All Endpoints (slowapi limiter.py)
- [x] Fix CSP to Allow Maps/CDN

**Key deliverables:**
- ALLOWED_HOSTS middleware (`backend/middleware/allowed_hosts.py`)
- Progressive Guest Auth (`frontend/lib/guest-auth.ts`)
- Static Mock Token Rejection enforced in security middleware
- AuthGuard E2E Bypass via `__E2E_SKIP_AUTH__` localStorage flag

---

## Phase 2 — Observability & Monitoring

**Status: COMPLETE ✅**
- [x] Expose Prometheus `/metrics` Endpoint (backend/core/metrics.py)
- [x] Add Prometheus Metrics to Chatbot Service
- [x] Set Up Grafana Dashboard
- [x] Add Structured Logging to All Shims

---

## Phase 3 — Testing & CI/CD Fixes

**Status: COMPLETE ✅**
- [x] Create Missing Load Test Scripts
- [x] Create Chaos Test Script
- [x] Add Cross-Service Integration Tests
- [x] Fix Frontend CI Silent Failures (ESLint and TypeScript checks are blocking steps)
- [x] Add SOS E2E Test
- [x] Add Security Integration Tests

---

## Phase 4 — Infrastructure Hardening

**Status: COMPLETE ✅**
- [x] Add SOS Data Retention Policy
- [x] Versioned Docker Images
- [x] Add Database Migration Tests
- [x] Add Referrer-Policy & Permissions-Policy Headers
- [x] Implement Data Deletion API

---

## Phase 5 — Performance Optimization

**Status: COMPLETE ✅**
- [x] True SSE Streaming from LLM Providers
- [x] Increase DB Connection Pool
- [x] Preconnect to Map Tile CDNs
- [x] Purge Unused CSS

---

## Phase 6 — Production-Readiness Polish

**Status: COMPLETE ✅**
- [x] Create Incident Response Runbooks
- [x] Add PWA-Specific E2E Tests
- [x] Add Accessibility Thresholds
- [x] Add Lighthouse Performance Budget

---

## Effort Estimates

| Phase | Tasks | Lines of Code | Estimated Time |
|-------|-------|---------------|---------------|
| Phase 1: Security | 6 tasks | ~400 | 2-3 days |
| Phase 2: Observability | 4 tasks | ~250 | 1-2 days |
| Phase 3: Testing | 6 tasks | ~800 | 3-4 days |
| Phase 4: Infra | 5 tasks | ~300 | 2-3 days |
| Phase 5: Performance | 4 tasks | ~200 | 1-2 days |
| Phase 6: Polish | 4 tasks | ~300 | 2-3 days |
| **Total** | **29 tasks** | **~2,250** | **11-17 days** |

---

## Risk-Adjusted Recommendations

### Do First (Highest ROI) — ALL COMPLETE
1. **1.1 RBAC** — Prevents auth bypass ✅
2. **1.2 Chatbot Auth** — Secures public endpoints ✅
3. **2.1 `/metrics`** — Unlocks observability ✅
4. **3.1 Load Tests** — Unblocks CI ✅
5. **1.3 Secure Offline Queue** — Protects user PII ✅

### Defer
- **5.1 True Streaming** — Complex provider integration, low user impact ✅ (Completed)
- **6.4 Lighthouse Budget** — Nice-to-have, won't block deployment ✅ (Completed)
- **4.2 Versioned Docker** — Needed only for multi-instance rollback ✅ (Completed)
