# Backend Coverage Implementation Plan

## Current Status
- **Tests:** 1365/1365 passing (backend)
- **Coverage targets already met:**
  - local_emergency_catalog: **97%**
  - roadwatch: **90%+**
  - geocoding: **100%**
  - services/emergency_locator: **99%**
- **Combined total (all services):** 2829 unit tests (backend 1365 + chatbot 892 + frontend 572)
- **E2E tests:** 45/55 passing

**Status: ALL TARGETS ACHIEVED** ✅

---

## Phase 1 Targets — All Met
| Target Module | Target Coverage | Achieved |
|---------------|----------------|----------|
| local_emergency_catalog | 90%+ | **97%** |
| roadwatch | 90%+ | **90%+** |
| geocoding | 100% | **100%** |
| services/emergency_locator | 90%+ | **99%** |
| Overall | 90%+ | **Achieved** |

---

## Success Metrics

| Metric | Current |
|--------|---------|
| Overall Backend Coverage | 90%+ |
| Test Count (Backend) | 1365 |
| Total Unit Tests | 2829 |
| CI Pass Rate | 100% |
| Backend Lint | 0 errors |
| Frontend Lint | 0 warnings |

---

## Key Coverage Achievements

### High-Coverage Modules
- **Geocoding Service**: 100% — full Photon, BigDataCloud, Nominatim fallback coverage
- **Local Emergency Catalog**: 97% — catalog loading, search, filtering, edge cases
- **Emergency Locator**: 99% — Haversine, radius stepping, cache, Overpass fallback
- **Challan Service**: 90%+ — state overrides, vehicle multipliers, repeat offenders

### API Route Coverage
| Route Module | Coverage |
|---|---|
| Emergency API | 90%+ |
| Challan API | 90%+ |
| RoadWatch API | 90%+ |
| MCP Server API | 85%+ |
| Live Tracking API | 85%+ |
| Waze Feed API | 85%+ |
| User API | 85%+ |

### Service Layer Coverage
| Service Module | Coverage |
|---|---|
| Geocoding | 100% |
| Emergency Locator | 99% |
| Local Emergency Catalog | 97% |
| Challan Service | 90%+ |
| RoadWatch Service | 90%+ |
| LLM Service | 90%+ |
| Routing Service | 75%+ |

### Core Module Coverage
| Core Module | Coverage |
|---|---|
| Redis Client | 85%+ |
| JWKS Client | 85%+ |
| Tenant Module | 90%+ |

---

## Chatbot Service Coverage
| Metric | Value |
|--------|-------|
| Overall Coverage | **95%** |
| Test Count | **892** |

---

## Notes

- All coverage targets from the original 90% plan have been achieved and exceeded
- Focus has moved to E2E tests (45/55 passing) and edge case hardening
- Remaining gap: 10 E2E tests related to form validation in production standalone build (React 19 RSC streaming event hydration)
- Live tracking E2E tests (2) need a WebSocket mock server
