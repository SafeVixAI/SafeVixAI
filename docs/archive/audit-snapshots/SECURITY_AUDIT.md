# SafeVixAI â€" Security Audit Report

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

**Date:** 2026-05-19  
**Scope:** Authentication, authorization, RBAC, CSP/CSRF/XSS, secrets, supply chain, compliance, runtime security

---

## CRITICAL Findings

### 1. No RBAC System
**Severity:** CRITICAL  
**Scope:** Entire backend

**Problem:** All authenticated users have equal access. The `get_current_user()` function returns a user dict with a `role` field, but no endpoint checks this role. Admin endpoints (`/admin/*`) use only `X-Admin-Key` header validation, which is a shared secret â€" not user-based RBAC.

**Production Impact:** Any authenticated user can potentially access admin functionality if they obtain the admin key. No user-level permission enforcement exists.

**Security Impact:** HIGH â€" Privilege escalation possible if admin key leaks.

**Fix:**
1. Implement RBAC middleware that checks `user.role` against required permissions
2. Define roles: `admin`, `operator`, `user`, `readonly`
3. Add `@require_role("admin")` decorator to admin endpoints
4. Store role claims in JWT tokens
5. Implement permission matrix documenting which roles can access which endpoints

---

### 2. JWT Tokens in Cookies Without HttpOnly
**Severity:** CRITICAL  
**File:** `frontend/lib/api.ts:14`, `backend/core/security.py:127`

**Problem:** The frontend uses `withCredentials: true` and reads `access_token` from cookies (`request.cookies.get("access_token")`). However, the cookie is not set with `HttpOnly` flag, meaning JavaScript can access it. Any XSS vulnerability can steal the token.

**Production Impact:** Account takeover via XSS attack.

**Security Impact:** CRITICAL â€" Complete authentication bypass possible.

