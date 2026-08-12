# Authorization

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [AUTHENTICATION.md](AUTHENTICATION.md), [Security.md](chatbot/security.md)

---

## Role Hierarchy

```mermaid
flowchart BT
    CIT[citizen] -->|"inherits to"| OP[operator]
    OP -->|"inherits to"| ADM[admin]

    style CIT fill:#238636,color:#fff
    style OP fill:#1f6feb,color:#fff
    style ADM fill:#9e6a03,color:#fff


    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b
    classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#7c2d12
    classDef neutral fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b

    class CIT neutral
    class OP neutral
    class ADM neutral```

Each role inherits the permissions of all roles below it.

---

## Permission Matrix

| Endpoint | citizen | operator | admin |
|----------|---------|----------|-------|
| `GET /health` | ✅ | ✅ | ✅ |
| `GET /api/v1/emergency/*` | ✅ | ✅ | ✅ |
| `POST /api/v1/sos/trigger` | ✅ | ✅ | ✅ |
| `POST /api/v1/roads/report` | ✅ | ✅ | ✅ |
| `GET /api/v1/roads/issues` | ✅ | ✅ | ✅ |
| `POST /api/v1/auth/*` | ✅ | ✅ | ✅ |
| `GET /api/v1/user/profile` | ✅ | ✅ | ✅ |
| `PUT /api/v1/user/profile` | ✅ | ✅ | ✅ |
| `GET /api/v1/command-center/*` | ❌ | ✅ | ✅ |
| `PUT /api/v1/roads/issues/{id}/status` | ❌ | ✅ | ✅ |
| `GET /api/v1/admin/*` | ❌ | ❌ | ✅ |
| `POST /api/v1/admin/cache/purge` | ❌ | ❌ | ✅ |
| `POST /api/v1/admin/webhooks` | ❌ | ❌ | ✅ |

---

## Implementation

### FastAPI Dependency
```python
from fastapi import Depends
from core.security import require_role

@router.get("/admin/cache/purge")
async def purge_cache(
    user: Annotated[User, Depends(require_role("admin"))],
):
    ...
```

### Middleware
```python
# backend/core/security.py
async def require_role(required_role: str):
    async def role_checker(request: Request):
        user = request.state.user
        if ROLE_HIERARCHY[user.role] < ROLE_HIERARCHY[required_role]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker
```

---

## Public Endpoints (No Auth)

Some endpoints are accessible without authentication:
- `POST /api/v1/roads/report` (anonymous reports allowed)
- `GET /api/v1/emergency/*` (emergency lookup)
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /health`

---

## Service-to-Service Authorization

Backend → Chatbot communication uses:
```
X-API-Key: sk-safevixai-xxxxxxxxxxxx
```

This is configured via the `CHATBOT_SERVICE_URL` environment variable and validated server-side.

---

## Best Practices

1. **Principle of least privilege**: Grant minimum permissions needed
2. **Server-side enforcement**: Never trust client-side role checks
3. **Audit logging**: All authorization failures are logged with user ID and endpoint
4. **Regular review**: Permissions should be reviewed quarterly
5. **Default deny**: New endpoints default to requiring authentication
