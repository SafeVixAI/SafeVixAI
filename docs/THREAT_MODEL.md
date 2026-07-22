# Threat Model & Assurance Case

> **Version:** 1.0  
> **Applies to:** SafeVixAI (all three services: backend, chatbot, frontend)  
> **Last updated:** 2026-06-17

---

## Trust Boundaries

```
[User Device]
    │  TLS 1.2+ (HTTPS/WSS)
    ▼
[Frontend — Vercel / PWA]
    │  JWT Bearer + Internal API Key
    ▼
[Backend — Render]
    │  Internal API Key
    ├──►[Chatbot Service — Render]
    │       │  API Key
    │       ▼
    │    [LLM Providers — Groq, Cerebras, Gemini, etc.]
    │
    ├──►[PostgreSQL + PostGIS — Supabase]
    └──►[Redis — Upstash]
```

### Boundary A: User ↔ Frontend (Untrusted)
- **TLS termination** at Vercel edge
- **CSP headers** prevent XSS and data injection
- **Input sanitization** before rendering

### Boundary B: Frontend ↔ Backend (Low Trust)
- **JWT validation** on every authenticated request
- **Rate limiting** (100/min general, 3/min SOS)
- **Pydantic schema validation** for all inputs

### Boundary C: Backend ↔ Chatbot (Medium Trust)
- **Internal API key** (X-Internal-Api-Key header)
- **Private network** (same Render region)
- **Request timeout** via asyncio.wait_for()

### Boundary D: Chatbot ↔ LLM Providers (Low Trust)
- **API keys** stored as env vars
- **SafetyChecker** evaluates prompts before sending
- **Timeouts** prevent hanging connections

---

## Assets

| Asset | Confidentiality | Integrity | Availability | Protection |
|-------|----------------|-----------|--------------|------------|
| User credentials | High | Critical | High | Argon2id hashing, JWT |
| GPS location | Medium | Medium | Medium | Not persisted server-side |
| Emergency contacts | High | Medium | Low | IndexedDB only (client-side) |
| Chat history | Medium | Medium | Low | Redis 24h TTL |
| LLM API keys | Critical | Critical | Medium | Environment variables |
| Database credentials | Critical | Critical | Critical | Environment variables, network isolation |
| JWT signing secret | Critical | Critical | Critical | Environment variable |
| Internal API key | Critical | Critical | Medium | Environment variable |

---

## Threats

### T1: Prompt Injection / Jailbreak
| Field | Detail |
|-------|--------|
| **Risk** | Attacker crafts input that bypasses LLM safety filters |
| **Impact** | LLM produces harmful, illegal, or misleading content |
| **Likelihood** | Medium (well-known attack vector) |
| **Mitigation** | SafetyChecker with 60+ patterns; "Call 112" enforcement for injury queries |
| **Residual** | Low — SafetyChecker is regex-based, may miss novel patterns |
| **Accept** | No — actively monitored and updated |

### T2: JWT Token Theft / Forgery
| Field | Detail |
|-------|--------|
| **Risk** | Attacker steals or forges JWT to impersonate user |
| **Impact** | Unauthorized access to user data and actions |
| **Likelihood** | Low (HS256, short expiry, TLS transport) |
| **Mitigation** | 24h access token + 30d refresh token; refresh rotation |
| **Residual** | Very Low |

### T3: XSS via User-Generated Content
| Field | Detail |
|-------|--------|
| **Risk** | Attacker injects script via form input |
| **Impact** | Session hijacking, data exfiltration |
| **Likelihood** | Low (Pydantic validation + React escaping) |
| **Mitigation** | CSP headers (no unsafe-eval); Pydantic input validation; React XSS protection |
| **Residual** | Very Low |

### T4: LLM Provider Data Leak
| Field | Detail |
|-------|--------|
| **Risk** | Chat messages sent to LLM provider are logged or leaked by provider |
| **Impact** | User chat data exposed to third party |
| **Likelihood** | Low (major providers have SOC 2 / GDPR compliance) |
| **Mitigation** | No PII in chat inputs; 24h TTL on chat history; privacy policy disclosure |
| **Residual** | Medium — inherent to using external AI services |
| **Accept** | Yes (disclosed in privacy policy) |

