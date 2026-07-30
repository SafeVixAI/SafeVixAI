# SafeVixAI — Security

## Security Overview

SafeVixAI handles sensitive user data (GPS location, blood group, emergency contacts) and makes calls to emergency services. Security is critical.

---

```mermaid
flowchart TB
    subgraph Transport["Transport Security"]
        T[HTTPS / WSS / TLS 1.2+]
    end

    subgraph Auth["Authentication"]
        A1[JWT RS256 + HS256]
        A2[JWKS Key Rotation]
        A3[Guest UUID v4]
        A4[Service-to-Service API Key]
    end

    subgraph API_Sec["API Security"]
        R1[Rate Limiting - TokenBucket]
        C1[CORS Restricted Origins]
        H1[Host Header Validation]
        CSRF[CSRF Protection]
    end

    subgraph Data_Protect["Data Protection"]
        D1[IndexedDB - Blood group, Contacts]
        D2[Redis - 24h TTL chat]
        D3[TLS for Redis - rediss://]
        D4[No GPS persistence]
    end

    subgraph LLM_Safety["LLM Safety"]
        S1[SafetyChecker - 60+ patterns]
        S2[Prompt Injection Defense]
        S3[Call 112 - Injury disclosure]
        S4[RAG trust boundary]
    end

    Transport --> Auth
    Auth --> API_Sec
    API_Sec --> Data_Protect
    Data_Protect --> LLM_Safety

    style Transport fill:#1f6feb,color:#fff
    style Auth fill:#238636,color:#fff
    style API_Sec fill:#9e6a03,color:#fff
    style Data_Protect fill:#6e5494,color:#fff
    style LLM_Safety fill:#da3633,color:#fff
```

## 1. Authentication & Authorization

### JWT Authentication
- **HS256** tokens with 24h access token, 30d refresh token
- Issued and validated via `backend/core/security.py`
- Supabase JWT validation also supported (`SUPABASE_JWT_SECRET` + `SUPABASE_JWT_AUDIENCE`)
- Bearer token injection: Frontend API client (`lib/api.ts`) attaches Bearer token from Zustand store (in-memory only — NOT persisted to localStorage)

### Mock Token Rejection
- Static blacklist + regex pattern matching rejects mock/fake/test/demo tokens
- Enforced in security middleware before JWT validation

### Token Revocation
- In-memory set + Redis-backed revocation list
- Revoked tokens rejected at validation time

### AuthGuard (Frontend)
- Component-level guard wrapping protected routes
- Bypassed in E2E via `localStorage.__E2E_SKIP_AUTH__` flag
- When flag is `'true'`, AuthGuard renders children directly without any auth check

### Guest Auth
- Anonymous UUID-based guest IDs via `frontend/lib/guest-auth.ts`
- Blood group and emergency contacts stored in IndexedDB only — never leave device

### Service-to-Service Auth
- `X-Internal-Api-Key` header for chatbot ↔ backend communication
- Backend validates this header via `get_current_user_optional` for internal requests

### RBAC
- Role-based access control via `backend/core/rbac.py` + `require_role()` dependency
- Supports granular permission checks per route

### Auth Bypass for Offline
- `GET /api/v1/offline/bundle/{city}` is intentionally unauthenticated (required for offline use)

---

## 2. API Security

### CORS Configuration
```python
# backend/core/config.py — CORS is environment-driven with fail-fast in production
# If ENVIRONMENT=production and CORS_ORIGINS="*", the app raises RuntimeError at startup.
# Same guard exists in chatbot_service/config.py.
```

### Rate Limiting
Implemented via `slowapi` (IP-based):

| Endpoint Group | Limit |
|---------------|-------|
| General | 100/minute |
| Auth | 5/minute |
| SOS | 3/minute |
| Challan | 60/minute |
| Chat | 30/minute |
| Geocode | 30/minute |

### CSP Headers
- Strict Content Security Policy in production
- No `'unsafe-eval'` in production CSP

### ALLOWED_HOSTS Middleware
- `backend/middleware/allowed_hosts.py` — enforces Host header validation
- Prevents Host header injection attacks in production

### Security Headers
- **HSTS** (HTTP Strict Transport Security)
- **X-Content-Type-Options**: nosniff
- **X-Frame-Options**: DENY
- **Permissions-Policy**: restricted feature access
- **Cache-Control**: appropriate for sensitive responses