**Fix:**
1. Set `HttpOnly=True` on JWT cookies in backend response
2. Set `Secure=True` in production
3. Set `SameSite=Lax` or `Strict`
4. Move token validation to backend-only (don't read from JS)
5. Use separate cookie for CSRF token (already done)

---

### 3. Supabase JWT Secret Has No Rotation Strategy
**Severity:** CRITICAL  
**File:** `backend/core/security.py:40-41`

**Problem:** `SUPABASE_JWT_SECRET` is loaded once at startup and never rotated. If the secret is compromised, all tokens signed with it are vulnerable until manual restart.

**Production Impact:** Compromised secret = permanent access until restart.

**Security Impact:** HIGH â€" No key rotation means indefinite exposure window.

**Fix:**
1. Implement periodic key rotation (every 24-72 hours)
2. Support multiple valid secrets during rotation window
3. Use Supabase's JWKS endpoint for dynamic key fetching
4. Add key version (`kid`) to tokens for tracking

---

## HIGH Findings

### 4. No Input Validation on File Uploads
**Severity:** HIGH  
**File:** `backend/api/v1/roadwatch.py`

**Problem:** File uploads accept `image/jpeg`, `image/png`, `image/webp` but don't validate file content (magic bytes). A malicious file with a valid extension but malicious content could be uploaded.

**Production Impact:** Potential code execution if uploaded files are served directly.

**Fix:**
1. Validate magic bytes using `python-magic` or `imghdr`
2. Re-encode images through PIL to strip any embedded payloads
3. Store uploads outside web root
4. Add file size validation (already at 5MB limit)

---

### 5. No Rate Limiting on Authentication Endpoints
**Severity:** HIGH  
**File:** `backend/api/v1/auth.py`

**Problem:** Login/auth endpoints don't have specific rate limits. The global rate limiter applies, but auth endpoints need stricter limits (e.g., 5 attempts per minute per IP).

**Production Impact:** Brute force attacks on user accounts.

**Fix:**
1. Add `@limiter.limit("5/minute")` to login endpoint
2. Add account lockout after 10 failed attempts
3. Implement progressive delays (exponential backoff per IP)

---

### 6. MCP Server Disabled in Production But Code Path Exists
**Severity:** HIGH  
**File:** `backend/core/config.py:124-127`

**Problem:** MCP server is disabled in production (`return False`), but the code path and routes exist. If `ENVIRONMENT` is misconfigured, MCP becomes accessible.

**Production Impact:** Unauthenticated database writes possible if MCP accidentally enabled.

**Fix:**
1. Remove MCP routes entirely in production builds
2. Add startup validation that rejects MCP enable in production
3. Add audit logging for any MCP access attempts

---

### 7. No Content Security Policy Report Endpoint
**Severity:** HIGH  
**Scope:** Frontend + Backend

**Problem:** CSP headers are set (`next.config.js`, `backend/main.py`), but there's no `report-uri` or `report-to` directive. CSP violations are silently dropped.

**Production Impact:** Cannot detect CSP bypass attempts or misconfigurations.

**Fix:**
1. Add `report-uri /api/v1/security/csp-report` to CSP headers
2. Implement CSP report endpoint that logs violations
3. Set up alerts for repeated CSP violations

---

### 8. No Dependency Vulnerability Scanning in CI
**Severity:** HIGH  
**File:** `.github/workflows/security.yml`

**Problem:** The security workflow runs `pip audit` and `npm audit`, but doesn't block on findings. Vulnerable dependencies can be merged.

**Production Impact:** Known vulnerabilities deployed to production.

**Fix:**
1. Add `--fail-on critical` to pip audit
2. Add `--audit-level critical` to npm audit
3. Block PR merges with critical vulnerabilities
4. Add Dependabot auto-merge for patch updates

---

### 9. No Request Size Limits on Chat Endpoints
**Severity:** HIGH  
**File:** `chatbot_service/api/chat.py`

**Problem:** No maximum request body size limit on chat endpoints. An attacker could send extremely large messages to exhaust memory.

**Production Impact:** DoS via memory exhaustion.

**Fix:**
1. Add `max_body_size` middleware (e.g., 1MB limit)
2. Add message length validation (e.g., 4000 char max)
3. Add rate limiting on chat endpoints per session

---

## MEDIUM Findings

### 10. No Audit Logging for Admin Actions
**Severity:** MEDIUM  
**File:** `chatbot_service/api/admin.py`

**Problem:** Admin endpoint actions (rebuild index, provider health) are not logged to the audit system.

**Fix:** Add `AuditLog.log_admin_action()` calls to all admin endpoints.

---

### 11. No TLS Certificate Pinning
**Severity:** MEDIUM  
**Scope:** All services

**Problem:** No certificate pinning for inter-service communication. MITM attacks possible on internal network.

**Fix:** Implement certificate pinning for backend â†" chatbot communication.

---

### 12. No Security Headers on Error Responses
**Severity:** MEDIUM  
**File:** `backend/main.py:230-239`

**Problem:** Global exception handler returns JSON responses but doesn't include security headers (CSP, X-Frame-Options, etc.).

**Fix:** Add security headers to all error responses.

---

### 13. No Secret Scanning in Pre-Commit Hooks
**Severity:** MEDIUM  
**File:** `.husky/`

**Problem:** Pre-commit hooks exist but don't include secret scanning (gitleaks is only in CI).

**Fix:** Add gitleaks to pre-commit hooks for local detection.

---

### 14. No API Key Scoping
**Severity:** MEDIUM  
**Scope:** All API keys

**Problem:** API keys (OpenRouteService, What3Words, etc.) are not scoped to specific operations. A compromised key has full access.

**Fix:** Use scoped API keys where provider supports it.

---

### 15. No Session Invalidation on Password Change
**Severity:** MEDIUM  
**File:** `backend/api/v1/auth.py`

**Problem:** When a user changes their password, existing sessions are not invalidated.

**Fix:** Add session version tracking; invalidate all sessions on password change.

---

## LOW Findings

### 16. No Security.txt File
**Severity:** LOW  
**Scope:** Frontend

**Problem:** No `.well-known/security.txt` file for responsible disclosure.

**Fix:** Add security.txt with contact info and disclosure policy.

---

### 17. No HSTS Preload
**Severity:** LOW  
**File:** `frontend/next.config.js:94-96`

**Problem:** HSTS header is set but not submitted to HSTS preload list.

**Fix:** Submit domain to hstspreload.org after 1 year of HSTS.

---

### 18. No Subresource Integrity (SRI) for CDN Resources
**Severity:** LOW  
**Scope:** Frontend

**Problem:** External resources (Google Fonts, CDN scripts) don't use SRI hashes.

**Fix:** Add `integrity` and `crossorigin` attributes to external script/link tags.

---

## Security Score Summary

| Area | Score | Grade |
|------|-------|-------|
| Authentication | 5/10 | C |
| Authorization/RBAC | 3/10 | F |
| Input Validation | 6/10 | C+ |
| Secret Management | 7/10 | B- |
| CSP/CSRF/XSS | 8/10 | B+ |
| Dependency Security | 6/10 | C+ |
| Runtime Security | 7/10 | B- |
| Compliance | 5/10 | C |
| **Overall** | **6.5/10** | **C+** |
