# Authorization

> Version 1.0.0 | Last updated: 2026-07-29

## Role Hierarchy

```mermaid
graph BT
    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b

    subgraph Roles["Role Hierarchy — Levels"]
        SYS["system<br/>Level 3"]:::security
        ADMIN["admin<br/>Level 2"]:::control
        OFFICER["officer<br/>Level 1"]:::edge
        CITIZEN["citizen<br/>Level 0"]:::data
    end

    CITIZEN -->|"elevated to"| OFFICER
    OFFICER -->|"elevated to"| ADMIN
    ADMIN -->|"elevated to"| SYS
```

## Permission Check Flow

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

    REQ["Incoming Request"]:::edge --> EXTRACT["Extract JWT from Authorization header"]:::control
    EXTRACT --> VALIDATE["Validate JWT signature"]:::security
    VALIDATE -->|"Invalid"| N401["401 Unauthorized"]:::security
    VALIDATE -->|"Valid"| PARSE["Parse payload: sub, role, org_id"]:::control

    PARSE --> CHECK{"Route requires role?"}:::decision

    CHECK -->|"No"| AUTHZ_PUBLIC["Allow — Public endpoint"]:::success
    CHECK -->|"Yes, require_role"| ROLE_CHECK{"User.role >= required?"}:::decision

    ROLE_CHECK -->|"No"| N403["403 Forbidden"]:::security
    ROLE_CHECK -->|"Yes"| ALLOW["Allow — Authorized"]:::success

    subgraph Protected["Protected Route Examples"]
        ADMIN_P["/admin/cache/purge<br/>requires: admin or system"]:::security
        OFFICER_P["/api/v1/officer/*<br/>requires: officer or higher"]:::control
        USER_P["/api/v1/user/profile<br/>requires: authenticated"]:::edge
    end

    ALLOW --> ADMIN_P
    ALLOW --> OFFICER_P
    ALLOW --> USER_P
```

## Route Access Map

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

    subgraph Public["Public — No Auth Required"]
        LAND["/landing"]:::external
        LOGIN["/login"]:::external
        SIGNUP["/signup"]:::external
        FORGOT["/forgot-password"]:::external
        RESET["/reset-password"]:::external
        PRIV["/privacy"]:::external
        TERMS["/terms"]:::external
    end

    subgraph Authenticated["Authenticated — Any Valid JWT"]
        SOS["/sos"]:::edge
        PROFILE["/profile"]:::edge
        SETTINGS["/settings"]:::edge
        CHALLAN["/challan"]:::edge
        EMERGENCY["/emergency"]:::edge
        ASSISTANT["/assistant"]:::edge
        GUIDE["/guide"]:::edge
        BYSTANDER["/bystander"]:::edge
        TRACKING["/tracking"]:::edge
        OFFICER["/officer"]:::edge
        REPORT["/report"]:::edge
        LOCATOR["/locator"]:::edge
        CMD_CENTER["/command-center"]:::edge
    end

    subgraph Admin["Admin — admin/system role"]
        ADMIN_PANEL["/admin/*"]:::security
    end

    Public --> Authenticated --> Admin
```

## Role Permissions Table

| Role | Level | Description |
|------|-------|-------------|
| `citizen` | 0 | Default authenticated user |
| `officer` | 1 | Traffic/field officer |
| `admin` | 2 | System administrator |
| `system` | 3 | Internal service account |

## Permission Model

### Backend (FastAPI dependencies)

```python
# Protected endpoint
@router.get("/api/v1/user/profile")
async def get_profile(user = Depends(get_current_user)):
    ...

# Role-gated endpoint
@router.post("/api/v1/admin/cache/purge")
async def purge_cache(user = Depends(require_role(["admin", "system"]))):
    ...

# Public-optional endpoint (returns None if unauthenticated)
@router.get("/api/v1/emergency/nearby")
async def nearby_services(user = Depends(get_current_user_optional)):
    ...
```

### Frontend (AuthGuard)

- `AuthGuard` component wraps authenticated routes
- Checks for valid JWT in localStorage/Zustand
- Redirects to `/landing` if unauthenticated
- Bypassed in E2E via `__E2E_SKIP_AUTH__` flag

## Tenant Isolation

The tenant isolation middleware automatically filters database queries by `org_id`:

```python
request.state.tenant_id = await get_tenant_id(request)
# All queries filtered by tenant_id
```

## Internal API Access

Service-to-service calls use `X-Internal-Api-Key` header. Each service has its own key in environment variables. Keys are validated via constant-time comparison (`hmac.compare_digest`).

## Admin Endpoints

Protected by `ADMIN_SECRET` env var. Admin-only operations include:
- `GET /api/v1/admin/health` - Full system health
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/cache/status` - Cache status
- `POST /api/v1/admin/cache/purge` - Cache purge
- Various CRUD operations for system administration
