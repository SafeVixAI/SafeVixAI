# Runbook: OOM Kill Response

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** SEV1 | **Service:** All | **Time to execute:** 10 minutes

## Symptoms
- Service container exits with code 137
- `Killed` message in logs
- Service auto-restarts but crashes again
- Render shows "Crashed" status

## Steps

### 1. Confirm OOM kill
```bash
# Docker
docker inspect svai_backend | grep -i oom
# Look for "OOMKilled": true

# Linux
dmesg | grep -i "killed process"
```

### 2. Check memory usage before crash
```bash
# Render dashboard → Metrics → Memory
# Or docker stats if running locally
docker stats svai_backend svai_chatbot
```

### 3. Immediate fix: restart with more memory
```bash
# Docker Compose: edit docker-compose.yml
# Increase deploy.resources.limits.memory

# Render: upgrade plan
# Free (512MB) → Starter ($7/mo, 1GB) → Standard ($25/mo, 2GB)
```

### 4. If chatbot is the culprit (ML models)
```bash
# Chatbot with torch + transformers needs ~2GB minimum
# Ensure render.yaml has plan: standard for chatbot

# Or reduce model size:
# - Use smaller embedding model
# - Disable speech model if not needed
# - Use template provider instead of heavy LLMs
```

### 5. Long-term fixes
- Add memory profiling to identify leaks
- Implement connection pooling for DB
- Set up memory usage alerts at 80%
- Consider horizontal scaling for backend

## Prevention
| Service | Min Memory | Recommended |
|---------|-----------|-------------|
| Backend | 256MB | 512MB |
| Chatbot | 1GB | 2GB |
| Frontend | 128MB | 256MB |
| PostgreSQL | 256MB | 512MB |
| Redis | 64MB | 128MB |
