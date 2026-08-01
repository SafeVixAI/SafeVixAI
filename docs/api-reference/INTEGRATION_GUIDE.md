# Integration Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [API.md](API.md), [SDK_GUIDE.md](SDK_GUIDE.md), [AUTHENTICATION.md](../architecture/AUTHENTICATION.md)

---

## Overview

SafeVixAI exposes three services for integration:

| Service | Base URL | Purpose |
|---------|----------|---------|
| Backend API | `https://api.safevixai.gov.in` | Core data: emergency, challan, road reports, SOS, tracking, civic intel |
| Chatbot API | `https://chatbot.safevixai.gov.in` | AI-powered traffic law, first-aid, legal RAG, Indian language support |
| WebSocket | `wss://api.safevixai.gov.in/api/v1/tracking/{session_id}` | Live location tracking, family safety monitoring |

---

## Authentication

### JWT Bearer Token (Primary)

All authenticated endpoints require a JWT in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

**Token acquisition:**
```
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "operator@safevixai.gov.in",
  "password": "your-password"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Token details:**
- Algorithm: RS256
- Expiry: 1 hour (access), 30 days (refresh)
- Refresh: `POST /api/v1/auth/refresh`
- JWKS endpoint: `GET /.well-known/jwks.json`

**Claims:**
```json
{
  "sub": "user-uuid",
  "role": "operator | admin | citizen",
  "iat": 1680000000,
  "exp": 1680003600
}
```

### API Key (Service-to-Service)

```
X-API-Key: sk-safevixai-xxxxxxxxxxxx
```

---

## REST API Endpoints

See [API.md](API.md) for the complete reference. Key groups:

| Area | Base Path |
|------|-----------|
| Emergency | `/api/v1/emergency/` |
| Challan | `/api/v1/challan/` |
| Road Reports | `/api/v1/roads/` |
| SOS | `/api/v1/sos/` |
| Tracking | `/api/v1/tracking/` |
| Civic Intel | `/api/v1/civic-intel/` |
| Waze Feed | `/api/v1/waze/` |
| Auth | `/api/v1/auth/` |
| Admin | `/api/v1/admin/` |
| Chat | `/api/v1/chat/` |
| Health | `/health` |

---

## WebSocket Connections

Live tracking uses a dedicated WebSocket endpoint.

### Connection
```javascript
const ws = new WebSocket('wss://api.safevixai.gov.in/api/v1/tracking/{session_id}');

ws.onopen = () => {
  ws.send(JSON.stringify({ type: 'auth', token: 'jwt-token-here' }));
};
```

### Message Types

**Client → Server:**
```json
{ "type": "location_update", "lat": 13.0827, "lon": 80.2707, "speed": 45, "battery": 80 }
{ "type": "sos_trigger", "reason": "accident" }
```

**Server → Client:**
```json
{ "type": "location_update", "lat": 13.0827, "lon": 80.2707, "user_id": "abc123" }
{ "type": "sos_alert", "message": "SOS triggered by family member", "user_id": "abc123" }
{ "type": "error", "code": "SESSION_EXPIRED", "message": "Tracking session has ended" }
```

---

## Rate Limits

| Tier | Rate Limit | Applies To |
|------|-----------|------------|
| Unauthenticated | 10 req/min per IP | All endpoints |
| Authenticated | 60 req/min per user | All endpoints |
| Challan Calculator | 30 req/min per user | `/api/v1/challan/` |
| Chatbot | 20 req/min per user | `/api/v1/chat/` |
| Waze Feed | TokenBucket (configurable) | `/api/v1/waze/` |

Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Pagination

List endpoints support cursor-based pagination:

```
GET /api/v1/roads/issues?cursor=abc123&limit=20
```

Response:
```json
{
  "items": [...],
  "next_cursor": "def456",
  "has_more": true,
  "total": 150
}
```

---

## Error Handling

Standard error response format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      { "field": "lat", "message": "Must be between -90 and 90" }
    ],
    "request_id": "req_abc123"
  }
}
```

HTTP status codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity, 429 Too Many Requests, 500 Internal Server Error.

See [ERROR_CODES.md](ERROR_CODES.md) for the complete error code reference.

---

## SDK & Client Libraries

### cURL
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.safevixai.gov.in/api/v1/emergency/nearby?lat=13.0827&lon=80.2707"
```

### Python
```python
import httpx

async with httpx.AsyncClient() as client:
    resp = await client.get(
        "https://api.safevixai.gov.in/api/v1/emergency/nearby",
        params={"lat": 13.0827, "lon": 80.2707},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp.json()
```

### JavaScript / TypeScript
```typescript
const response = await fetch(
  `https://api.safevixai.gov.in/api/v1/emergency/nearby?lat=${lat}&lon=${lon}`,
  { headers: { Authorization: `Bearer ${token}` } }
);
const data = await response.json();
```

---

## CORS Configuration

For production, restrict CORS to specific origins:
```python
# backend/core/config.py
CORS_ORIGINS: list[str] = [
    "https://safevixai.vercel.app",
    "https://your-custom-domain.com",
]
```

A wildcard `*` in production raises a `RuntimeError`.

---

## Webhooks

See [WEBHOOKS.md](WEBHOOKS.md) for the complete webhook reference.

Available events: `sos.activated`, `report.submitted`, `issue.resolved`, `user.registered`, `tracking.started`, `tracking.ended`.

---

## Best Practices

1. **Implement retry with exponential backoff** for transient failures (429, 5xx)
2. **Use idempotency keys** for critical POST operations
3. **Cache JWKS responses** (they rotate infrequently)
4. **Handle WebSocket reconnection** with exponential backoff
5. **Validate all responses** against the documented schemas
6. **Set reasonable timeouts** (30s for API calls, 60s for chatbot)
7. **Monitor rate limit headers** to avoid throttling