### T5: Denial of Service / Rate Limit Bypass
| Field | Detail |
|-------|--------|
| **Risk** | Attacker floods endpoints to exhaust resources |
| **Impact** | Service unavailable for legitimate users |
| **Likelihood** | Medium (public API) |
| **Mitigation** | Rate limiting (5 tiers); Redis-based token bucket |
| **Residual** | Low — distributed DDoS would require WAF-level protection |

### T6: Dependency Supply Chain Attack
| Field | Detail |
|-------|--------|
| **Risk** | Compromised npm/PyPI package introduces vulnerability |
| **Impact** | Remote code execution, data exfiltration |
| **Likelihood** | Low (pinned versions, weekly audits) |
| **Mitigation** | Dependabot; pip-audit + npm audit in CI; Trivy scanning; SBOM generation |
| **Residual** | Low |

### T7: Internal API Key Leak
| Field | Detail |
|-------|--------|
| **Risk** | Chatbot internal API key exposed via env var leak or log |
| **Impact** | Unauthorized access to backend services |
| **Likelihood** | Low (key in env vars only, never logged) |
| **Mitigation** | OIDC-based keyless auth where possible; key rotation procedure |

### T8: SOS Spam / False Emergency Reports
| Field | Detail |
|-------|--------|
| **Risk** | Attacker floods SOS endpoint with false reports |
| **Impact** | Wastes emergency responder time |
| **Likelihood** | Medium |
| **Mitigation** | 3 req/min rate limit on SOS; guest auth tied to UUID; backend abuse detection |
| **Residual** | Low — cannot fully prevent determined abuse |

---

## Secure Design Principles Applied

| Principle | Implementation |
|-----------|---------------|
| **Least Privilege** | Workflow permissions scoped per job; GitHub token uses minimum scopes |
| **Defense in Depth** | Input validation (Pydantic) → Auth (JWT) → Rate limiting → CSP headers |
| **Fail Secure** | AuthGuard blocks all routes by default; explicit allowlist for public routes |
| **Privacy by Design** | Blood group / emergency contacts never leave device; GPS not persisted |
| **Secure Defaults** | CSP without unsafe-eval; CORS restricted; ALLOWED_HOSTS enforced |
| **Separation of Concerns** | Three services with distinct security boundaries |
| **Least Common Mechanism** | Each service has its own env vars, secrets, and database connections |

---

## Assurance Case

### Claim: SafeVixAI protects user data from unauthorized access

| Evidence | Source |
|----------|--------|
| JWT authentication with 24h expiry | `backend/core/security.py` |
| Argon2id password hashing | `backend/core/security.py` |
| CSP headers in production responses | `frontend/next.config.js` |
| Rate limiting on all public endpoints | `backend/core/limiter.py` |
| ALLOWED_HOSTS middleware validation | `backend/middleware/allowed_hosts.py` |
| Input validation via Pydantic schemas | `backend/models/schemas.py` |
| Private vulnerability reporting process | `SECURITY.md` |
| Credentials in IndexedDB only (never server) | `frontend/lib/store.ts` |

### Claim: AI responses are safe and not harmful

| Evidence | Source |
|----------|--------|
| SafetyChecker with 60+ injection patterns | `chatbot_service/agent/safety_checker.py` |
| "Call 112 immediately" enforcement | `chatbot_service/agent/safety_checker.py` |
| LLM provider timeout handling | `chatbot_service/providers/provider_router.py` |
| RAG chunk sanitization | `chatbot_service/agent/context_assembler.py` |
| 10-provider fallback prevents single-point failure | `chatbot_service/providers/provider_router.py` |

### Claim: The system is available under expected load

| Evidence | Source |
|----------|--------|
| Rate limiting (5 tiers, Redis-backed) | `backend/core/limiter.py` |
| Circuit breakers for external services | `backend/core/circuit_breaker.py` |
| Load testing with k6 | `load-testing/` |
| Health checks on all services | `backend/main.py`, `chatbot_service/main.py` |
| Redis connection graceful fallback | `backend/core/redis_client.py` |

---

## Security Review Schedule

| Review Type | Frequency | Responsible |
|-------------|-----------|-------------|
| Dependency audit | Weekly (automated) | Dependabot + CI |
| Secret scanning | Every commit (automated) | Gitleaks |
| SAST scan | Every commit (automated) | CodeQL |
| Container vulnerability scan | Every build (automated) | Trivy |
| Manual security review | Quarterly | Security Team |
| Penetration test | Annual | External (TBD) |
| Threat model update | When architecture changes | Security Team |
