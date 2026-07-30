# SafeVixAI — Security Risk Map

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

> Generated: 2026-05-22 | Full security audit with CVE tracking

---

## CRITICAL RISKS (Immediate Action Required)

### C1: No Role-Based Authorization Enforcement
**Files:** `backend/api/v1/*.py` (all routes use `get_current_user` but never check `role`)
**Impact:** Any authenticated user (including Supabase "authenticated" role) has full access to all user-facing endpoints. The JWT `role` claim is embedded but never checked.
**Evidence:**
- `PATCH /api/v1/roads/report/{id}/verify` — any authenticated user can verify road reports
- `POST /api/v1/chat/` + `/stream` — chatbot proxies accept any auth token
- User profile, tracking, SOS — no role scoping beyond user_id ownership
**Fix:** Implement `require_role(Role.OPERATOR)` decorator and apply to sensitive endpoints.

### C2: Offline SOS Queue Stores JWT + Medical PII in IndexedDB
**File:** `frontend/lib/offline-sos-queue.ts`
**Impact:** Auth tokens, blood group, and emergency contacts stored unencrypted in persistent browser storage. Accessible to any JS on the same origin.
**Data stored:** `{ lat, lon, authToken, userId, bloodGroup, emergencyContacts, timestamp }`
**Fix:** Remove sensitive fields from queue. Auth token should use refresh token pattern. Blood group should NOT leave device per project privacy claim.

---

## HIGH RISKS (Week 1)

### H1: No Rate Limiting on Many Endpoints
**Files:** Various backend route modules (geocoding, routing, user CRUD, live-tracking, authority)
**Impact:** Unlimited abuse potential — scraping, enumeration, DOS on unrate-limited endpoints.
**Endpoints without limits:** geocode search/reverse, routing preview/safe-route, user CRUD, live-tracking CRUD, feeds/waze, offline/bundle, authority, infrastructure.

### H2: No Data Deletion/Export APIs
**Impact:** GDPR non-compliance. User data (profile, SOS history, chat logs) cannot be deleted or exported programmatically.
**Fix:** Implement `DELETE /api/v1/users/{id}` and `GET /api/v1/users/{id}/export` endpoints.

### H3: SOS Incidents Persist Indefinitely
**File:** `backend/models/sos_incident.py`, no cleanup migration
**Impact:** Exact GPS coordinates + user_id of every SOS trigger stored forever. No data retention policy.
**Fix:** Add cleanup job (delete after 90 days) and migration.

### H4: Blood Group Sent to Server
**File:** `backend/models/schemas.py:283` (`UserProfileCreate.blood_group`)
**Impact:** Contradicts AGENTS.md privacy claim: "Blood group never leaves device — privacy by architecture." The `UserProfile` model and API both accept blood group, which is stored in the database.
**Fix:** Align docs with reality, or remove blood_group from server API.

### H5: Chatbot API Endpoints Unauthenticated
**Files:** `chatbot_service/api/chat.py` (`/api/v1/chat/`, `/api/v1/chat/stream`)
**Impact:** Public internet can access chatbot without any auth. Rate limiting (20/min) is the only protection.
**Fix:** Add Bearer token validation via shared JWT verification.

---

## MEDIUM RISKS (Week 2)

### M1: JWT Weaknesses
- **HS256 symmetric** — same key signs and verifies; RS256 would be stronger
- **No refresh tokens** — 24h expiry with no way to extend session
- **No revocation** — logged-out tokens remain valid until expiry
- **Single operator** — no user registration, one hardcoded operator
**Fix:** Add refresh token rotation, RS256, token blacklist.

### M2: CSP Too Restrictive
**Files:** `backend/main.py:186`, `chatbot_service/main.py:215`
```
Content-Security-Policy: default-src 'self'
```
**Breaks:** MapLibre tile loads, CDN resources (fonts, images), admin dashboard inline styles, WebSocket connections.
**Fix:** Relax to allow map tile servers, CDNs, unsafe-inline for Next.js.

### M3: CSRF Token Cookie Not HttpOnly
**File:** `backend/main.py:267`
**Impact:** JS-accessible CSRF token is vulnerable if XSS exists. Required for double-submit cookie pattern.
**Mitigation:** Bearer-authenticated requests skip CSRF check (mitigates for API clients).

### M4: Error Messages May Leak API Keys
**Files:** `chatbot_service/providers/base.py:88-110` (`raise_for_provider_status` includes `body[:500]`)
**Impact:** If a provider returns error response containing the API key, it's logged and potentially emailed via alert.
**Fix:** Redact known key patterns from error messages.

