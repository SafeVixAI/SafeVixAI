# SafeVixAI — Operations Handbook

**Version:** 1.0.0
**Date:** 2026-07-21

---

## 1. Service Architecture

```
Frontend (Next.js 15, Port 3000)
  → Backend (FastAPI, Port 8000)
  → Chatbot (FastAPI, Port 8010)
  → PostgreSQL 16 + PostGIS (Port 5432)
  → Redis 7 (Port 6379)
```

## 2. Health Checks

| Service | Endpoint | Port |
|---------|----------|------|
| Frontend | `GET /` (200 OK) | 3000 |
| Backend | `GET /health` | 8000 |
| Chatbot | `GET /health` | 8010 |
| PostgreSQL | `pg_isready` | 5432 |
| Redis | `redis-cli ping` | 6379 |

## 3. Monitoring

### Prometheus Metrics
- Backend: `http://backend:8000/metrics`
- Chatbot: `http://chatbot:8010/metrics`
- PostgreSQL: `http://postgres-exporter:9187/metrics`
- Redis: `http://redis-exporter:9121/metrics`

### Grafana
- URL: `http://localhost:3001` (monitoring stack)
- Default credentials: `admin/admin`
- Provisioned dashboard: `SafeVixAI Overview`

### Alerting Rules
Defined in `monitoring/prometheus/alerts.yml`:
- **Critical**: Backend/Chatbot/Frontend/Redis/Postgres down, disk space <10%
- **Warning**: Memory >85%, CPU >80%, error rate >5%, p95 latency >2s

## 4. Logging

All services use structured JSON logging:
- Production: JSON format with `ts`, `level`, `logger`, `msg`, `request_id`
- Development: Human-readable console format
- Logs output to stdout/stderr (12-factor app pattern)

## 5. Backup

### Database
- Automated via `db-backup.yml` workflow
- Backups stored as GitHub Actions artifacts
- Restore: `psql DATABASE_URL < backup.sql`

### Application State
- No persistent app state (stateless architecture)
- Redis cache: ephemeral, repopulated on restart
- User uploads: `data/uploads/` volume mount

## 6. Running in Production

### Docker Compose
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes
```bash
kubectl apply -k k8s/
```

### Terraform (AWS)
```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

## 7. Scaling

| Service | Horizontal Scaling | Bottleneck |
|---------|-------------------|------------|
| Frontend | Stateless, any number of replicas | None |
| Backend | Stateless, Redis-backed rate limiting | PostgreSQL connections |
| Chatbot | Stateless, Redis-backed memory | GPU/LLM API rate limits |
| PostgreSQL | Read replicas for read-heavy workloads | Write throughput |
| Redis | Redis Cluster for large deployments | Memory |

## 8. Incident Response

See `docs/runbooks/` for detailed runbooks:
1. **LLM Outage** (RB-001): Fallback chain auto-activates
2. **DB Failover** (RB-002): Read replica promotion
3. **Rollback** (RB-005): Container rollback + DB migration downgrade
4. **All LLMs Down**: Email alert triggers, TemplateProvider acts as fallback
5. **Redis Down**: In-memory cache fallback
6. **Docker Down**: K8s alternative, or rebuild from source

## 9. Security Contacts

- **Security issues**: security@safevixai.gov.in
- **General inquiries**: safevixai@googlegroups.com
- **Vulnerability disclosure**: See SECURITY.md for timeline
