# Migration Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Applies to:** v0.x → v1.0  
> **Cross-references:** [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md), [CHANGELOG.md](../api-reference/api/changelog.md)

---

## Version Migration Paths

| From | To | Breaking Changes | DB Migration | Config Changes | Risk |
|------|----|-----------------|-------------|---------------|------|
| v0.1 | v0.2 | API prefix `/api/` → `/api/v1/` | `001_initial` | None | Low |
| v0.2 | v0.3 | Chat endpoint `/chat` → `/api/v1/chat/` | None | `CHATBOT_SERVICE_URL` added | Low |
| v0.3 | v0.4 | Leaflet removed → MapLibre GL | None | None | Medium |
| v0.4 | v0.5 | CQRS event bus, service refactor | `e7b9a1_indexes.py` | `REDIS_URL` optional | Medium |
| v0.5 | v0.6 | Provider registry restructured | None | API key renames | Low |
| v0.6 | v0.7 | City centers to DB | `10016_city_centers.py` | `ADMIN_SECRET` required | Medium |
| v0.7 | v0.8 | `sys.path` hacks removed | None | Python 3.11 minimum | Medium |
| v0.8 | v0.9 | Safety rules hardened | None | None | Low |
| v0.9 | v1.0 | Circuit breaker on 8 calls | None | `ALERT_EMAIL` added | Low |

---

## v0.1 → v0.2 (API Versioning)

**Breaking:** All endpoints moved from `/api/` to `/api/v1/`.

**Migration:**
1. Update frontend `NEXT_PUBLIC_BACKEND_URL` references
2. Update chatbot `MAIN_BACKEND_BASE_URL`
3. Update any external integrations

---

## v0.3 → v0.4 (Map Rendering)

**Breaking:** Leaflet removed, MapLibre GL is the only map provider.

**Migration:**
1. Replace `<MapContainer>` with MapLibre equivalents (`MapLibreCanvas`, `MapCore`)
2. Import `maplibre-gl/dist/maplibre-gl.css` in `layout.tsx`
3. Copy marker icons to `public/leaflet/`

---

## v0.4 → v0.5 (CQRS Event Bus)

**Breaking:** Service constructors replaced with CQRS commands/queries.

**Migration:**
1. Run `alembic upgrade head` for GiST indexes
2. Initialize CQRS via `init_cqrs_bus(app)` in `main.py`
3. Replace service calls with command dispatch via `get_cqrs_bus(request)`

---

## v0.6 → v0.7 (City Centers to DB)

**Breaking:** `CITY_CENTERS` constant removed from config.

**Migration:**
1. Run `alembic upgrade head` for migration `10016_city_centers.py`
2. Run `python scripts/data/seed_city_centers.py`
3. Set `ADMIN_SECRET` in production `.env`

---

## v0.7 → v0.8 (Import Cleanup)

**Breaking:** `sys.path` modifications removed.

**Migration:**
1. Remove any `sys.path.insert(0, ...)` calls
2. Use absolute package-relative imports
3. Ensure Python 3.11+

---

## v0.8 → v0.9 (Safety Rules)

**Non-breaking.** `HF_TOKEN` is now optional (was previously marked as required).

---

## v0.9 → v1.0 (Production Release)

**Non-breaking.** Adds circuit breakers, email alerting, and SBOM generation.

---

## Database Migration Procedures

### Apply Migrations
```bash
cd backend
alembic upgrade head
alembic current  # Verify
```

### Rollback
```bash
alembic downgrade -1         # One step
alembic downgrade <revision> # To specific revision
```

### Data Migration Scripts
| Script | Version | Purpose |
|--------|---------|---------|
| `scripts/data/seed_city_centers.py` | v0.7 | Populate city_center table |
| `scripts/app/seed_emergency.py` | v0.1 | Seed emergency services |
| `scripts/app/seed_nhp_hospitals.py` | v0.2 | Seed hospital data |
| `scripts/app/seed_healthsites.py` | v0.3 | Seed health facilities |

---

## Environment Variable Changes

| Version | Variable | Change |
|---------|----------|--------|
| v0.2 | `CHATBOT_SERVICE_URL` | Added |
| v0.5 | `REDIS_URL` | Now optional (in-memory fallback) |
| v0.6 | `OVERPASS_URLS` | Added (comma-separated) |
| v0.7 | `ADMIN_SECRET` | Optional → **Required** |
| v0.9 | `HF_TOKEN` | Required → Optional |
| v1.0 | `ALERT_EMAIL`, `ALERT_EMAIL_PASSWORD` | Added |

---

## Rollback Procedures

### Full Rollback
```bash
# 1. Revert database
cd backend && alembic downgrade <previous_revision>

# 2. Revert code
git checkout <previous_tag>

# 3. Rebuild and restart
docker compose up --build -d
```

### Service Rollback
```bash
docker pull safevixai/backend:<previous_tag>
docker tag safevixai/backend:<previous_tag> safevixai/backend:latest
docker compose up -d backend
```

---

## Testing After Migration

```bash
# Backend
cd backend && pytest tests/ -v --cov

# Chatbot
cd chatbot_service && pytest tests/ -v --cov

# Frontend
cd frontend && npm test
```

All tests must pass before declaring migration complete.
