# Advanced Setup Guide

> **Audience:** DevOps engineers, platform administrators  
> **Last updated:** 2026-07-26  
> **Cross-references:** [Deployment.md](./Deployment.md), [Environment.md](./Environment.md), [Database.md](./Database.md)

---

## Production Deployment

### Architecture Overview

SafeVixAI consists of three independently deployable services:

| Service | Framework | Default Port | Platform |
|---------|-----------|-------------|----------|
| `frontend/` | Next.js 15 (App Router) | 3000 | Vercel / Docker |
| `backend/` | FastAPI | 8000 | Render.com / Docker |
| `chatbot_service/` | FastAPI | 8010 | Render.com / Docker |

### Production Checklist

- [ ] Environment secrets configured per service
- [ ] Database migrations applied: `alembic upgrade head`
- [ ] ChromaDB vectorstore built: `python data/build_vectorstore.py`
- [ ] CORS origins restricted to known domains
- [ ] Rate limiting enabled with Redis backend
- [ ] Health check endpoints registered in load balancer
- [ ] Log aggregation configured
- [ ] Backup schedule established
- [ ] SSL/TLS certificates provisioned
- [ ] Monitoring dashboards deployed

---

## High-Availability Configuration

### Service Redundancy

Deploy at least **2 instances** of each service behind a load balancer:

```yaml
# docker-compose.ha.yml
services:
  backend:
    deploy:
      replicas: 3
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 3
        window: 120s
  chatbot_service:
    deploy:
      replicas: 2
```

### Stateless Design

Both backend and chatbot_service are **stateless** — all state is externalized:

| State | Storage |
|-------|---------|
| User sessions | Redis (conversation memory, JWT blacklist) |
| Primary data | PostgreSQL (with PostGIS) |
| Caches | Redis (rate limits, distributed locks, JWKS) |
| Vector store | ChromaDB (persistent, committed to repo) |
| File uploads | Local `data/uploads/` (use S3 in HA) |

### Connection Pooling

```python
# backend/core/config.py
DATABASE_POOL_SIZE: int = 20
DATABASE_MAX_OVERFLOW: int = 10
DATABASE_POOL_PRE_PING: bool = True
DATABASE_POOL_RECYCLE: int = 3600
```

---

## Multi-Region Setup

### DNS-Based Routing
Use Route53 or Cloudflare DNS geo-routing to direct traffic to the nearest region.

### Database Topology
| Region | Role |
|--------|------|
| Primary | Read/Write |
| Secondary | Read replica (streaming replication) |

Reads → replicas, writes → primary.

### Redis Geo-Distribution
Use Redis Enterprise or ElastiCache Global Datastore for cross-region replication.

---

## Custom Domain Configuration

### Vercel (Frontend)
```bash
vercel domains add safevixai.com
vercel domains add app.safevixai.com
```

### Render (Backend/Chatbot)
Add CNAME records at DNS provider:
```
api.safevixai.com.  CNAME  your-service.onrender.com.
```

---

## SSL/TLS Setup

### Let's Encrypt (Docker)
```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - certs:/etc/letsencrypt

  certbot:
    image: certbot/certbot
    volumes:
      - certs:/etc/letsencrypt
    command: certonly --webroot --webroot-path=/var/www/html -d safevixai.com
```

---

## Load Balancer Configuration

### NGINX
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
}

server {
    listen 443 ssl;
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## CDN Configuration

Configure a CDN (Cloudflare, Fastly) in front of:

| Path | Origin | Cache TTL |
|------|--------|-----------|
| `/*.js`, `/*.css` | Vercel | 1 year |
| `/api/*` | Render | No cache |
| `/ws/*` | Render | No cache (WebSocket) |

---

## Monitoring Stack Setup

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    volumes:
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
```

---

## Backup Strategies

| Data | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| PostgreSQL | Daily | 30 days | `pg_dump` |
| File uploads | Hourly | 7 days | S3 sync |
| Redis | Optional | — | RDB snapshots |
| ChromaDB | Per release | — | Git LFS |

---

## Disaster Recovery

1. **Database failure**: Restore from latest backup, apply WAL replay
2. **Full region failure**: Switch DNS to secondary region, promote read replica
3. **Data corruption**: Restore from backup, replay write-ahead log
4. **Security incident**: Isolate affected service, rotate all secrets, restore from clean backup

See [docs/runbooks/](./runbooks/) for detailed incident response procedures.
