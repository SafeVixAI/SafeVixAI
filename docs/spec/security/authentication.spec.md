# Authentication & Token Specification (SPEC)

> **Authority:** Authoritative System Specification  
> **Source of Truth:** `backend/core/security.py`  
> **Status:** Production Normative (v1.0.0-STABLE)

---

## 1. Cryptographic Standard & Algorithm

SafeVixAI authentication is built on signed JSON Web Tokens (RFC 7519) utilizing the **HMAC-SHA256 (`HS256`)** symmetric signature algorithm for internal service and API operations, with optional Supabase JWKS RS256 verification (ADR-009).

### 1.1 Key Generation & Security Requirements
- **Production Environment (`ENVIRONMENT=production`):**
  - `JWT_SECRET_KEY` is **mandatory**.
  - Must be a cryptographically secure random secret of **at least 32 bytes (256 bits)**.
  - Absence or insufficient length triggers immediate fail-fast server termination at startup (`RuntimeError`).
- **Development Environment:**
  - If unset, generates an ephemeral 64-character URL-safe random key using `secrets.token_urlsafe(64)` with a warning.

---

## 2. Token Lifecycle & Expiration

| Token Type | Lifespan / TTL | Environment Variable | Purpose |
| :--- | :--- | :--- | :--- |
| **Access Token** | **24 Hours** (Default) | `ACCESS_TOKEN_EXPIRE_HOURS` | Authorizes API requests across REST and WebSocket endpoints. |
| **Refresh Token** | **30 Days** (Default) | `REFRESH_TOKEN_EXPIRE_DAYS` | Obtains new access tokens without requiring re-authentication. |

---

## 3. JWT Payload Structure & Claims Contract

### 3.1 Standard Claims

```json
{
  "sub": "usr_9b1deb4d3b7d4e89",
  "role": "operator",
  "jti": "550e8400-e29b-41d4-a716-446655440000",
  "iss": "safevixai-backend",
  "aud": "safevixai-app",
  "iat": 1789000000,
  "exp": 1789086400
}
```

- **`sub` (Subject):** Unique user identifier string.
- **`role` (Role):** One of the 5 canonical RBAC roles (`admin`, `operator`, `field_officer`, `user`, `readonly`).
- **`jti` (JWT ID):** UUIDv4 identifying the unique token instance for revocation tracking.
- **`exp` (Expiration Time):** UNIX timestamp in UTC.
- **`iat` (Issued At):** UNIX timestamp in UTC.

---

## 4. Token Revocation & Security Defenses

### 4.1 LRU Revocation Cache
`SecurityState` maintains an in-memory Least-Recently-Used (LRU) cache of revoked token JTIs (`_revoked_token_jtis`, capacity: 10,000 entries). Logged-out tokens or revoked operator sessions are rejected with HTTP 401.

### 4.2 Mock & Static Token Rejection
The security engine enforces strict pattern matching against known mock, debug, or insecure test tokens (e.g., tokens matching `^mock_`, `^test_`, or `demo-token`). Any attempt to authenticate with synthetic tokens in production returns HTTP 401 Unauthorized.
