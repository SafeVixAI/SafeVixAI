# SafeVixAI — Security Audit Report

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../../AGENTS.md).

**Date:** 2026-05-26 | **Auditor:** Deep codebase review

---

## 1. Authentication

| Finding | Severity | Status |
|---------|----------|--------|
| PBKDF2 password hashing — no plaintext | ✅ GOOD | Verified |
| `admin123` not hardcoded (FALSE from prior audit) | ✅ GOOD | PBKDF2 + env vars |
| `mock-jwt-token-for-Project` explicitly rejected | ✅ GOOD | REJECTED_STATIC_TOKENS set |
| JWT_SECRET_KEY required in production (ephemeral only in dev) | ✅ GOOD | RuntimeError if missing |
| Dual JWT validation (app JWT + Supabase JWT + JWKS optional) | ✅ GOOD | Multi-path validation |
| Chatbot API auth now enforced in production | ✅ FIXED | `verify_internal_auth` fails without CHATBOT_INTERNAL_API_KEY |
| Single-operator only (no user registration) | ⚠️ ACCEPTED | Project constraint |
| No token revocation / blacklist | ⚠️ RISK | 24h expiry mitigates |
| JWT stored in IndexedDB (offline SOS queue) | ⚠️ RISK | Location PII co-located |

---

## 2. Authorization (RBAC)

| Finding | Severity | Status |
|---------|----------|--------|
| JWT has `role` claim | ✅ GOOD | Roles: ADMIN > OPERATOR > USER > READONLY |
| Circuit breaker endpoints check ADMIN role | ✅ GOOD | Verified in tests |
| Most endpoints don't check role claim | ❌ GAP | No role-check decorator on user/officer endpoints |
| `X-Admin-Key` header still allowed in CORS | ⚠️ LEGACY | Deprecated but functional |

---

## 3. API Security

| Finding | Severity | Status |
|---------|----------|--------|
| Rate limiting on ALL endpoints (5-40 req/min) | ✅ GOOD | slowapi with IP key |
| CSRF double-submit cookie | ✅ GOOD | Token in cookie + header |
| All SOS endpoints rate-limited (10/min POST) | ✅ GOOD | Prevents abuse |
| Health endpoint doesn't leak env name | ✅ GOOD | Hardcoded "production" |
| FastAPI docs disabled in production | ✅ GOOD | docs_url=None check |
| No Host header validation | ❌ GAP | ALLOWED_HOSTS not implemented |
| Error messages may leak provider response bodies | ⚠️ RISK | Need sanitization |

---

## 4. Data Protection

| Finding | Severity | Status |
|---------|----------|--------|
| .env files with live credentials committed to git | ❌ CRITICAL | All 3 files tracked |
| Supabase service_role key in git | ❌ CRITICAL | Full DB access |
| Gmail app password in git (skeg twci qhnq pory) | ❌ CRITICAL | Email alerts compromised |
| 11 LLM API keys in git | ❌ CRITICAL | Cost + abuse risk |
| SOS incidents persist forever (no data retention) | ⚠️ GAP | Migration exists but not enabled |
| Blood group + contacts in IndexedDB (privacy-by-design) | ✅ GOOD | Never leaves device |

---

## 5. Network Security

| Finding | Severity | Status |
|---------|----------|--------|
| CSP: `default-src 'self'` with specific connect-src | ✅ GOOD | Maps, CDN, backend domains |
| CSP: `'unsafe-inline'` in script-src | ⚠️ NEEDED | Next.js requirement |
| CSP: `'unsafe-eval'` in dev only | ✅ GOOD | Removed in production |
| HSTS: `max-age=31536000; includeSubDomains` | ✅ GOOD | 1 year |
| CORS: explicit origins in production (wildcard blocked) | ✅ GOOD | Config validation |
| X-Frame-Options: DENY | ✅ GOOD | Anti-clickjacking |
| Permissions-Policy: restricted camera/mic/geo | ✅ GOOD | Least privilege |

---

## 6. Prompt Injection Defense (7 layers)

| Layer | Location | Status |
|-------|----------|--------|
| 1. Input normalization (Unicode NFKC, zero-width strip) | SafetyChecker | ✅ GOOD |
| 2. Harm pattern detection (60+ patterns) | SafetyChecker | ✅ GOOD |
| 3. Jailbreak detection (20+ patterns, l33t decode, space obfuscation) | SafetyChecker | ✅ GOOD |
| 4. RAG trust boundary delimiters | base.py | ✅ GOOD |
| 5. Token budget enforcement (12K chars) | base.py | ✅ GOOD |
| 6. Output safety check | SafetyChecker | ✅ FIXED (was dead code) |
| 7. Medical disclaimer | SafetyChecker | ✅ FIXED (was dead code) |

---

## 7. Summary

| Category | Score | Critical Issues |
|----------|-------|-----------------|
| Authentication | 85/100 | 0 |
| Authorization | 55/100 | 1 (no RBAC enforcement) |
| API Security | 88/100 | 1 (no Host validation) |
| Data Protection | 45/100 | 4 (all .env credentials) |
| Network Security | 90/100 | 0 |
| Prompt Injection | 95/100 | 0 |
| **Overall** | **72/100** | **6 remaining** |

**Immediate rotation required:** JWT_SECRET_KEY, SUPABASE_URL/KEYS, all 11 LLM API keys, Gmail app password, REDIS_URL.
