# SafeVixAI â€" Staging Environment Configuration

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

#
# This file documents how to set up and use a staging environment
# on Render (or any other platform) for pre-production testing.

## Purpose
- Test database migrations before production
- Validate new LLM provider integrations
- Run E2E tests against a real backend
- Demo to stakeholders without affecting production data

## Render Staging Setup

### 1. Create Staging Services
- Clone production services with `-staging` suffix
- Use separate Supabase project (or separate schema)
- Use separate Upstash Redis instance

### 2. Environment Variables
Copy production `.env` values and modify:
```
ENVIRONMENT=staging
DATABASE_URL=postgresql+asyncpg://...  # staging DB
REDIS_URL=redis://...                   # staging Redis
ADMIN_SECRET=<different-from-production>
SENTRY_DSN=<staging-sentry-dsn>
ALERT_EMAIL=<staging-alert-email>
```

### 3. Branch Protection
- Staging deploys from `develop` branch
- Production deploys from `main` branch
- PR required to merge `develop` â†' `main`

### 4. Data Seeding
```bash
# Seed staging with anonymized production data
cd backend && python scripts/app/seed_db.py --staging
cd backend && python scripts/app/seed_emergency.py --staging
cd chatbot_service && python data/build_vectorstore.py
```

### 5. Smoke Tests
```bash
# Run post-deploy smoke tests against staging
curl -f https://safevixai-staging.onrender.com/health
curl -f https://safevixai-chatbot-staging.onrender.com/health
curl -f https://safevixai-staging.vercel.app/api/health
```

## Local Staging
For local testing, use `docker-compose.yml` with:
```bash
ENVIRONMENT=staging docker compose up --build
```

## Promotion to Production
1. Run smoke tests against staging
2. Review Sentry error dashboard
3. Check provider health dashboard
4. Merge `develop` â†' `main` via PR
5. Production auto-deploys from `main`
