# SafeVixAI — Runbook: Deployment Rollback

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** Varies  
**Service:** Any  
**Last Updated:** 2026-05-18

---

## When to Roll Back
- New deployment causes > 5% error rate spike
- Critical functionality broken (SOS, emergency locator, auth)
- Database migration failed and left schema in broken state

## Rollback Steps — Render Services

### Backend / Chatbot Service
1. Go to **Render dashboard** → select the broken service
2. Click **"Deploys"** tab
3. Find the last known-good deploy (use timestamps; check commit message)
4. Click **"Re-deploy"** on that deploy
5. Wait for deployment to go `Live`
6. Validate: `GET /health` → `{"status": "ok"}`

### Frontend (Vercel)
1. Go to **Vercel dashboard** → SafeVixAI project
2. Click **"Deployments"** tab
3. Find the last known-good deployment
4. Click **⋮ → Promote to Production**
5. Validate: check the app loads and `/sos` page works

## Database Migration Rollback
> ⚠️ Only if a bad Alembic migration was deployed

```bash
# SSH into Render shell (or run locally with production DATABASE_URL)
cd backend
alembic downgrade -1   # roll back one migration
```

> Check `alembic/versions/` to verify which migration is being rolled back.

## Post-Rollback Actions
- [ ] Create incident report (see incident-response.md)
- [ ] Document which commit caused the issue
- [ ] Open a post-mortem issue in GitHub
- [ ] Fix the root cause before re-deploying

## RTO: 10 minutes for Render/Vercel rollback
