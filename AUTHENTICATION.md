# Authentication

> Version 1.0.0 | Last updated: 2026-07-25

## Overview

SafeVixAI uses a dual-key authentication system: HS256 for Supabase-compatible interactive sessions and RS256 for JWKS-verified service tokens. Guest sessions and internal API keys provide additional access tiers.

## Token Types

### Access Token (JWT)

| Property | Value |
|----------|-------|
| Format | JWT (JSON Web Token) |
| Algorithm | HS256 (Supabase), RS256 (JWKS) |
| Header | `Authorization: Bearer <token>` |
| TTL | 15 minutes (configurable) |
| Payload | `sub` (UUID), `role`, `org_id`, `iat`, `exp`, `jti` |

### Refresh Token

| Property | Value |
|----------|-------|
| Format | Opaque string (SHA-256 hashed) |
| Storage | Redis with 30-day TTL |
| Rotation | Old token invalidated on refresh |

### Guest Token (X-Guest-ID)

| Property | Value |
|----------|-------|
| Format | UUID v4 |
| Header | `X-Guest-ID` |
| TTL | 7 days |
| Use Case | Anonymous road reports, temporary SOS contacts |

### Internal API Key (X-Internal-Api-Key)

| Property | Value |
|----------|-------|
| Format | Pre-shared secret |
| Header | `X-Internal-Api-Key` |
| Use Case | Service-to-service calls (frontend↔backend↔chatbot) |

## Supabase Integration

The frontend uses `@supabase/supabase-js` for sign-up/sign-in; the backend verifies tokens independently via `get_current_user` dependency. The `SUPABASE_JWT_SECRET` env var must match the Supabase project's JWT secret.

```
Client → Supabase: signup/login → { access_token, refresh_token }
Client → Backend: Bearer token → get_current_user → allow/deny
```

## JWKS Key Rotation

RS256 tokens use a JWKS endpoint for public key distribution:

1. `JWKSManager.start()` fetches keys with stampede protection
2. New RSA-2048 key pairs are rotated via admin endpoint
3. Old keys remain valid for a 24-hour grace period
4. Tokens remain valid until `exp` — no forced re-login

## Token Lifecycle

| Event | Issues | TTL |
|-------|--------|-----|
| Sign-up | Access + Refresh | 15 min / 30 days |
| Sign-in | Access + Refresh | 15 min / 30 days |
| Refresh | Access + Refresh (rotated) | 15 min / 30 days |
| Guest creation | Guest UUID | 7 days |

## Validation Flow

```
get_current_user(request):
  1. Extract Authorization header
  2. If missing and public_optional: return AnonymousUser(guest_id)
  3. If missing and protected: raise UNAUTHORIZED
  4. Decode header without verification (get alg)
  5. If RS256: fetch JWKS (stampede protected), verify with RSA public key
  6. If HS256: verify with SUPABASE_JWT_SECRET
  7. Return authenticated user with role + org_id
```

## Frontend AuthGuard

- Protects authenticated routes (all except `/landing`, `/login`, `/signup`, `/forgot-password`, `/reset-password`, `/privacy`, `/terms`)
- E2E bypass: `localStorage.setItem('__E2E_SKIP_AUTH__', 'true')`
- Session restore from IndexedDB via Supabase SSR

## Public Endpoints

Endpoints using `get_current_user_optional` return the user if authenticated or `None` if not:
- `GET /api/v1/emergency/nearby`
- `GET /api/v1/roads/issues`
- `POST /api/v1/roads/report` (anonymous reports accepted)
- `GET /api/v1/public/*`

## Rate Limiting by Endpoint

| Endpoint | Limit | Scope |
|----------|-------|-------|
| Login/Signup | 5 req/min | IP |
| Token Refresh | 10 req/min | IP |
| SOS | 3 req/min | IP |
| General API | 100 req/min | IP |
