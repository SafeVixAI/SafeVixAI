# Runbook: Service Restart

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** SEV2 | **Service:** All | **Time to execute:** 2 minutes

## Symptoms
- Service unresponsive or returning 502/503
- OOM kill detected in logs
- Memory usage exceeding limits

## Steps

### 1. Check service status
```bash
# Render dashboard → check service logs
# Or locally:
docker ps | grep svai_
docker logs svai_backend --tail 50
```

### 2. Restart the affected service
```bash
# Docker Compose
docker compose restart backend     # or chatbot, frontend

# Single container
docker restart svai_backend
```

### 3. Check dependencies
```bash
# Verify PostgreSQL is running
docker exec svai_postgres pg_isready -U svai

# Verify Redis is running
docker exec svai_redis redis-cli -a "$REDIS_PASSWORD" ping
```

### 4. Verify health
```bash
curl http://localhost:8000/health   # Backend
curl http://localhost:8010/health   # Chatbot
curl http://localhost:3000/         # Frontend
```

### 5. If OOM kill suspected
```bash
# Check dmesg for OOM killer
dmesg | grep -i oom

# Increase memory limit in docker-compose.yml
# Or upgrade Render plan (free → Starter $7/mo)
```

## Prevention
- Monitor memory usage trends
- Set up alerts at 80% memory utilization
- Consider upgrading from free tier if OOM kills are frequent
