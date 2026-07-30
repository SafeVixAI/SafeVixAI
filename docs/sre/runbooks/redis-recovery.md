# Runbook: Redis Recovery

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** SEV1 | **Service:** Backend + Chatbot | **Time to execute:** 5 minutes

## Symptoms
- Backend returning 500 errors
- Chatbot losing conversation history
- `ConnectionError` to Redis in logs
- Cache miss rate at 100%

## Steps

### 1. Check Redis status
```bash
docker exec svai_redis redis-cli -a "$REDIS_PASSWORD" ping
# Should return PONG
```

### 2. If Redis is down, restart
```bash
docker compose restart redis
# Wait for health check to pass
docker compose ps redis
```

### 3. Verify data persistence
```bash
# Check if data survived restart
docker exec svai_redis redis-cli -a "$REDIS_PASSWORD" DBSIZE
# Should show non-zero key count
```

### 4. If data is lost, rebuild cache
```bash
# Backend cache will rebuild on demand
# Chatbot conversation memory will rebuild as users chat
# No manual rebuild needed — both services handle Redis unavailability gracefully
```

### 5. Verify services
```bash
curl http://localhost:8000/health
curl http://localhost:8010/health
```

### 6. If Redis is corrupted
```bash
# Stop Redis
docker compose stop redis

# Clear data volume (WARNING: loses all cached data)
docker volume rm svai_redis_data

# Restart with clean state
docker compose up -d redis
```

## Prevention
- Monitor Redis memory usage: `INFO memory`
- Set maxmemory-policy: `allkeys-lru`
- Enable AOF persistence in production
- Set up alerts on Redis connectivity
