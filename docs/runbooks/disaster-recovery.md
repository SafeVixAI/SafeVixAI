<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 SafeVixAI Team -->
# SafeVixAI Disaster Recovery Runbook

**Author:** DevOps Team  
**Last Updated:** 2026-07-19  
**Severity:** CRITICAL — refer to this runbook during any production incident

---

## 1. Recovery Priorities

| Priority | Service | RTO | RPO | Why |
|----------|---------|-----|-----|-----|
| **P0** | SOS / Emergency Locator | 5 min | 0 (real-time) | Life-safety critical |
| **P1** | Backend API | 15 min | 5 min | Core business logic |
| **P2** | Chatbot Service | 30 min | 15 min | AI assistance, falls back to template |
| **P3** | Frontend (Next.js PWA) | 1 hr | 0 (static) | Vercel CDN caches at edge |
| **P4** | Admin Dashboard | 2 hr | 15 min | Internal tool |

---

## 2. Database Recovery

### Prerequisites
```bash
# Ensure PostgreSQL client tools installed
sudo apt-get install postgresql-client
# Verify backup exists
ls -la backups/safevixai_*.sql.gz
```

### Full Restore from Latest Backup
```bash
# Step 1: Download latest backup from GitHub Actions artifacts
# Or restore from local:
TIMESTAMP="20260719_060000"
gunzip -k "backups/safevixai_${TIMESTAMP}.sql.gz"

# Step 2: Restore to production database
PGPASSWORD=$PROD_DB_PASSWORD pg_restore \
  -h $PROD_DB_HOST \
  -U $PROD_DB_USER \
  -d $PROD_DB_NAME \
  --no-owner --no-acl \
  --clean --if-exists \
  "backups/safevixai_${TIMESTAMP}.sql"

# Step 3: Run migrations forward (if backup is older than current schema)
cd backend
alembic upgrade head

# Step 4: Verify
python scripts/verify-backup.py --backup "backups/safevixai_${TIMESTAMP}.sql.gz"
```

### Point-in-Time Recovery (PITR)
Supabase supports PITR with 7-day retention:
```sql
-- Supabase dashboard → Database → Backups → Point-in-Time Recovery
-- Select timestamp before the incident
-- Target: a new database instance
-- Then switch DATABASE_URL to the new instance
```

### Data Corruption Recovery
```bash
# 1. Take production offline (maintenance page)
# 2. Restore to a parallel DB instance
# 3. Verify data integrity with queries
PGPASSWORD=$PROD_DB_PASSWORD psql -h $PROD_DB_HOST -U $PROD_DB_USER -d restored_db -c "
  SELECT schemaname, tablename, n_live_tup 
  FROM pg_stat_user_tables 
  ORDER BY n_live_tup DESC;
"
# 4. Point DATABASE_URL to restored instance
# 5. Verify SOS/emergency endpoints work
curl -f http://localhost:8000/health
curl -f http://localhost:8000/api/v1/emergency/nearby?lat=13.08&lon=80.27
```

---

## 3. Redis Failure

Redis is **not on the critical path** — all services fall back to in-memory caching.

### Symptoms
- `/health` endpoint shows `redis: "unhealthy"` with `redis_cached: true`
- Chatbot falls back to in-memory conversation memory
- Rate limiting falls back to in-memory counters

### Recovery Steps
```bash
# 1. Check Redis service
docker compose ps redis
docker compose logs redis

# 2. Restart Redis
docker compose restart redis

# 3. Verify reconnection
curl -f http://localhost:8000/health | python -c "import json,sys; print(json.load(sys.stdin)['redis'])"
```

**No manual intervention needed** — app auto-recovers within 1 health check cycle (30s).

---

## 4. LLM Provider Outage

SafeVixAI uses a 10-provider fallback chain. A single provider outage is transparent.

### Symptoms
- `/health` shows some providers as `unhealthy`
- Chatbot responses slower (timeout + cascade)
- Alert email sent via `core/alert.py`

