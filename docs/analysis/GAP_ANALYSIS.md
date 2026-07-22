# SafeVixAI — Gap Analysis (2026-05-26)

> **SNAPSHOT**: This document reflects the state as of 2026-05-26. For current state see [AGENTS.md](../../AGENTS.md).

> What was planned vs what's actually implemented. Verified from code, not audits.

---

## 1. Feature Completeness (25 Features)

| Status | Count | Details |
|--------|-------|---------|
| COMPLETE | 25 | Emergency Locator, Family Live Tracking, Challan Calculator, RoadWatch Reporter, AI Chatbot RAG, LLM Fallback Chain (10 providers), Offline SOS Queue, WebLLM Offline AI, What3Words, Voice/ASR, Indian Language Detection, PWA Share Target, QR Emergency Card, MCP Server, Waze CIFS Feed, Circuit Breakers, Streaming Chat, Conversation Summarization, Multi-Turn Intent Refinement, Safety Checker, GSAP Animations, Speech Language Mapping, Assistant Voice Output, Crash Detection (Accelerometer + CrashCountdown UI integrated), Authentication (Production JWT + Secure Service-to-Service Auth Bypass fully implemented) |
| PARTIAL | 0 | None — All items fully verified |
| BROKEN | 0 | — |
| MISSING | 0 | — |

---

## 2. Planned vs Actual

### 2.1 Backend Security

| Claimed Issue | Actual State | GAP |
|---------------|-------------|-----|
| `admin123` hardcoded | **NOT FOUND** — PBKDF2 + env vars | FALSE POSITIVE |
| `mock-jwt-token` accepted | **REJECTED** — REJECTED_STATIC_TOKENS set | FALSE POSITIVE |
| CORS wildcard | **BLOCKED** — config rejects '*' in production | FALSE POSITIVE |
| User profile ownership | Endpoints require auth but some lack user_id verification | **PARTIAL GAP: verify_profile_ownership** |
| Live tracking unauthenticated | **PROTECTED** — auth + signed JWT for view | NO GAP |
| SOS is GET not POST | **BOTH** — GET for lookup, POST for incident | NO GAP (design choice) |
| Waze feed broken | **FUNCTIONAL** — proper imports, valid SQL | NO GAP |
| JWT secret regenerated every restart | **ONLY IN DEV** — production requires env var | NO GAP |

### 2.2 Frontend

| Claimed Issue | Actual State | GAP |
|---------------|-------------|-----|
| Crash detection TOAST only | **PARTIAL** — EnterpriseClientAppHooks renders CrashCountdown; ClientAppHooks is orphaned | **VERIFIED: ClientAppHooks.tsx dead code** |
| Marcus Thorne/O Negative hardcoded | **NOT FOUND** in any frontend file | FALSE POSITIVE |
| SLOCALHOST fallbacks | Found in `lib/api.ts`, `lib/share.ts`, `lib/deep-link.ts` | **VERIFIED: 3 files with hardcoded URL fallbacks** |
| /assistant page blank on mobile | **NOT VERIFIED** — height calc depends on CSS | NEEDS RESPONSIVE TEST |

### 2.3 Chatbot

| Claimed Issue | Actual State | GAP |
|---------------|-------------|-----|
| RAG is lexical not ChromaDB | **CHROMADB + sentence-transformers**; lexical is fallback | FALSE POSITIVE |
| Report tool wrong field names | Uses `data=` not `json=`, field names match backend | **DESIGN CHOICE: form-encoded is intentional** |
| torch in requirements | **PRESENT** (2.12.0) but only for speech, graceful fallback | **VERIFIED: 800MB dep for optional feature** |
| Provider env names inconsistent | **CONSISTENT** — all follow PROVIDER_API_KEY pattern | NO GAP |

---

## 3. True Gaps (Verified from Code)

### CRITICAL (Fix Immediately)

| Gap | Location | Impact | Fix |
|-----|----------|--------|-----|
| **All 3 .env files committed with live credentials** | `backend/.env`, `chatbot_service/.env`, `frontend/.env` | Full credential exposure to all repo users | Rotate all keys, git filter .env from history |
| **SafetyChecker output check never called** | `chatbot_service/agent/safety_checker.py:234-255` | LLM responses not validated for harmful content | Add `check_output_safety()` call in ChatEngine |
| **Medical disclaimer never added** | `chatbot_service/agent/safety_checker.py:226-232` | Medical advice not disclaimed | Add `add_medical_disclaimer_if_needed()` after first aid responses |

### HIGH (Fix This Week)

