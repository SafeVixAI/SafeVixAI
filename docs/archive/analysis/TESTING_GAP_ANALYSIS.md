# SafeVixAI — Testing Gap Analysis

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

> Generated: 2026-05-22 | Coverage gaps, risk-based priorities, recommendations

---

## 1. Coverage Summary

| Service | Test Files | Tests Passing | Coverage % | Framework | CI Integration |
|---------|-----------|---------------|-----------|-----------|---------------|
| Backend | 32+ | 1365/1365 | ~85% core, unknown services | pytest (asyncio_mode=auto) | ✅ backend.yml |
| Chatbot | 20+ | 892/892 | Unknown | pytest (asyncio_mode=strict) | ✅ chatbot.yml |
| Frontend | 12+ | Unknown | Unknown | Jest + Playwright | ✅ frontend.yml |
| End-to-End | 6+ e2e files | 45/55 | N/A | Playwright | ✅ e2e.yml |

---

## 2. Critical Gaps (Blocking CI / Production)

### GAP-1: Load Test Scripts Missing
**Files:** `tests/load/backend_api_load.js`, `tests/load/chatbot_api_load.js`, `tests/load/frontend_load.js`
**Workflow:** `.github/workflows/load-testing.yml` references these files
**Impact:** `load-testing.yml` will fail at runtime. Cannot validate performance under load.
**Fix:** Create k6 scripts or remove workflow. Priority: HIGH.

### GAP-2: Chaos Test Script Missing
**File:** `tests/test_chaos.py`
**Workflow:** `.github/workflows/chaos-tests.yml` references this file
**Impact:** `chaos-tests.yml` will fail at runtime. Cannot validate circuit breaker and failure recovery.
**Fix:** Create chaos test or remove workflow. Priority: HIGH.

### GAP-3: No Cross-Service Integration Tests
**Testing gap:** No test validates the full frontend → backend → chatbot pipeline
**Critical flows untested:**
- Chat message → Backend proxy → Chatbot → LLM call → Backend → Frontend SSE
- Frontend SOS → Backend API → EmergencyLocator → PostGIS/Overpass
- Chatbot tool call → Backend API (Challan/SOS/Road)
**Risk:** Changes in one service can break another without detection.
**Fix:** Add integration test that spins up all 3 services and tests the pipeline. Priority: HIGH.

---

## 3. High-Priority Gaps

### GAP-4: No Database Migration Tests
**Testing gap:** Alembic migrations are never tested against a fresh or existing database.
**Risk:** Migration errors discovered only during deployment.
**Fix:** Add pytest fixtures that apply all migrations to a test database. Priority: HIGH.

### GAP-5: No SOS End-to-End Flow Test
**Testing gap:** No test covers the complete SOS flow:
- Frontend SOS button → Double-tap → API call → Backend SOS → Emergency services → SMS share
- Offline SOS → IndexedDB queue → Online sync → API flush
**Partial coverage:** Chatbot has `test_emergency_tool.py`, frontend has `SOSButton.test.tsx`
**Fix:** Add E2E test for full SOS flow. Priority: HIGH.

### GAP-6: No Security Integration Tests
**Testing gap:** No tests verify:
- CSRF protection blocks forged requests
- Rate limiting triggers correctly
- JWT with wrong audience/issuer is rejected
- Prompt injection bypass attempts are blocked (chatbot tests cover this partially)
- Admin endpoints reject wrong keys
- CORS blocks disallowed origins
**Partial coverage:** Backend `test_security.py` and `test_csrf.py` exist
**Fix:** Add comprehensive security integration tests. Priority: HIGH.

### GAP-7: No Prometheus Metrics Tests
**Testing gap:** 18+ metrics are defined in `backend/core/metrics.py` but no tests verify:
- Metrics are incremented on correct triggers
- Metrics have correct labels
- `/metrics` endpoint returns valid Prometheus format
**Fix:** Add metrics endpoint + tests. Priority: HIGH.

---

## 4. Medium-Priority Gaps