### M5: Tracking URL Embeds JWT in Fragment
**File:** `backend/api/v1/live_tracking.py:113`
```python
tracking_url = f"{frontend_url}/track/{session_id}#token={view_token}"
```
**Impact:** JWT in URL fragment persists in SMS/WhatsApp chat history, SMS logs, browser history.

### M6: Chatbot Rate Limiter Uses Memory (Not Redis)
**File:** `chatbot_service/limiter.py`
**Impact:** Rate limits reset on service restart. No cross-worker rate limiting if multi-instance.
**Fix:** Use Redis-backed slowapi like backend does.

### M7: Tenant Isolation Not Exploited
**File:** `backend/core/tenant.py`
`org_id` is extracted and stored in request state but never actually enforced in queries. The TenantAwareQuery filter pattern exists in migration 10007 but actual query usage is inconsistent.

### M8: Admin Secret Shared Between Services
**Impact:** Same `ADMIN_SECRET` for backend and chatbot. If one is compromised, both admin interfaces are exposed.

### M9: No HSTS Preload
HSTS header set but domain not submitted to browser preload lists. Prevents initial visit protection.

### M10: No Referrer-Policy / Permissions-Policy Headers
Missing headers that could prevent referrer leakage and restrict browser API access.

---

## LOW RISKS

### L1: Error Sanitization Incomplete
Only redacts SELECT/INSERT/DELETE. Misses UPDATE, DROP, ALTER, UNION, etc.

### L2: sessionStorage Queue Fallback
Offline queue falls back to sessionStorage when IndexedDB unavailable. Cleared on tab close.

### L3: POST /mcp Excluded from CSRF
MCP endpoints bypass CSRF checks. Acceptable for admin-only endpoints with separate auth.

### L4: Health Endpoint Claims Always "production"
`environment` field hardcoded to "production" in health response. Acceptable for security obscurity.

---

## DEPENDENCY VULNERABILITIES (Accepted Risk)

| Package | Vuln | Severity | Status |
|---------|------|----------|--------|
| brace-expansion (transitive) | Moderate | Moderate | Accepted |
| postcss in next (transitive) | Moderate | Moderate | Accepted |
| ws in socket.io (transitive) | Moderate | Moderate | Accepted |

Per AGENTS.md: "Fixing requires breaking version bumps — accepted risk."

---

## SECURITY CONTROL MATRIX

| Control | Status | Details |
|---------|--------|---------|
| Auth: JWT | ✅ Implemented | HS256, 24h expiry, cookie + Bearer |
| Auth: RBAC | ❌ Missing | Role in JWT, never enforced |
| Auth: MFA | ❌ Missing | Not implemented |
| Auth: Rate limiting | ⚠️ Partial | Critical endpoints limited, many unrate-limited |
| Network: HTTPS | ✅ Configured | HSTS, Secure cookies |
| Network: CSP | ⚠️ Weak | Overly restrictive, breaks features |
| Network: CORS | ✅ Good | Specific origins, explicit methods/headers |
| Network: HSTS | ⚠️ Partial | Header set, not preloaded |
| Data: Encryption at rest | ⚠️ Partial | DB encrypted by Supabase, IndexedDB plaintext |
| Data: Encryption in transit | ✅ TLS | Redis TLS, HTTPS everywhere |
| Data: PII minimization | ⚠️ Issue | Blood group sent to server despite privacy claim |
| Data: Retention | ❌ Missing | SOS incidents, tracking data persist forever |
| Data: Deletion | ❌ Missing | No GDPR delete/export endpoints |
| Input: Validation | ✅ Good | Pydantic schemas on all structured endpoints |
| Input: SQL injection | ✅ Good | Parameterized queries, no string interpolation |
| Injection: Prompt | ✅ Excellent | 7-layer defense-in-depth |
| Upload: Validation | ✅ Good | Magic bytes, EXIF stripping, size limit |
| Upload: Storage | ✅ Good | Supabase Storage with service_role key |
| Session: Cookie security | ✅ Good | HttpOnly, Secure, SameSite=Lax |
| Session: CSRF | ✅ Implemented | Double-submit cookie pattern |
| Session: Idempotency | ✅ Implemented | Idempotency-Key header, 24h dedup |
| Monitoring: Sentry | ✅ Implemented | Error tracking with 0.1 sample rate |
| Monitoring: Alerting | ✅ Implemented | Email alerts with 5-min cooldown |
| Monitoring: Metrics | ❌ Defined but not exposed | Prometheus module exists, no `/metrics` endpoint |
| Infra: Container security | ✅ Good | Non-root user, network isolation |
| Infra: Secret scanning | ✅ Periodic | Gitleaks weekly + Codacy SAST |
| Infra: Dependency scanning | ✅ Periodic | pip-audit + npm audit weekly + Dependabot |