| Gap | Location | Impact | Fix |
|-----|----------|--------|-----|
| **SWR used in 1 of 23 pages only** | `frontend/app/challan/page.tsx` | Missing caching, deduplication, revalidation | Convert Axios calls to SWR hooks |
| **Chatbot unauthenticated** | `chatbot_service/api/chat.py` | Anyone can send 20 msg/min | Add `X-Service-Token` or forward backend JWT |
| **Dead code: context_assembler 3 route methods** | `chatbot_service/agent/context_assembler.py:188-364` | Code bloat, confusion | Remove dead methods |
| **Dead tool: EmergencyTool unwired** | `chatbot_service/tools/emergency_tool.py` | Orphan feature | Wire into ContextAssembler or remove |
| **Media disclaimer never appended** | `chatbot_service/agent/safety_checker.py:226-232` | Medical advice without disclaimer | Wire into ChatEngine output |
| **Profile ownership not fully verified** | `backend/api/v1/user.py` | Potential PII access | Add user_id ownership check to all profile endpoints |

### MEDIUM

| Gap | Location | Impact | Fix |
|-----|----------|--------|-----|
| `safevixai.com` hardcoded in 16 hreflang URLs | `frontend/app/layout.tsx:69-84` | Wrong canonical URLs in production | Use `NEXT_PUBLIC_APP_URL` |
| `next-themes` installed but unused | `frontend/package.json` | Dead dependency 0.4.6 | Remove from package.json |
| Framer Motion orphaned in lockfile | `frontend/package-lock.json` | Dead dependency | Prune with `npm dedupe` |
| `@mlc-ai/web-llm` referenced in docs, missing from deps | `frontend/package.json` | Offline AI path unclear | Add to deps or remove from docs |
| Duplicated render.yaml | `chatbot_service/render.yaml` + root `render.yaml` | Configuration drift | Remove duplicate |
| ChromaDB sub-gitignore contradicts root | `chatbot_service/.gitignore` | Confusion for new devs | Remove chroma_db line from sub-gitignore |
| No Host header validation | `backend/main.py` | Host header injection | Add ALLOWED_HOSTS middleware |
| No data retention policies | `backend/migrations/10005_data_retention.py` exists but not enforced | SOS incidents persist forever | Enable retention cron job |

### LOW

| Gap | Location | Impact | Fix |
|-----|----------|--------|-----|
| `X-Admin-Key` header still allowed in CORS | `backend/main.py:400` | Dead legacy auth | Remove from allow_headers |
| `private _client` attribute access on cache | `backend/api/v1/tracking.py:269` | Fragile | Add public property |
| Harcoded audience/issuer strings | `backend/core/security.py:39-40` | Config hardening | Make env-configurable |
| Template provider confidence hardcoded to 0.3 | `chatbot_service/providers/router.py` | Always below 0.3 threshold | Make configurable |
| `pydantic-settings` in chatbot deps but unused | `chatbot_service/requirements.txt` | Dead dependency | Remove |
| `emergency` custom ease never registered | `frontend/lib/gsap.ts` | Custom ease name unused | Register on demand |

---

## 4. Testing Coverage Gaps

| Area | Current | Target | Gap |
|------|---------|--------|-----|
| Frontend unit tests | 572 passing | 500+ | MET |
| Backend pytest | 1365 passing | 1300+ | MET |
| Chatbot pytest | 892 passing | 800+ | MET |
| Backend coverage | 59% | 70% | **11% GAP** |
| Frontend coverage | ~30% (12 component tests) | 70% | **40% GAP** |
| E2E tests | Playwright configured, count unknown | All critical flows | **NEEDS AUDIT** |
| Crash detection tests | None found | 5+ P0 tests | **HIGH GAP** |
| SOS dispatch tests | None found | 5+ P0 tests | **HIGH GAP** |
| Auth security tests | Present in backend | All auth scenarios | PARTIAL |
| LLM fallback tests | Present in chatbot | All scenarios | PARTIAL |

---

## 5. UI/UX Gaps

| Gap | Details | Priority |
|-----|---------|----------|
| CrashCountdown orphaned in ClientAppHooks.tsx | Never imported; EnterpriseClientAppHooks renders it correctly | HIGH (documentation only) |
| Theme toggle not visible in UI | Dark/light switch exists in theme provider but no UI for it | LOW |
| No offline map tiles | MapLibre requires network; critical for locator page offline | MEDIUM |
| `@mlc-ai/web-llm` missing from frontend deps | Offline AI model cannot load | MEDIUM |
