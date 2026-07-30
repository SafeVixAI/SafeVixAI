# Error Codes Reference

> Version 1.0 | 2026-07-29

## Circuit Breaker State Machine

```mermaid
stateDiagram-v2
    [*] --> Closed: Initial State
    Closed --> Open: Failures >= threshold (5)<br/>within window (60s)
    Open --> HalfOpen: Timeout elapsed (30s)
    HalfOpen --> Closed: Probe success<br/>(single request passes)
    HalfOpen --> Open: Probe failure<br/>(still failing)
    Open --> Open: Reset timeout (30s)

    note right of Closed
        Normal operation.
        Requests pass through.
        Failure counter resets
        every 60s sliding window.
    end note

    note right of Open
        Fast-fail all requests
        with 503 Service Unavailable.
        Circuit reset after 30s.
    end note

    note right of HalfOpen
        Single probe request allowed.
        Success -> recover to Closed.
        Failure -> back to Open.
    end note
```

## Error Codes by HTTP Status Group

```mermaid
classDiagram
    class _4xx_Client_Errors {
        +400 Bad Request: ERR_INVALID_INPUT
        +400 Bad Request: ERR_MISSING_FIELD
        +401 Unauthorized: ERR_INVALID_TOKEN
        +401 Unauthorized: ERR_TOKEN_EXPIRED
        +403 Forbidden: ERR_INSUFFICIENT_PERMISSIONS
        +404 Not Found: ERR_NOT_FOUND
        +409 Conflict: ERR_DUPLICATE_ENTRY
        +422 Unprocessable: ERR_VALIDATION_FAILED
        +429 Rate Limited: ERR_RATE_LIMITED
    }

    class _5xx_Server_Errors {
        +500 Internal: ERR_INTERNAL_ERROR
        +502 Bad Gateway: ERR_UPSTREAM_TIMEOUT
        +503 Unavailable: ERR_SERVICE_UNAVAILABLE
        +503 Circuit Open: ERR_CIRCUIT_OPEN
        +504 Gateway Timeout: ERR_GATEWAY_TIMEOUT
    }

    class _Business_Errors {
        +200 Warning: ERR_WEAK_PASSWORD
        +200 Warning: ERR_OFFLINE_QUEUED
        +200 Warning: ERR_SESSION_EXPIRED
    }

    _4xx_Client_Errors --> _5xx_Server_Errors : escalates
    _5xx_Server_Errors --> _Business_Errors : degraded
```

## HTTP Status

- 200: Success
- 400: Validation error
- 401: Unauthenticated
- 403: Forbidden
- 404: Not found
- 409: Conflict
- 422: Pydantic validation
- 429: Rate limited
- 500: Internal error
- 503: Service unavailable

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 422 | Schema validation failed |
| UNAUTHORIZED | 401 | No valid auth |
| FORBIDDEN | 403 | Insufficient role |
| RATE_LIMITED | 429 | Too many requests |
| LLM_UNAVAILABLE | 503 | All providers failed |
| CIRCUIT_OPEN | 503 | Circuit breaker open |
| INVALID_TRANSITION | 400 | Invalid state transition |
| DUPLICATE_REQUEST | 409 | Idempotency replay |
| AUTH_EXPIRED | 401 | JWT expired |
| AUTH_INVALID | 401 | JWT invalid |

## Circuit Breaker

Closed - Open (30s) - Half-Open - Closed (probe success) or Open (probe fail)
