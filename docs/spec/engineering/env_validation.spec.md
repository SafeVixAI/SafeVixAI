# SafeVixAI â€" Environment Variable Validation

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

**Date:** 2026-05-18
**OPS#11 FIX: Startup validation for all required env vars**

---

## Backend Required Variables

| Variable | Required | Default | Validation |
|----------|----------|---------|------------|
| `DATABASE_URL` | Yes | None | Must be valid PostgreSQL URL |
| `REDIS_URL` | No | None | Must be valid Redis URL if set |
| `CHATBOT_SERVICE_URL` | Yes | `http://localhost:8010/api/v1` | Must be valid URL |
| `ADMIN_SECRET` | Yes (for MCP) | None | Min 16 chars if set |
| `CORS_ORIGINS` | Yes | `*` | Must not be `*` in production |
| `SENTRY_DSN` | No | None | Must be valid Sentry DSN if set |

## Chatbot Required Variables

| Variable | Required | Default | Validation |
|----------|----------|---------|------------|
| `DEFAULT_LLM_PROVIDER` | Yes | `groq` | Must be valid provider name |
| `DEFAULT_LLM_MODEL` | Yes | None | Must be non-empty |
| `REDIS_URL` | No | None | Must be valid Redis URL if set |
| `MAIN_BACKEND_BASE_URL` | Yes | `http://localhost:8000` | Must be valid URL |
| `CORS_ORIGINS` | Yes | `http://localhost:3000` | Must not contain `*` in production |
| `SENTRY_DSN` | No | None | Must be valid Sentry DSN if set |

## Frontend Required Variables

| Variable | Required | Default | Validation |
|----------|----------|---------|------------|
| `NEXT_PUBLIC_BACKEND_URL` | Yes | `http://localhost:8000` | Must be valid URL |
| `NEXT_PUBLIC_CHATBOT_URL` | Yes | `http://localhost:8010` | Must be valid URL |
| `NEXT_PUBLIC_SENTRY_DSN` | No | None | Must be valid Sentry DSN if set |

---

## Startup Validation Script

### Backend (`backend/scripts/validate_env.py`)
```python
#!/usr/bin/env python3
"""Validate all required environment variables at startup."""
import os
import sys
from urllib.parse import urlparse

def validate():
    errors = []
    
    # DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        errors.append("DATABASE_URL is required")
    elif not db_url.startswith(("postgresql://", "postgresql+asyncpg://")):
        errors.append("DATABASE_URL must be a PostgreSQL URL")
    
    # CHATBOT_SERVICE_URL
    chatbot_url = os.getenv("CHATBOT_SERVICE_URL", "http://localhost:8010/api/v1")
    try:
        urlparse(chatbot_url)
    except Exception:
        errors.append("CHATBOT_SERVICE_URL must be a valid URL")
    
    # CORS_ORIGINS in production
    if os.getenv("ENVIRONMENT") == "production":
        cors = os.getenv("CORS_ORIGINS", "*")
        if cors == "*":
            errors.append("CORS_ORIGINS must be explicit in production")
    
    if errors:
        print("âŒ Environment validation failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    
    print("âœ... Environment validation passed")

if __name__ == "__main__":
    validate()
```

### Chatbot (`chatbot_service/scripts/validate_env.py`)
```python
#!/usr/bin/env python3
"""Validate all required environment variables at startup."""
import os
import sys
from urllib.parse import urlparse

VALID_PROVIDERS = {"groq", "gemini", "cerebras", "sarvam", "template", "mistral", "together", "openrouter", "nvidia"}

def validate():
    errors = []
    
    # DEFAULT_LLM_PROVIDER
    provider = os.getenv("DEFAULT_LLM_PROVIDER", "groq").lower()
    if provider not in VALID_PROVIDERS:
        errors.append(f"DEFAULT_LLM_PROVIDER must be one of: {VALID_PROVIDERS}")
    
    # DEFAULT_LLM_MODEL
    model = os.getenv("DEFAULT_LLM_MODEL")
    if not model:
        errors.append("DEFAULT_LLM_MODEL is required")
    
    # MAIN_BACKEND_BASE_URL
    backend_url = os.getenv("MAIN_BACKEND_BASE_URL", "http://localhost:8000")
    try:
        urlparse(backend_url)
    except Exception:
        errors.append("MAIN_BACKEND_BASE_URL must be a valid URL")
    
    # CORS_ORIGINS in production
    if os.getenv("ENVIRONMENT") == "production":
        cors = os.getenv("CORS_ORIGINS", "")
        if "*" in cors:
            errors.append("CORS_ORIGINS must not contain * in production")
    
    if errors:
        print("âŒ Environment validation failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    
    print("âœ... Environment validation passed")

if __name__ == "__main__":
    validate()
```

---

## Integration with Startup

### Backend (render.yaml)
```yaml
preDeployCommand: "python scripts/validate_env.py && alembic upgrade head"
```

### Chatbot (render.yaml)
```yaml
preDeployCommand: "python scripts/validate_env.py"
```
