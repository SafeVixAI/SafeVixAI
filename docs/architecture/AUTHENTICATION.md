# Authentication

> Version 1.0.0 | Last updated: 2026-07-29

## Dual-Key Auth System

```mermaid
graph LR
    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b

    subgraph HS256["HS256 — Supabase Sessions"]
        H1["Supabase Auth"]:::security
        H2["SUPABASE_JWT_SECRET<br/>Shared Secret Key"]:::security
        H3["Frontend Sessions<br/>Signup, Login, Refresh"]:::edge
        H1 --> H2 --> H3
    end

    subgraph RS256["RS256 — JWKS Enterprise"]
        R1["JWKSManager<br/>Key Rotation Service"]:::control
        R2["RSA-2048 Key Pair<br/>Public + Private"]:::security
        R3["Service Tokens<br/>Admin, Internal Services"]:::security
        R1 --> R2 --> R3
    end

    subgraph Guest["Guest — Anonymous"]
        G1["X-Guest-ID<br/>UUID v4"]:::security
        G2["Anonymous Access<br/>7 days TTL"]:::edge
        G1 --> G2
    end

    subgraph Internal["Internal — Service-to-Service"]
        I1["X-Internal-Api-Key<br/>Pre-shared Secret"]:::security
        I2["Backend to Chatbot<br/>Chat Proxy Calls"]:::control
        I1 --> I2
    end
```

## Token Validation Flow

```mermaid
flowchart TD
    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b

    REQ["Incoming Request"]:::edge --> AUTH{"Authorization Header?"}:::decision
    AUTH -->|"No"| OPT{"get_current_user_optional?"}:::decision
    OPT -->|"Yes"| ANON["Return AnonymousUser<br/>with guest_id"]:::success
    OPT -->|"No"| UNAUTH["Raise 401 UNAUTHORIZED"]:::security

    AUTH -->|"Bearer token"| DECODE["Decode header without verification"]:::control
    DECODE --> ALG{"Algorithm detected?"}:::decision

    ALG -->|"RS256"| JWKS["Fetch JWKS public keys<br/>stampede protected"]:::data
    JWKS --> VERIFY_RS["Verify with RSA public key"]:::security

    ALG -->|"HS256"| VERIFY_HS["Verify with SUPABASE_JWT_SECRET"]:::security

    VERIFY_RS --> CHECK{"Valid signature?"}:::decision
    VERIFY_HS --> CHECK

    CHECK -->|"No"| INV["Raise 401 Invalid Token"]:::security
    CHECK -->|"Yes"| USER["Load user from payload<br/>sub, role, org_id"]:::control
    USER --> DONE["Return AuthenticatedUser"]:::success
```

## Token Lifecycle

```mermaid
flowchart LR
    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b

    SIGNUP["Sign-up"]:::edge --> ACCESS["Issue Access Token<br/>15 min TTL"]:::security
    SIGNUP --> REFRESH["Issue Refresh Token<br/>30 day TTL"]:::security

    LOGIN["Sign-in"]:::edge --> ACCESS
    LOGIN --> REFRESH

    ACCESS --> EXP{"AuthZ check"}:::decision
    EXP -->|"Valid"| ALLOW["Allow Request"]:::success
    EXP -->|"Expired"| REFRESH_FLOW["Use Refresh Token"]:::control

    REFRESH_FLOW --> ROTATE["Rotate Tokens"]:::security
    ROTATE --> ACCESS
    ROTATE --> REFRESH

    GUEST["Guest Session"]:::edge --> GUEST_ID["Issue X-Guest-ID<br/>7 day TTL"]:::security
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