### GAP-8: No PWA-Specific Tests
**Gaps:**
- Manifest validation (icons, shortcuts, share_target)
- Service Worker install/activate/fetch lifecycle
- Cache strategies (cache-first vs network-first behavior)
- Background Sync registration and execution
- Push notification handling
**Partial coverage:** Frontend `offline.spec.ts` tests SW registration
**Fix:** Add PWA-specific E2E tests. Priority: MEDIUM.

### GAP-9: No WebSocket Stress Tests
**Gaps:**
- Multiple concurrent connections
- Reconnection after disconnect
- Message throughput under load
- Redis Pub/Sub multi-instance broadcast
- Origin validation
- Message size limits
**Partial coverage:** Backend `test_live_tracking.py` tests basic lifecycle
**Fix:** Add WebSocket stress tests with concurrent clients. Priority: MEDIUM.

### GAP-10: No Performance/Lighthouse Tests
**Gaps:**
- LCP, CLS, TTI measurements
- Bundle size analysis
- Memory usage tracking
- Animation frame rate (GSAP)
- Map rendering performance
**Fix:** Add Lighthouse CI to frontend.yml. Priority: MEDIUM.

### GAP-11: No Accessibility Violation Thresholds
**Gaps:**
- `tests/a11y/` directory exists but no automated threshold assertions
- No CI integration for accessibility regression
**Fix:** Add axe-core assertions with max-violation thresholds. Priority: MEDIUM.

### GAP-12: No Disaster Recovery Tests
**Gaps:**
- Database restore from backup
- Cache population after Redis flush
- Session recovery after service restart
- Circuit breaker recovery sequence
**Fix:** Add DR validation tests. Priority: MEDIUM.

---

## 5. Low-Priority Gaps

### GAP-13: No Fuzzing/DAST Testing
**Fix:** Add OWASP ZAP or API fuzzing to security workflow. Priority: LOW.

### GAP-14: No Mutation Testing
**Fix:** Add mutation testing (e.g., mutmut for Python). Priority: LOW.

### GAP-15: No Visual Regression Thresholds
Frontend visual tests exist but no automated diff thresholds. Priority: LOW.

### GAP-16: No Speech Recognition Tests
IndicSeamlessService has `test_speech_translation.py` but no ASR accuracy tests. Priority: LOW.

---

## 6. Test Quality Assessment

### Backend Test Quality
| Aspect | Rating | Notes |
|--------|--------|-------|
| Unit tests | ⭐⭐⭐⭐ | Core infrastructure well-tested (circuit breaker, cache, idempotency, etc.) |
| Service tests | ⭐⭐⭐ | Emergency, routing, challan, geocoding — good coverage |
| API tests | ⭐⭐⭐ | Auth, offline, emergency, MCP, Waze, tracking — solid |
| Integration tests | ⭐⭐ | Missing cross-service integration |
| Security tests | ⭐⭐ | CSRF + security tests exist but limited |
| Performance tests | ⭐ | Load test scripts missing |
| Async pattern | ✅ | asyncio_mode=auto (correct) |
| Fixtures | ✅ | Good patterns (DummySession, auth_headers, env overrides) |

### Chatbot Test Quality
| Aspect | Rating | Notes |
|--------|--------|-------|
| Unit tests | ⭐⭐⭐⭐ | All 9 intents, safety checker, provider routing well-tested |
| Service tests | ⭐⭐⭐ | Context assembler, tools, memory — good coverage |
| Integration tests | ⭐⭐⭐ | Chat engine integration with fakes |
| Security tests | ⭐⭐⭐⭐ | Prompt injection, jailbreak, l33t, unicode — comprehensive |
| Edge cases | ⭐⭐⭐ | Timeout handling, empty results, rate limiting, fallback chain |
| Performance tests | ⭐ | No load tests |
| Async pattern | ✅ | asyncio_mode=strict with @pytest.mark.asyncio (correct) |
| Fixtures | ⭐⭐⭐⭐ | Excellent Fake* class patterns |