### CSRF Protection
- Cookie-based CSRF protection
- Bearer token endpoints are exempt (stateless auth)

### Request ID
- `X-Request-ID` header for correlation and audit logging
- Attached to every request/response

### Input Validation
- All request parameters validated via **Pydantic** schemas
- GPS coordinates validated: lat [-90, 90], lon [-180, 180]
- Photo uploads: filetype validation, 10MB max size limit via `python-multipart`
- SQL injection: impossible — SQLAlchemy parameterized queries only
- Violation codes: validated against whitelist pattern `^MVA_[A-Z0-9_]+$`

---

## 3. Data Privacy

| Data | Stored? | Where | Notes |
|------|---------|-------|-------|
| GPS coordinates (emergency search) | No | Redis cache key only (no IP link) | Coordinates cached, not logged |
| GPS coordinates (road report) | Yes | PostgreSQL road_issues table | Required for complaint routing |
| Blood group | No | Browser IndexedDB only | Never sent to server |
| Emergency contacts | No | Browser IndexedDB only | Never sent to server |
| Vehicle number | No | Browser IndexedDB only | Only included in WhatsApp message |
| Chat messages (online) | Yes | Redis (24hr TTL) | Session-only, auto-deleted |
| Chat messages (offline) | No | Never leaves device | WebLLM runs fully locally |
| Crash detection events | Yes | Local state (no server upload yet) | Anonymised if added in future |
| Photos (road reports) | Yes | Supabase Storage | User-submitted evidence |

### Privacy Principles
- **Data minimization**: Only collect what's strictly needed
- **Purpose limitation**: Emergency location not used for analytics
- **Storage limitation**: Chat history auto-deleted after 24 hours
- **Local processing**: All offline AI inference stays on device
- **User consent**: Blood group/contacts stored only after explicit user action

---

## 4. Transport Security

- All traffic over **HTTPS** (Vercel + Render both enforce HTTPS)
- Upstash Redis connection over **TLS** (`rediss://` scheme)
- Supabase connection over **SSL** (`?sslmode=require` in connection string)
- WebSocket connections use **WSS** (secure WebSocket)

---

## 5. Crash Detection

- **DeviceMotion API** at ~60Hz accelerometer sampling
- Multi-tier thresholds: Minor 6G, Moderate 15G, Severe 30G
- Speed gate: GPS speed must be > 15 km/h (prevents phone-drop false positives)
- Duration gate: high-G must last < 500ms
- 20-second "Are you okay?" **CrashCountdown UI** with progress circle + haptic vibration
- If no cancel: triggers SOS workflow
- **Fully implemented** — not a V2/planned feature

---

## 6. Prompt Injection Defense

- **SafetyChecker**: `chatbot_service/agent/safety_checker.py` — 12-pattern guard blocks harmful queries before any LLM call
- Prohibited patterns: "ignore previous instructions", "you are now", "system prompt", etc.
- Harmful query categories blocked: "how to fake an accident", "how to escape after hit and run"
- Always prepends "Call 112 immediately" for injury-related queries
- Intent detection runs before RAG to classify and scope the query
- LLM provider timeout: `asyncio.wait_for()` enforced on every provider call
- RAG context explicitly instructed: "Answer ONLY from the provided text."

---

## 7. Supabase Storage

- Photo uploads for road reports stored in Supabase Storage
- Filetype validated by MIME type AND magic bytes
- Maximum upload size: 10MB

---

## 8. Sentry Error Monitoring

- Optional Sentry SDK integration in both backend and frontend
- Configured via `SENTRY_DSN` environment variable

---

## 9. Dependency Security

- All Python packages **pinned** in requirements.txt (no floating versions)
- All npm packages **pinned** in package.json
- GitHub Dependabot enabled for automated security updates
- `pip audit` runs in CI to check for known CVEs
- `npm audit` runs in CI frontend build step

---

*Document version: 2.0 | AI-powered road safety platform | Updated: June 2026*

## Related

- [AUTHENTICATION.md](AUTHENTICATION.md) — Auth flows and JWT validation
- [AUTHORIZATION.md](AUTHORIZATION.md) — RBAC and permission model
- [THREAT_MODEL.md](THREAT_MODEL.md) — Threat modeling and risk assessment
- [SECURITY_REQUIREMENTS.md](SECURITY_REQUIREMENTS.md) — Detailed security requirements