### Recovery Steps
```bash
# 1. Check which providers are down
curl -sf http://localhost:8000/health | python -m json.tool

# 2. If ALL 10 providers are down:
#    - Chatbot falls back to TemplateProvider (deterministic)
#    - Users get accurate but non-LLM responses
#    - Fix: check API keys in chatbot_service/.env

# 3. If one provider is consistently failing:
#    - Add it to the EXCLUDED_PROVIDERS list in chatbot_service/config.py
#    - Or let the circuit breaker handle it automatically
```

**No manual intervention needed** — fallback chain handles up to 8 providers failing.

---

## 5. Frontend CDN Failure

Vercel has built-in CDN failover. Manual action is rarely needed.

### Symptoms
- Users report "Page not loading" but app is functional
- DNS resolves to different edge nodes depending on region

### Recovery Steps
```bash
# 1. Check Vercel status
curl -f https://www.vercel-status.com

# 2. Force redeployment
curl -X POST "https://api.vercel.com/v1/deployments" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "safevixai", "gitSource": {"ref": "main"}}'

# 3. Alternative: Serve from static backup
#    Build and serve locally as a fallback
npm run build
npm start -- -p 4000  # Fallback port
```

---

## 6. Complete Region Failure (AWS ap-south-1)

### Prerequisites
- Secondary region configured in `terraform/`
- ECR images replicated to secondary region
- DNS failover configured

### Failover Steps
```bash
# 1. Update k8s deployment to secondary region
kubectl config use-context safevixai-dr
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/chatbot-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# 2. Verify all pods are healthy
kubectl -n safevixai get pods
kubectl -n safevixai rollout status deployment/backend
kubectl -n safevixai rollout status deployment/chatbot

# 3. Update DNS to point to secondary region
#    Route53: update A record to secondary LB

# 4. Verify end-to-end
curl -f https://app.safevixai.com/health
```

---

## 7. Recovery Checklist

Use this checklist during any incident. Check off items as completed.

### Immediate (0-5 min)
- [ ] Acknowledge incident in team channel
- [ ] Assess severity: P0 (life-safety) vs P1-P4
- [ ] If P0: Enable SOS offline mode (already auto-enabled)
- [ ] Check `/health` endpoint
- [ ] Check Redis status
- [ ] Check database connectivity
- [ ] Check LLM provider availability

### Short-term (5-30 min)
- [ ] Restore database if corrupted
- [ ] Restart failed services
- [ ] Verify SOS endpoint functional
- [ ] Verify emergency numbers loadable
- [ ] Notify users via PWA push notification (if needed)

### Recovery (30 min - 2 hr)
- [ ] Full database restore (if applicable)
- [ ] Run `python scripts/verify-backup.py`
- [ ] Verify chatbot responses
- [ ] Verify frontend loads
- [ ] Run E2E smoke tests
- [ ] Post-mortem document initiated

### Post-recovery
- [ ] Reduce RTO for future incidents
- [ ] Add monitoring alert if gap found
- [ ] Update this runbook
- [ ] Schedule chaos engineering test

---

## 8. Emergency Contacts

| Role | Contact | Escalation Time |
|------|---------|-----------------|
| On-call Engineer | PagerDuty / Slack | Immediate |
| Backend Lead | Slack @backend-lead | 15 min |
| DevOps Lead | Slack @devops-lead | 15 min |
| Database Admin | Slack @dba | 30 min |
| Security Lead | Slack @security | 30 min |

---

## 9. Testing Schedule

| Test Type | Frequency | Tool | Success Criteria |
|-----------|-----------|------|-----------------|
| Database restore | Weekly (Mon) | `scripts/verify-backup.py` | All tables recoverable |
| Redis failover | Monthly | Chaos engineering workflow | In-memory fallback activates |
| LLM provider cascade | Monthly | Integration tests | All 10 providers route correctly |
| Full DR drill | Quarterly | Manual | < 1hr RTO for P0 services |