### Frontend Test Quality
| Aspect | Rating | Notes |
|--------|--------|-------|
| Component tests | ⭐⭐⭐ | 12 component tests covering key interfaces |
| Hook tests | ⭐⭐ | useSOS excluded from Jest (Playwright covers) |
| E2E tests | ⭐⭐⭐ | SOS, offline, visual regression, responsive |
| PWA tests | ⭐⭐ | SW registration tested, but not manifest or install |
| Accessibility | ⭐⭐ | Tests exist but no thresholds |
| Performance | ⭐ | No Lighthouse/Web Vitals tests |

---

## 7. Risk-Based Testing Priorities

```
┌────────────────────────────────────────────────────────────────┐
│                    TESTING PRIORITY MATRIX                      │
├──────────┬──────────────┬──────────────┬───────────────────────┤
│ Risk     │ Not Tested   │ Partially    │ Well Tested           │
├──────────┼──────────────┼──────────────┼───────────────────────┤
│ CRITICAL │ Cross-service│ SOS flow     │ Safety Checker        │
│          │ integration  │              │                       │
├──────────┼──────────────┼──────────────┼───────────────────────┤
│ HIGH     │ Load/Perf    │ DB migrations│ Provider Router       │
│          │ Security E2E │ WebSocket    │ Emergency Locator      │
│          │ Metrics      │ Auth flows   │ Prompt Injection       │
├──────────┼──────────────┼──────────────┼───────────────────────┤
│ MEDIUM   │ PWA/Manifest │ Offline AI   │ Circuit Breaker       │
│          │ Accessibility│ Service Worker│ Cache/Idempotency    │
│          │ Speech       │ Visual       │ Intent Detection      │
├──────────┼──────────────┼──────────────┼───────────────────────┤
│ LOW      │ Mutation     │ Component    │ API Endpoints         │
│          │ DAST/Fuzzing │ Storybook    │ ORM/Models            │
└──────────┴──────────────┴──────────────┴───────────────────────┘
```

---

## 8. Recommended Test Additions

### Immediate (Week 1)
```python
# 1. Cross-Service Integration Test (backend → chatbot)
async def test_chatbot_via_backend_proxy():
    # POST /api/v1/chat/ on backend → proxies to chatbot
    # Verify response contains expected fields
    pass

# 2. Metrics Exposure Test (backend)
async def test_metrics_endpoint():
    # GET /metrics → valid Prometheus format
    pass

# 3. SOS E2E Flow
async def test_sos_full_flow():
    # Frontend SOS button → Backend API → Family tracking → SMS
    pass
```

### Short-Term (Week 2)
```python
# 4. DB Migration Test
async def test_all_migrations():
    # Apply all alembic migrations to fresh DB
    # Verify all tables created with correct schema
    pass

# 5. RBAC Enforcement Test
async def test_role_enforcement():
    # JWT with wrong role → 403 on sensitive endpoint
    pass

# 6. WebSocket Concurrent Stress Test
async def test_websocket_multiple_clients():
    # 50 concurrent WebSocket connections
    # Verify all receive broadcasts
    pass
```

### Medium-Term (Month 1)
```python
# 7. PWA Manifest Test
def test_manifest():
    # Verify manifest.json contains all required fields
    pass

# 8. Service Worker Cache Strategy Test
def test_sw_cache_strategies():
    # Verify cache-first for offline data
    # Verify network-first for API calls
    pass

# 9. Lighthouse Performance Test
test('Lighthouse scores above thresholds', () => {
    // LCP <= 2500ms, CLS <= 0.1, TBT <= 200ms
})
```

---

## 9. Test Infrastructure Improvements

| Improvement | Current State | Target | Effort |
|------------|--------------|--------|--------|
| Coverage reporting | XML artifacts in CI | PR comments with diff coverage | 1 day |
| Test parallelization | Sequential pytest | pytest-xdist | 2 hours |
| Test data factories | Manual fixtures | Factory Boy / Faker | 2 days |
| API contract testing | Basic spec generation | OpenAPI + Pact | 3 days |
| Visual regression | Playwright screenshots | Percy / Chromatic | 2 days |
| Mutation testing | None | mutmut for Python | 2 days |
