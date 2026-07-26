# Authorization

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [AUTHENTICATION.md](./AUTHENTICATION.md), [Security.md](./Security.md)

---

## Role Hierarchy

```
admin → operator → citizen
```

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
