# Upgrade Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md), [CHANGELOG.md](../CHANGELOG.md), [Deployment.md](./Deployment.md)

---

## Before You Start

1. **Read the changelog** — Review [CHANGELOG.md](../CHANGELOG.md) for all changes between versions
2. **Check for breaking changes** — See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for breaking changes
3. **Back up your database** — Always take a backup before upgrading
4. **Review environment variables** — Check for new or changed variables

---

## Step-by-Step Upgrade

### 1. Check Current Version
```bash
# Backend
cd backend && python -c "from core.config import Settings; print(Settings().VERSION)"

# Frontend
cd frontend && cat package.json | grep '"version"'
```

### 2. Pull Latest Code
```bash
git fetch origin
git checkout tags/v1.0.0  # Or the target version tag
```

### 3. Back Up Database
```bash
pg_dump -h localhost -U postgres -d safevixai > backup_$(date +%Y%m%d).sql
```

### 4. Update Dependencies
```bash
# Backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Chatbot
cd ../chatbot_service
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Frontend
cd ../frontend
npm ci  # Clean install from lockfile
```

### 5. Update Configuration
Compare your `.env` files with `.env.example`:
```bash
cd backend
diff .env .env.example
```

Add any new variables from the example file.

### 6. Run Database Migrations
```bash
cd backend
alembic upgrade head
alembic current  # Verify at latest
```

### 7. Run Seed Scripts (if any)
```bash
cd backend
python scripts/data/seed_city_centers.py  # If migration 10016 is new
```

### 8. Run Tests
```bash
cd backend && pytest tests/ -v --cov
cd ../chatbot_service && pytest tests/ -v --cov
cd ../frontend && npm test && npm run lint
```

### 9. Deploy
```bash
# Docker
docker compose up --build -d

# Or manually start services
# Backend
cd backend && uvicorn main:app --port 8000

# Chatbot
cd ../chatbot_service && uvicorn main:app --port 8010

# Frontend
cd ../frontend && npm run build && npm start
```

### 10. Verify
```bash
curl http://localhost:8000/health
curl http://localhost:8010/health
# Open http://localhost:3000
```

---

## Post-Upgrade Checklist

- [ ] All services report healthy via `/health`
- [ ] Database migrations at correct revision
- [ ] All environment variables set correctly
- [ ] Frontend loads without errors (check browser console)
- [ ] API endpoints return expected responses
- [ ] Chatbot responds to queries
- [ ] SOS flow works end-to-end
- [ ] Challan calculator returns correct results
- [ ] Road report submission works
- [ ] Offline mode functions (test with DevTools offline mode)

---

## Rollback

If the upgrade fails:

### Quick Rollback (Docker)
```bash
# Revert to previous Docker images
docker compose down
docker compose up -d  # Uses previous images
```

### Database Rollback
```bash
cd backend
alembic downgrade -1  # Undo last migration
```

### Full Rollback
```bash
git checkout <previous_tag>
cd backend && pip install -r requirements.txt
cd ../chatbot_service && pip install -r requirements.txt
cd ../frontend && npm ci
# Restart services
```

---

## Common Upgrade Issues

| Issue | Solution |
|-------|----------|
| Alembic migration fails | Check database connection, run `alembic current` and `alembic history` |
| Module not found | Reinstall dependencies: `pip install -r requirements.txt` |
| API returns 404 | Check API prefix (use `/api/v1/` not `/api/`) |
| Frontend build error | Clear `.next/` and rebuild: `rm -rf .next && npm run build` |
| WebSocket disconnects | Update token (JWKS may have rotated) |

---

## Need Help?

- Check [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) for common issues
- Search [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues)
- Ask in [GitHub Discussions](https://github.com/SafeVixAI/SafeVixAI/discussions)
