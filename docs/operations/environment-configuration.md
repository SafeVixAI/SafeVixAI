# Environment Configuration

## Environment Matrix

| Variable | Dev (local) | Staging | Production |
|----------|-------------|---------|------------|
| `ENVIRONMENT` | development | staging | production |
| `DATABASE_URL` | Local Postgres | Supabase staging | Supabase production |
| `REDIS_URL` | Localhost | Upstash staging | Upstash production |
| `CORS_ORIGINS` | `localhost:3000` | staging domain | production domain |
| `ADMIN_SECRET` | Dev secret | Staging secret | Production secret |
| `SENTRY_DSN` | (optional) | Staging DSN | Production DSN |

## Deployment Targets

| Service | Dev | Staging | Production |
|---------|-----|---------|------------|
| Frontend | `localhost:3000` | Vercel preview | safevixai.vercel.app |
| Backend | `localhost:8000` | Render preview | safevixai-api.onrender.com |
| Chatbot | `localhost:8010` | Render preview | safevixai-chatbot.onrender.com |
| Database | Local Postgres | Supabase staging | Supabase production |

## Certificate Rotation

- SSL/TLS certs managed automatically by Vercel (frontend) and Render (backend/chatbot)
- No manual cert rotation needed for standard deployments
- Custom domains: certs issued via Let's Encrypt (auto-renew)

## Backup Schedule

| Data | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| PostgreSQL | Daily | 30 days | `pg_dump` → S3 |
| Redis | Ephemeral | N/A | Rebuild from DB |
| User files (uploaded photos) | Continuous | 90 days | Supabase storage backup |
