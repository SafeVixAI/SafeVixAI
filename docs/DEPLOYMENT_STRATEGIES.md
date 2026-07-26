# Deployment Strategies

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [Deployment.md](./Deployment.md), [ADVANCED_SETUP.md](./ADVANCED_SETUP.md), [SCALING_GUIDE.md](./SCALING_GUIDE.md)

---

## Overview

SafeVixAI supports multiple deployment strategies. Choose the one that matches your risk tolerance and operational maturity.

---

## Blue-Green Deployment

Two identical environments ("blue" and "green") — traffic switches between them.

```
User → Load Balancer → Blue (live)     → Database
                     → Green (standby)  → Database
```

**Switch**: Update load balancer to point to Green.
**Rollback**: Switch back to Blue.

**Pros**: Zero downtime, instant rollback.
**Cons**: Double infrastructure cost during deployment.

---

## Canary Releases

Gradually shift traffic to the new version:

| Phase | Traffic to New Version | Duration | Validation |
|-------|----------------------|----------|------------|
| 1 | 10% | 15 min | Error rate < 0.1% |
| 2 | 25% | 30 min | Latency p95 < baseline + 10% |
| 3 | 50% | 1 hour | All metrics stable |
| 4 | 100% | — | Full rollout |

**Rollback**: Immediately route all traffic back to the old version.

**Pros**: Risk mitigation, real-world validation.
**Cons**: Slower rollout, needs sophisticated load balancer.

---

## Rolling Updates

Update instances one at a time:

```yaml
# Kubernetes
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

**Pros**: No additional infrastructure, gradual.
**Cons**: Mixed versions during update, slower rollback.

---

## Zero-Downtime Migrations

### Schema Changes
- **Additive changes** (new columns, new tables): Safe to deploy anytime
- **Destructive changes** (drop columns, rename): Require multi-phase migration

### Multi-Phase Migration Pattern
```
Phase 1: Add new column (both old and new code work)
Phase 2: Deploy code that writes to both, reads from new
Phase 3: Backfill old data
Phase 4: Remove old column
```

### Safe DDL Operations
```sql
-- Safe (additive)
ALTER TABLE road_issues ADD COLUMN severity INTEGER;

-- Requires care
ALTER TABLE road_issues ALTER COLUMN status SET NOT NULL;
-- Must ensure all rows have non-null status before running

-- Multi-phase
-- Phase 1: Add new column + write to both
-- Phase 2: Migrate old data
-- Phase 3: Drop old column
ALTER TABLE road_issues DROP COLUMN old_status;
```

---

## Feature Flags

Use environment variables or a feature flag service:

```python
# backend/core/feature_flags.py
FEATURE_FLAGS = {
    "bystander_v2": os.getenv("FEATURE_BYSTANDER_V2", "false").lower() == "true",
    "offline_ai_v2": os.getenv("FEATURE_OFFLINE_AI_V2", "false").lower() == "true",
}
```

**Best practices:**
- Short-lived flags (remove after rollout)
- Flag names in feature_flag registry
- Log flag state at startup
- Test with flags both on and off

---

## A/B Testing

Use PostHog or a similar platform for frontend experiments:
```typescript
// Frontend A/B test
const variant = useFeatureFlag('new-sos-button');
return variant === 'v2' ? <SosButtonV2 /> : <SosButton />;
```

---

## Environment Promotion

```
Dev (manual deploy) → Staging (auto-deploy from PR) → Production (manual deploy from main)
```

| Environment | Deploy Trigger | Data | Monitoring |
|-------------|---------------|------|------------|
| Dev | Local/Manual | Dummy | Minimal |
| Staging | PR merge to main | Anonymized prod copy | Full |
| Production | Manual release | Real | Full + Alerting |

---

## Branch-Based Deployments

- **Vercel**: Every PR gets a preview deployment
- **Render**: Branch-based previews for backend/chatbot
- URL: `pr-123.safevixai.vercel.app`

---

## Release Trains

For planned releases:
1. Feature freeze at `T-7 days`
2. Release branch `release/v1.x.0`
3. Bug fix PRs only to release branch
4. Regression testing (CI + manual)
5. Tag and deploy at `T-0`

---

## Rollback Procedures

### Docker
```bash
docker pull safevixai/backend:<previous-tag>
docker tag safevixai/backend:<previous-tag> safevixai/backend:latest
docker compose up -d backend
```

### Kubernetes
```bash
kubectl rollout undo deployment/backend -n safevixai
kubectl rollout status deployment/backend -n safevixai
```

### Database
```bash
cd backend && alembic downgrade -1
```

See [docs/runbooks/deployment-rollback.md](./runbooks/deployment-rollback.md) for detailed rollback procedures.
