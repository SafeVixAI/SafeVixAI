# Scaling Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [Architecture.md](./Architecture.md), [DEPLOYMENT_STRATEGIES.md](./DEPLOYMENT_STRATEGIES.md), [ADVANCED_SETUP.md](./ADVANCED_SETUP.md)

---

## Horizontal vs Vertical Scaling

| Approach | Method | Benefits | Limits |
|----------|--------|----------|--------|
| **Horizontal** | Add more instances | Linear scalability, fault tolerance | State management, complexity |
| **Vertical** | Bigger instances | Simple, no code changes | Hardware cap, downtime for resize |

**Recommendation:** Start vertical, add horizontal as needed. Both backend and chatbot are stateless — ideal for horizontal.

---

## Stateless Service Design

Both backend and chatbot are stateless:

| Service | State | Externalized To |
|---------|-------|----------------|
| Backend | None (stateless) | PostgreSQL, Redis |
| Chatbot | None (stateless) | ChromaDB, Redis |

This means:
- Any instance can handle any request
- Add instances behind a load balancer
- No session affinity (sticky sessions) needed

---

## Database Scaling

### Connection Pooling
```python
# backend/core/config.py
DATABASE_POOL_SIZE = 20          # Per instance
DATABASE_MAX_OVERFLOW = 10       # Burst capacity
DATABASE_POOL_PRE_PING = True    # Verify connections
DATABASE_POOL_RECYCLE = 3600     # Recycle stale connections
```

### Read Replicas
Route read queries to replicas, writes to primary:
```python
# Read from replica
async with async_session(read_replica_url) as session:
    result = await session.execute(select(User))

# Write to primary
async with async_session(primary_url) as session:
    session.add(new_user)
    await session.commit()
```

### Connection Limits
| Instance Count | Pool Per Instance | Total Connections |
|---------------|------------------|------------------|
| 1 | 20 (+10 overflow) | 30 |
| 3 | 15 (+5 overflow) | 60 |
| 5 | 10 (+5 overflow) | 75 |
| 10 | 5 (+3 overflow) | 80 |

Database `max_connections` must be configured accordingly.

---

## Redis Scaling

### Sentinel (High Availability)
```
Client → Sentinel → Primary Redis
                → Replica Redis (failover target)
```

### Cluster (Sharding)
```
Client → Redis Cluster (3 masters, 3 replicas)
         ├── Shard 1: keys 0-5461
         ├── Shard 2: keys 5462-10922
         └── Shard 3: keys 10923-16383
```

**When to cluster:** > 10GB data or > 50K ops/sec

---

## Caching Strategies

### Cache-Aside (Lazy Loading)
```python
async def get_user(user_id: str) -> User:
    # Try cache first
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return User.parse_raw(cached)

    # Fall back to database
    user = await db.get(User, user_id)
    if user:
        await redis.set(f"user:{user_id}", user.json(), ex=3600)
    return user
```

### Write-Through
```python
async def update_user(user_id: str, data: dict) -> User:
    user = await db.update(User, user_id, data)
    await redis.set(f"user:{user_id}", user.json(), ex=3600)
    return user
```

### Stampede Protection
```python
# core/redis_client.py
async def get_json_with_stampede_protection(key, fetch_func, ttl=300, stale_ttl=3600):
    """SET NX EX mutex + stale-while-revalidate."""
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)

    # Try to acquire refresh lock
    lock_key = f"{key}:lock"
    locked = await redis.set(lock_key, "1", nx=True, ex=10)
    if locked:
        data = await fetch_func()
        await redis.set(key, json.dumps(data), ex=ttl)
        return data

    # Wait for the first request to complete
    await asyncio.sleep(0.1)
    cached = await redis.get(key)
    return json.loads(cached) if cached else await fetch_func()
```

---

## Rate Limiting at Scale

Use Redis-backed Token Bucket:
```python
# backend/core/limiter.py
class TokenBucket:
    def __init__(self, redis, key: str, capacity: int, refill_rate: float):
        self.redis = redis
        self.key = f"rate_limit:{key}"
        self.capacity = capacity
        self.refill_rate = refill_rate
```

Distributed rate limiting with consistent hashing ensures fairness across instances.

---

## Auto-Scaling Policies

### CPU-Based
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Request-Based
```yaml
  metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 1000
```

---

## Resource Estimation

### Per Instance
| Service | CPU | Memory | Disk | Network |
|---------|-----|--------|------|---------|
| Backend | 0.5-1 vCPU | 512MB-1GB | 1GB (logs) | Low |
| Chatbot | 1-2 vCPU | 2-4GB (torch) | 2GB (chroma) | Medium |
| Frontend | 0.5 vCPU | 512MB | 500MB | Low |
| PostgreSQL | 1-2 vCPU | 2-4GB | 10GB+ | Medium |
| Redis | 0.5 vCPU | 1-2GB | — | Low |

### Cost Projection (100K Users/Month)

| Service | Instances | Monthly Cost |
|---------|-----------|-------------|
| Frontend (Vercel Pro) | — | $20/mo |
| Backend (Render) | 3 × small | $25/mo |
| Chatbot (Render) | 2 × medium | $30/mo |
| PostgreSQL (Supabase Pro) | — | $25/mo |
| Redis (Upstash) | — | $10/mo |
| **Total** | | **~$110/mo** |

---

## CQRS for Write Scaling

The existing [CQRS event bus](./Architecture.md#cqrs) separates commands (writes) from queries (reads):

```
Command: POST /api/v1/roads/report → SubmitReportCommand → Event Bus → Handler → DB
Query:   GET /api/v1/roads/issues   → Direct DB read
```

Benefits:
- Scale reads and writes independently
- Offload write validation to command handlers
- Queue commands for async processing
