# Authentication

> Version 1.0.0 | Last updated: 2026-07-29

## Dual-Key Auth System

```mermaid
graph LR
    subgraph HS256["HS256 — Supabase Sessions"]
        H1[Supabase Auth]
        H2[SUPABASE_JWT_SECRET<br/>Shared Secret Key]
        H3[Frontend Sessions<br/>Signup, Login, Refresh]
        H1 --> H2 --> H3
    end

    subgraph RS256["RS256 — JWKS Enterprise"]
        R1[JWKSManager<br/>Key Rotation Service]
        R2[RSA-2048 Key Pair<br/>Public + Private]
        R3[Service Tokens<br/>Admin, Internal Services]
        R1 --> R2 --> R3
    end

    subgraph Guest["Guest — Anonymous"]
        G1[X-Guest-ID<br/>UUID v4]
        G2[Anonymous Access<br/>7 days TTL]
        G1 --> G2
    end

    subgraph Internal["Internal — Service-to-Service"]
        I1[X-Internal-Api-Key<br/>Pre-shared Secret]
        I2[Backend to Chatbot<br/>Chat Proxy Calls]
        I1 --> I2
    end
```

## Token Validation Flow

```mermaid
flowchart TD
    REQ[Incoming Request] --> AUTH{Authorization Header?}

    AUTH -->|No| OPT{get_current_user_optional?}
    OPT -->|Yes| ANON[Return AnonymousUser<br/>with guest_id]
    OPT -->|No| UNAUTH[Raise 401 UNAUTHORIZED]

    AUTH -->|Bearer token| DECODE[Decode header without verification]
    DECODE --> ALG{Algorithm detected?}

    ALG -->|RS256| JWKS[Fetch JWKS public keys<br/>stampede protected]
    JWKS --> VERIFY_RS[Verify with RSA public key]

    ALG -->|HS256| VERIFY_HS[Verify with SUPABASE_JWT_SECRET]

    VERIFY_RS --> CHECK{Valid signature?}
    VERIFY_HS --> CHECK

    CHECK -->|No| INV[Raise 401 Invalid Token]
    CHECK -->|Yes| USER[Load user from payload<br/>sub, role, org_id]
    USER --> DONE[Return AuthenticatedUser]
```

## Token Lifecycle

```mermaid
flowchart LR
    SIGNUP[Sign-up] --> ACCESS[Issue Access Token<br/>15 min TTL]
    SIGNUP --> REFRESH[Issue Refresh Token<br/>30 day TTL]

    LOGIN[Sign-in] --> ACCESS
    LOGIN --> REFRESH

    ACCESS --> EXP{AuthZ check}
    EXP -->|Valid| ALLOW[Allow Request]
    EXP -->|Expired| REFRESH_FLOW[Use Refresh Token]

    REFRESH_FLOW --> ROTATE[Rotate Tokens]
    ROTATE --> ACCESS
    ROTATE --> REFRESH

    GUEST[Guest Session] --> GUEST_ID[Issue X-Guest-ID<br/>7 day TTL]
```

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
| Use Case | Service-to-service calls (frontend-backend-chatbot) |

## Supabase Integration

The frontend uses `@supabase/supabase-js` for sign-up/sign-in; the backend verifies tokens independently via `get_current_user` dependency. The `SUPABASE_JWT_SECRET` env var must match the Supabase project's JWT secret.

```
Client to Supabase: signup/login to { access_token, refresh_token }
Client to Backend: Bearer token to get_current_user to allow/deny
```

## JWKS Key Rotation

RS256 tokens use a JWKS endpoint for public key distribution:

1. `JWKSManager.start()` fetches keys with stampede protection
2. New RSA-2048 key pairs are rotated via admin endpoint
3. Old keys remain valid for a 24-hour grace period
4. Tokens remain valid until `exp` - no forced re-login

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
