# SafeVixAI — Database Design

## Database: PostgreSQL 16 + PostGIS 3.4 (via Supabase)

**Why PostGIS?** `ST_DWithin` with GIST index finds records within a radius in **< 50ms** regardless of table size.

> **Critical Gotchas**
> - `ST_MakePoint` takes **longitude FIRST, latitude second** — opposite to `[lat, lon]` convention
> - Always use `::geography` (meters), never `::geometry` (degrees) in `ST_DWithin`
> - GIST index on all geometry columns for spatial performance
> - PostGIS extension must exist before Alembic migrations: `CREATE EXTENSION IF NOT EXISTS postgis;`

---

## Enable PostGIS (Run Once)

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SELECT PostGIS_version();
```

---

## ER Diagram

```mermaid
erDiagram
    users ||--o{ road_issues : "reports"
    users ||--o{ sos_incidents : "triggers"
    users ||--o{ challan_records : "incurs"
    users ||--o{ officers : "is"

    emergency_services {
        bigint id PK
        text name
        text category
        geometry location "GIST INDEX"
        text phone
        text city
    }

    users {
        uuid id PK
        varchar email UK
        varchar phone UK
        varchar password_hash
        varchar role
        boolean is_active
    }

    road_issues {
        bigint id PK
        uuid user_id FK
        text issue_type
        integer severity
        geometry location "GIST INDEX"
        text status
    }

    sos_incidents {
        bigint id PK
        uuid user_id FK
        geometry location "GIST INDEX"
        varchar status
    }

    challan_records {
        bigint id PK
        uuid user_id FK
        varchar violation_code
        integer fine_amount
        boolean paid
    }

    officers {
        bigint id PK
        uuid user_id FK "UNIQUE"
        varchar badge_number UK
        geometry jurisdiction "GIST INDEX"
        varchar department
    }

    wards {
        bigint id PK
        integer ward_number
        geometry boundary "GIST INDEX"
        integer municipality_id FK
    }
```

## ORM Models (23 Python model files in `backend/models/`)

All 23 model files are defined under `backend/models/` using SQLAlchemy ORM + GeoAlchemy2. The initial Alembic migration (`backend/migrations/versions/001_initial_schema.py`) creates 7 core tables; 31 database migrations add and manage tables, RLS policies, and PostGIS indexes.

**Migrations:**
| Migration | Tables Added |
|-----------|-------------|
| `001_initial_schema.py` | 7 core tables (users, emergency_services, road_issues, sos_incidents, officers, wards, challan_records) |
| `e7b9a1_indexes.py` | GiST index on `road_issues.location`, covering indexes on `status`, `category` |
| `10016_city_centers.py` | `city_centers` table for DB-backed metro center coordinates |

---

### 1. `users` (`user.py`) — User profiles & auth

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| email | VARCHAR | UNIQUE, NOT NULL |
| phone | VARCHAR | UNIQUE |
| password_hash | VARCHAR | NOT NULL |
| display_name | VARCHAR | |
| avatar_url | TEXT | |
| role | VARCHAR | DEFAULT 'citizen' |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

Emergency contacts are stored in a JSONB column or a separate relation — see `user.py` for details.

---

### 2. `emergency_services` (`emergency.py`) — Emergency service locations

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| name | TEXT | NOT NULL |
| category | TEXT | NOT NULL, INDEX (hospital, police, ambulance, fire, towing, puncture, showroom) |
| sub_category | TEXT | |
| location | GEOMETRY(Point,4326) | NOT NULL, **GIST INDEX** |
| phone | TEXT | |
| address | TEXT | |
| city | TEXT | |
| district | TEXT | |
| state | TEXT | |
| state_code | CHAR(2) | INDEX |
| country_code | CHAR(2) | DEFAULT 'IN' |
| is_24hr | BOOLEAN | DEFAULT true |
| has_trauma | BOOLEAN | DEFAULT false |
| has_icu | BOOLEAN | DEFAULT false |
| bed_count | INTEGER | |
| rating | FLOAT | CHECK 0–5 |
| source | TEXT | DEFAULT 'overpass' |
| raw_tags | JSONB | |
| verified | BOOLEAN | DEFAULT false |
| osm_id | BIGINT | UNIQUE |
| osm_type | TEXT | |
| last_updated | TIMESTAMP | DEFAULT NOW() |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

### 3. `road_issues` (`road_issue.py`) — Community road issue reports

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | UUID | FK → users.id |
| issue_type | TEXT | NOT NULL (pothole, flood, accident_prone, broken, missing_signage, no_lighting) |
| severity | INTEGER | CHECK 1–5 |
| description | TEXT | |
| location | GEOMETRY(Point,4326) | NOT NULL, **GIST INDEX** |
| location_address | TEXT | |
| road_name | TEXT | |
| road_type | TEXT | (NH, SH, MDR, village_road, urban) |
| road_number | TEXT | |
| photo_url | TEXT | |
| ai_detection | JSONB | |
| reporter_id | UUID | |
| authority_name | TEXT | |
| authority_phone | TEXT | |
| authority_email | TEXT | |
| complaint_ref | TEXT | |
| status | TEXT | DEFAULT 'open' |
| status_updated | TIMESTAMP | |
| uuid | UUID | UNIQUE, DEFAULT `gen_random_uuid()` |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

---

### 4. `challan_records` (`challan.py`) — Challan / fine records

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | UUID | FK → users.id |
| violation_code | VARCHAR | NOT NULL |
| vehicle_type | VARCHAR | |
| state | CHAR(2) | |
| fine_amount | INTEGER | NOT NULL |
| paid | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMP | DEFAULT NOW() |

Violation code definitions and state overrides are sourced from CSV files:
- `backend/data/violations_seed.csv` — Motor Vehicle Act violation codes, base fines, imprisonment
- `backend/data/state_overrides.csv` — State-specific fine overrides

---

### 5. `sos_incidents` (`sos_incident.py`) — SOS emergency incidents

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | UUID | FK → users.id |
| location | GEOMETRY(Point,4326) | NOT NULL, **GIST INDEX** |
| status | VARCHAR | DEFAULT 'active' (active, resolved, cancelled) |
| notes | TEXT | |
| created_at | TIMESTAMP | DEFAULT NOW() |
| resolved_at | TIMESTAMP | |

---

### 6. `officers` (`officer.py`) — Law enforcement officers

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | UUID | FK → users.id, UNIQUE |
| badge_number | VARCHAR | NOT NULL, UNIQUE |
| jurisdiction | GEOMETRY(Polygon,4326) | **GIST INDEX** |
| department | VARCHAR | |
| rank | VARCHAR | |
| status | VARCHAR | DEFAULT 'active' |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

### 7. `wards` (`ward.py`) — Administrative ward boundaries

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| ward_number | INTEGER | NOT NULL |
| ward_name | VARCHAR | |
| boundary | GEOMETRY(Polygon,4326) | **GIST INDEX** |
| municipality_id | INTEGER | FK → municipality.id |
| councilor_name | VARCHAR | |
| councilor_phone | VARCHAR | |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

### 8. `municipalities` (`municipality.py`) — Municipality / ULB details

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| name | VARCHAR | NOT NULL |
| ulb_type | VARCHAR | (municipal_corporation, municipality, town_panchayat) |
| state | VARCHAR | |
| district | VARCHAR | |
| contact_email | VARCHAR | |
| contact_phone | VARCHAR | |
| website | VARCHAR | |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

### 9. `municipal_features` (`municipal_feature.py`) — Municipal assets

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| municipality_id | INTEGER | FK → municipality.id |
| feature_type | VARCHAR | NOT NULL |
| location | GEOMETRY(Point,4326) | **GIST INDEX** |
| properties | JSONB | |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

### 10. `streetlight_poles` (`streetlight_pole.py`) — Streetlight inventory

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| pole_id | VARCHAR | |
| location | GEOMETRY(Point,4326) | **GIST INDEX** |
| ward_id | INTEGER | FK → wards.id |
| status | VARCHAR | DEFAULT 'operational' |
| light_type | VARCHAR | (LED, sodium, halogen) |
| pole_height_m | FLOAT | |
| installed_date | DATE | |
| last_maintenance | DATE | |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

### 11. `admin_boundaries` (`admin_boundary.py`) — Administrative polygons

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| level | VARCHAR | (state, district, taluk, block, village, ward) |
| name | VARCHAR | NOT NULL |
| code | VARCHAR | (e.g., state code, LGD code) |
| boundary | GEOMETRY(Polygon,4326) | **GIST INDEX** |
| parent_id | INTEGER | FK → admin_boundaries.id |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

### 12. `complaint_events` (`complaint_event.py`) — Grievance lifecycle events

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| grievance_id | INTEGER | FK → grievance.id |
| event_type | VARCHAR | NOT NULL (submitted, acknowledged, escalated, resolved, rejected) |
| notes | TEXT | |
| actor_id | UUID | FK → users.id |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

### 13. `grievances` (`grievance.py`) — Citizen grievances

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | UUID | FK → users.id |
| title | VARCHAR | NOT NULL |
| description | TEXT | |
| category | VARCHAR | |
| location | GEOMETRY(Point,4326) | **GIST INDEX** |
| ward_id | INTEGER | FK → wards.id |
| status | VARCHAR | DEFAULT 'open' |
| assigned_to | UUID | FK → users.id |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

---

### 14. `city_centers` (`city_center.py`) — Indian metro city centers

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PK |
| city | VARCHAR | NOT NULL, UNIQUE |
| state | VARCHAR | NOT NULL |
| lat | FLOAT | NOT NULL |
| lon | FLOAT | NOT NULL |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT NOW() |

Seeded by `scripts/data/seed_city_centers.py` with 9 Indian metros (Delhi, Mumbai, Bangalore, Chennai, Hyderabad, Kolkata, Pune, Ahmedabad, Jaipur).

---

### 15. `lgd_entities` (`lgd_entity.py`) — Local Government Directory

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| lgd_code | VARCHAR | NOT NULL, UNIQUE |
| name | VARCHAR | NOT NULL |
| entity_type | VARCHAR | (state, district, block, village, town, ward) |
| parent_lgd_code | VARCHAR | |
| state_code | CHAR(2) | |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT NOW() |

---

### 16. `osm_civic_features` (`osm_civic_feature.py`) — OSM civic features

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| osm_id | BIGINT | UNIQUE |
| feature_type | VARCHAR | NOT NULL |
| name | TEXT | |
| location | GEOMETRY(Point,4326) | **GIST INDEX** |
| tags | JSONB | |
| source | VARCHAR | DEFAULT 'overpass' |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

---

### 17. `gov_datasets` (`gov_dataset.py`) — Government data records

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| dataset_name | VARCHAR | NOT NULL |
| source_url | TEXT | |
| record_data | JSONB | NOT NULL |
| ingested_at | TIMESTAMP | DEFAULT NOW() |

---

### 18. `etl_run_logs` (`etl_run_log.py`) — ETL pipeline logs

| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| pipeline_name | VARCHAR | NOT NULL |
| status | VARCHAR | (running, success, failed) |
| records_processed | INTEGER | |
| error_message | TEXT | |
| started_at | TIMESTAMP | DEFAULT NOW() |
| completed_at | TIMESTAMP | |

---

## Alembic Migration: `001_initial_schema.py`

Creates 7 core tables with PostGIS support:

| Table | Key Spatial Column | Notes |
|---|---|---|
| `users` | — | Auth, no spatial data |
| `emergency_services` | location (Point,4326) GIST | Core lookup table |
| `road_issues` | location (Point,4326) GIST | Community reports |
| `challan_records` | — | Fine/payment records |
| `sos_incidents` | location (Point,4326) GIST | SOS events |
| `officers` | jurisdiction (Polygon,4326) GIST | Patrol boundaries |

All other tables are created via auto-migration or subsequent migration files.

#### Subsequent Migration: `e7b9a1_indexes.py` (GiST + Covering Indexes)

Adds GiST index on `road_issues.location` and covering indexes on `road_issues.status` and `road_issues.category` for query performance. Applied via `alembic upgrade head`.

#### Subsequent Migration: `10016_city_centers.py` (City Centers Table)

Creates `city_centers` table for DB-backed Indian metro coordinates. Seeds 9 cities via `scripts/data/seed_city_centers.py`. Depends on `eb59ee6949aa`.

---

## Violation Data (CSV — not in DB)

These files are consumed at runtime by DuckDB (server) and DuckDB-Wasm (client):

| File | Source | Contents |
|---|---|---|
| `backend/data/violations_seed.csv` | Motor Vehicles Act | 50+ violation codes, base fines, imprisonment, DL points |
| `backend/data/state_overrides.csv` | State transport depts. | State-specific fine overrides per violation code |

---

## ChromaDB Vectorstores

| Path | Git | Purpose |
|---|---|---|
| `chatbot_service/data/chroma_db/` | Committed | Pre-built for Render cold-start — never delete |
| `backend/data/chroma_db/` | Gitignored | Built locally (~10 min) — rebuild on PDF changes |

---

## Cache Keys (Redis)

| Key Pattern | TTL | Purpose |
|---|---|---|
| `emergency:category:{cat}:lat:{lat}:lon:{lon}:radius:{r}` | 3600s | Emergency service query results |
| `geocode:search:{query}` | 86400s | Forward geocoding results |
| `geocode:reverse:{lat}:{lon}` | 86400s | Reverse geocode (city/state from GPS) |
| `authority:lat:{lat}:lon:{lon}` | 3600s | Authority routing results |
| `route:{start}:{end}:{profile}` | 900s | Route calculation results |
| `ward:{ward_id}` | 3600s | Ward data cache |
| `tracking:{group_id}` | — | WebSocket live tracking groups (no TTL) |
| `circuit_breaker:{name}` | — | Circuit breaker state |
| `revoked_token:{jti}` | — | JWT token revocation set |
| `rate_limit:{ip}:{endpoint}` | — | Rate limit counters (sliding window) |
| `chat_session:{session_id}` | 86400s | Conversation memory |
| `sos_broadcast:{incident_id}` | — | SOS broadcast subscribers |

**Stampede Protection:** `get_json_with_stampede_protection()` uses `SET NX EX` mutex with 50ms retry + stale-while-revalidate fallback. Available for any cache key that recalculates from source data.

**Redis TLS:** Enabled via `REDIS_TLS_ENABLED=true` + `REDIS_PASSWORD=...` env vars. `get_redis_client()` auto-upgrades to `rediss://` when TLS is enabled.

---

## Key Performance Queries

### Nearby Emergency Services

```sql
SELECT id, name, category, phone, address,
  ST_Distance(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS distance
FROM emergency_services
WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
ORDER BY distance
LIMIT :limit;
```

**Radius Expansion Algorithm:**
Steps: 500m → 1000m → 5000m → 10000m → 25000m → 50000m
Min results: 3
If fewer than 3 found, expand to next radius step.

### Road Issues in Bounding Box

```sql
SELECT id, category, description, status, ST_AsGeoJSON(location) as geom, created_at
FROM road_issues
WHERE location && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
ORDER BY created_at DESC;
```

### SOS Incidents by User

```sql
SELECT id, ST_AsGeoJSON(location) as geom, status, created_at, resolved_at
FROM sos_incidents
WHERE user_id = :user_id
ORDER BY created_at DESC;
```

### Road Authority Lookup (within 100m of road)

```sql
SELECT road_type, road_number, contractor_name,
  exec_engineer, exec_engineer_phone,
  budget_sanctioned, budget_spent
FROM road_infrastructure
WHERE ST_DWithin(geometry::geography, ST_MakePoint(:lon, :lat)::geography, 100)
ORDER BY ST_Distance(geometry::geography, ST_MakePoint(:lon, :lat)::geography)
LIMIT 1;
```

---

*Document version: 3.3 | AI-powered road safety platform | July 2026 (Enterprise Hardening Batch 26)*

## Related

- [BENCHMARKS.md](../compliance-and-reports/BENCHMARKS.md) — Database performance benchmarks
- [TESTING.md](../developer-guide/TESTING.md) — Testing standards for data layer
- [SCALING_GUIDE.md](../sre/SCALING_GUIDE.md) — Horizontal scaling and replication
- [MIGRATION_GUIDE.md](../sre/MIGRATION_GUIDE.md) — Migration paths and procedures
