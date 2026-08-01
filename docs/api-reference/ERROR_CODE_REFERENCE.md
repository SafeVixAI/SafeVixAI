# Error Code Reference

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [API.md](API.md), [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)

---

## AUTH Errors (Authentication & Authorization)

| Code | HTTP Status | Message | Description | Action |
|------|-------------|---------|-------------|--------|
| AUTH001 | 401 | Token expired | JWT access token has expired | Refresh token via `/auth/refresh` |
| AUTH002 | 401 | Invalid token | JWT signature verification failed | Obtain a new token |
| AUTH003 | 403 | Insufficient permissions | User role lacks required permission | Request elevated role |
| AUTH004 | 401 | Token revoked | Token has been revoked (logout) | Obtain a new token |
| AUTH005 | 401 | Missing authorization header | No `Authorization` header in request | Include `Bearer <token>` header |
| AUTH006 | 422 | Invalid token format | Token is malformed or wrong format | Check token format |
| AUTH007 | 429 | Too many login attempts | Login endpoint rate limited | Wait and retry |
| AUTH008 | 401 | JWKS fetch failed | Cannot fetch JSON Web Key Set | Retry, check JWKS endpoint |
| AUTH009 | 403 | Account disabled | User account has been disabled | Contact support |
| AUTH010 | 404 | User not found | User does not exist | Check user ID |

---

## API Errors

| Code | HTTP Status | Message | Description | Action |
|------|-------------|---------|-------------|--------|
| API001 | 400 | Validation error | Request body fails schema validation | Check error details for specific fields |
| API002 | 404 | Not found | Resource does not exist | Check resource ID |
| API003 | 405 | Method not allowed | HTTP method not supported for endpoint | Use correct HTTP method |
| API004 | 406 | Not acceptable | Requested content type not supported | Set Accept header to application/json |
| API005 | 415 | Unsupported media type | Content-Type not supported | Use application/json |
| API006 | 422 | Unprocessable entity | Request body is valid but semantically incorrect | Check business logic constraints |
| API007 | 429 | Rate limit exceeded | Too many requests | Check Retry-After header, back off |
| API008 | 500 | Internal server error | Unexpected server error | Retry with backoff, report if persists |
| API009 | 502 | Bad gateway | Upstream service error | Check dependent services |
| API010 | 503 | Service unavailable | Service temporarily unavailable | Retry with backoff |
| API011 | 504 | Gateway timeout | Upstream service timed out | Retry with backoff |
| API012 | 409 | Conflict | Resource conflict (duplicate, version mismatch) | Resolve conflict and retry |

---

## CHAT Errors (Chatbot)

| Code | HTTP Status | Message | Description | Action |
|------|-------------|---------|-------------|--------|
| CHAT001 | 400 | Safety check blocked | Message was blocked by SafetyChecker | Rephrase the query |
| CHAT002 | 503 | All providers failed | All 9 LLM providers failed to generate a response | Check provider health, retry later |
| CHAT003 | 504 | Provider timeout | LLM provider did not respond in time | Retry, configure longer timeout |
| CHAT004 | 400 | Context too long | Conversation history exceeds max tokens | Start new conversation |
| CHAT005 | 502 | Provider error | LLM provider returned an error | Check provider status |
| CHAT006 | 400 | Invalid provider hint | Specified provider not in registry | Use available provider name |
| CHAT007 | 404 | Tool not found | Requested agent tool does not exist | Check tool name |
| CHAT008 | 500 | Context assembly failed | Failed to assemble conversation context | Retry |
| CHAT009 | 400 | Empty message | Message is empty | Provide content |
| CHAT010 | 400 | Message too long | Message exceeds character limit | Shorten message |

---

## DB Errors (Database)

| Code | HTTP Status | Message | Description | Action |
|------|-------------|---------|-------------|--------|
| DB001 | 500 | Database connection failed | Cannot connect to PostgreSQL | Check database URL and connectivity |
| DB002 | 500 | Query execution failed | Database query error | Review query, check server logs |
| DB003 | 500 | Migration pending | Database migrations not applied | Run `alembic upgrade head` |
| DB004 | 500 | Deadlock detected | Transaction deadlock | Retry the request |
| DB005 | 500 | Connection pool exhausted | All database connections in use | Increase pool size or add instances |
| DB006 | 500 | Unique constraint violation | Duplicate value on unique column | Use different value |
| DB007 | 500 | Foreign key violation | Referenced row does not exist | Check foreign key value |
| DB008 | 500 | Serialization failure | Concurrent transaction conflict | Retry the request |

---

## INFRA Errors (Infrastructure)

| Code | HTTP Status | Message | Description | Action |
|------|-------------|---------|-------------|--------|
| INFRA001 | 503 | Redis connection failed | Cannot connect to Redis | Check REDIS_URL (falls back to in-memory) |
| INFRA002 | 503 | ChromaDB unavailable | ChromaDB vector store not accessible | Check vectorstore path and permissions |
| INFRA003 | 503 | LLM chain exhausted | All providers exhausted without results | Alert administrator, check API keys |
| INFRA004 | 500 | Circuit breaker open | External API circuit breaker is open | Wait for circuit to close (30s) |
| INFRA005 | 500 | Idempotency conflict | Duplicate idempotency key with different payload | Use unique idempotency key per request |
| INFRA006 | 503 | File upload failed | Could not save uploaded file | Check disk space and permissions |
| INFRA007 | 503 | Email alert failed | Failed to send alert email | Check SMTP configuration |
| INFRA008 | 503 | DuckDB query failed | Offline challan query error | Check CSV data files |
| INFRA009 | 401 | Invalid API key | Provider API key is invalid or expired | Update API key in environment |
| INFRA010 | 500 | Configuration error | Missing or invalid configuration | Check environment variables |

---

## Response Format

### Single Error
```json
{
  "error": {
    "code": "AUTH001",
    "message": "Token expired",
    "details": [
      {
        "field": "authorization",
        "message": "Token expired at 2026-07-26T09:00:00Z"
      }
    ],
    "request_id": "req_abc123def456"
  }
}
```

### Validation Errors
```json
{
  "error": {
    "code": "API001",
    "message": "Validation error",
    "details": [
      { "field": "lat", "message": "Must be between -90 and 90" },
      { "field": "lon", "message": "Must be between -180 and 180" }
    ],
    "request_id": "req_def789ghi012"
  }
}
```

---

## Best Practices

1. **Always check `request_id`** — include it in bug reports for log correlation
2. **Handle 429 gracefully** — read `Retry-After` header and back off
3. **Retry 5xx errors** — with exponential backoff (1s, 2s, 4s, 8s, 16s max)
4. **Do not retry 4xx errors** — they will always fail (fix the request)
5. **Log error codes** — for monitoring and alerting
