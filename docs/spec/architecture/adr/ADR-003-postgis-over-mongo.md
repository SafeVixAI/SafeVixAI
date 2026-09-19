# ADR-003: PostGIS for Geospatial Queries

**Date:** 2026-05-21  
**Status:** ✅ Accepted  
**Author:** SafeVixAI Backend Team  

## Context

The app needs radius-based geospatial queries for:
- Emergency services near a location (hospital, police, ambulance)
- Road issue reporting by area
- Officer assignment by ward boundary
- Live family tracking with geo-fencing

All queries need to be fast (<100ms), accurate (meter-level), and run on a free-tier budget.

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **PostGIS (chosen)** | PostgreSQL extension for spatial data | <50ms ST_DWithin queries, ACID compliance, free | Requires PostGIS extension |
| **MongoDB** | Native geospatial 2dsphere index | Easy to start with | No JOINs, separate stack to maintain, cost |
| **Elasticsearch** | Geo-distance queries on search index | Great for full-text + geo combined | Overhead, cost, complexity |

## Decision

Use PostgreSQL 16 + PostGIS 3.4 with the `ST_MakePoint(lon, lat)::geography` pattern.

All spatial queries use the `geography` type for meter-based distances. A GiST index is created on all geography columns.

## Consequences

- `ST_MakePoint(lon, lat)` — longitude FIRST, NOT latitude (common mistake)
- `::geography` cast for meter distances (not `::geometry` which uses degrees)
- GiST index on geography columns for fast radius searches
- All DB instances must have PostGIS extension installed before migrations
- Alembic migration `001_initial_schema.py` creates the extension with `CREATE EXTENSION IF NOT EXISTS postgis;`
