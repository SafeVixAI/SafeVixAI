# Rollback Strategy

This document defines the rollback procedures for each component of the SafeVixAI platform.

## Database Rollback

Alembic manages all database schema migrations. To revert to a previous version:

```bash
cd backend
# Check current revision
alembic current

# List migration history
alembic history

# Roll back one step
alembic downgrade -1

# Roll back to a specific revision
alembic downgrade <revision_id>

# Roll back to the beginning (all migrations)
alembic downgrade base
```

**Data loss warning:** `downgrade` reverses schema changes but does not restore data removed by a migration. Always take a database snapshot before running migrations in production:
```bash
pg_dump -Fc -U postgres safevixai > safevixai_$(date +%Y%m%d_%H%M%S).dump
```

## Frontend Rollback

Next.js app deployed on Vercel:

1. **Vercel Dashboard** — Instant rollback to any previous deployment:
   - Go to Vercel Dashboard > Deployments
   - Find the last known-good deployment
   - Click the "..." menu > "Promote to Production"
   - Rollback completes in <30 seconds

2. **Vercel CLI**:
   ```bash
   npx vercel rollback <deployment-url>
   ```

3. **Git revert** — Revert the commit and push to `main`:
   ```bash
   git revert HEAD
   git push origin main
   ```
   Vercel auto-deploys the reverted commit.

## Backend / Chatbot Rollback

FastAPI services deployed on Render.com:

1. **Render Dashboard** — Deploy rollback:
   - Go to Render Dashboard > select service
   - Click "Manual Deploy" > "Deploy latest image"
   - Or use "Revert to previous deploy" from deploy history

2. **Render CLI**:
   ```bash
   render deploy --service <service-id> --commit <previous-commit-sha>
   ```

3. **Docker rollback** — Revert the Docker image tag:
   ```bash
   docker pull ghcr.io/safevixai/backend:<previous-tag>
   docker tag ghcr.io/safevixai/backend:<previous-tag> ghcr.io/safevixai/backend:latest
   docker push ghcr.io/safevixai/backend:latest
   ```

## CI/CD Rollback

GitHub Deployment API provides programmatic rollback:

```bash
# Get the deployment ID of the last successful deployment
gh deployment list --repo <owner>/<repo> --environment production --json id

# Re-run the workflow with the previous commit
gh workflow run <workflow-id> --ref <previous-commit-sha>
```

For automated rollback on CI failure, configure in `.github/workflows/deploy.yml`:
```yaml
on:
  workflow_run:
    workflows: ["Deploy"]
    types:
      - completed
    branches:
      - main
```

Rollback via GitHub Actions on failure can be added using `actions/github-script` to trigger deployment of the previous build artifact.

## Full Stack Rollback

When a coordinated rollback across all services is needed:

```bash
# Tear down the production stack
docker compose -f docker-compose.prod.yml down

# Rebuild and start the verified baseline stack
docker compose -f docker-compose.yml up --build -d
```

This approach assumes `docker-compose.yml` contains the last stable, verified configuration. Pin specific image tags for reproducibility:

```yaml
services:
  backend:
    image: ghcr.io/safevixai/backend:v1.2.3
  chatbot:
    image: ghcr.io/safevixai/chatbot:v1.2.3
  frontend:
    image: ghcr.io/safevixai/frontend:v1.2.3
```

## Pre-Rollback Checklist

Before initiating any rollback:

- [ ] Confirm the severity and blast radius of the incident
- [ ] Identify the last known-good deployment/commit
- [ ] Verify database compatibility (schema must match the rolled-back code)
- [ ] Communicate rollback plan to the team
- [ ] Monitor rollback execution for errors
- [ ] Verify health checks pass after rollback completes
- [ ] Post-incident: create a fix forward ticket to address the root cause
