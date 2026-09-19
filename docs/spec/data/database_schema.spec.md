# Database Schema & Data Models Specification (SPEC)

> **Authority:** Authoritative Database Specification  
> **Source of Truth:** `backend/models/*.py`, `backend/scripts/app/supabase_migration.sql`  
> **Database Engine:** PostgreSQL 16 + PostGIS 3.4 Spatial Extension  
> **Status:** Production Normative (v1.0.0-STABLE)

---

## 1. Architectural Principles

1. **Spatial Geometry First:** All geographic positions, routes, and boundaries use PostGIS `Geometry('POINT', 4326)` or `Geometry('POLYGON', 4326)` columns with spatial R-tree GiST indexes.
2. **Longitude / Latitude Gotcha:** In PostGIS SQL functions (`ST_MakePoint`, `ST_Distance`), longitude MUST always precede latitude: `ST_MakePoint(longitude, latitude)`.
3. **Multi-Tenant Partitioning:** Core entities enforce multi-tenant isolation via `org_id: Mapped[str | None]` indexing.

---

## 2. Model Catalog (23 Active ORM Entities)

### 2.1 Core Identity & Access Management
- **`user_profiles` (`UserProfile` in `user.py`):** Citizen profiles (name, blood group, emergency contacts JSON, allergies, vehicle details, medical notes, org_id).
- **`operator_users` (`OperatorUser` in `user.py`):** Administrative and dispatcher credentials (email, hashed password, role enum, active status).

### 2.2 Emergency & Public Safety Subsystem
- **`emergency_services` (`EmergencyService` in `emergency.py`):** Hospitals, police stations, fire stations, trauma centers with `geom` spatial point.
- **`sos_incidents` (`SosIncident` in `sos_incident.py`):** Triggered citizen distress calls, dispatch status (`active`, `dispatched`, `resolved`, `cancelled`), location coordinates.
- **`officers` (`Officer` in `officer.py`):** On-ground patrol officers, badge IDs, vehicle types, live location coordinates.
- **`wards` (`Ward` in `ward.py`):** Municipal wards, polygons, boundary GeoJSON, and assigned ward inspectors.

### 2.3 Road Safety, Challans & Civic Intelligence
- **`road_issues` (`RoadIssue` in `road_issue.py`):** Civic hazard reports (potholes, waterlogging, broken signals), AI confidence score, severity rating.
- **`challan_records` (`ChallanRecord` in `challan.py`):** Motor Vehicles Act citations, penalty amounts, violation codes, payment statuses.
- **`streetlight_poles` (`StreetlightPole` in `streetlight_pole.py`):** Illumination network poles for nocturnal route safety calculations.
- **`municipalities` (`Municipality` in `municipality.py`):** City administrative units, coverage bounds, contact registries.
- **`city_centers` (`CityCenter` in `city_center.py`):** Hub coordinates for regional distance and dispatch clustering.
- **`admin_boundaries` (`AdminBoundary` in `admin_boundary.py`):** Multi-level spatial boundary geometries (State, District, Taluk).
- **`osm_civic_features` (`OsmCivicFeature` in `osm_civic_feature.py`):** OpenStreetMap points of interest and infrastructure nodes.
- **`municipal_features` (`MunicipalFeature` in `municipal_feature.py`):** Municipal assets (hydrants, speed breakers, cameras).
- **`lgd_entities` (`LgdEntity` in `lgd_entity.py`):** Local Government Directory standardized identifiers.
- **`gov_datasets` (`GovDataset` in `gov_dataset.py`):** Ingested Open Government Data (OGD) metadata and checksums.

### 2.4 Governance, Workflows & Notifications
- **`issue_reports` (`IssueReport` in `issue_report.py`):** Citizen complaint intake records and verification status.
- **`issue_timelines` (`IssueTimeline` in `issue_timeline.py`):** Event history of status transitions for civic reports.
- **`complaint_events` (`ComplaintEvent` in `complaint_event.py`):** Audit-logged state changes in complaint lifecycles.
- **`grievance_records` (`GrievanceRecord` in `grievance.py`):** Formally escalated citizen grievances and resolution SLAs.
- **`notifications` (`NotificationEvent` in `notification.py`):** Outbound multi-channel dispatch log (SMS, WebPush, WhatsApp, Email).
- **`provider_configs` (`ProviderConfig` in `provider_config.py`):** Multi-tenant LLM provider API credentials and rate limits.
- **`etl_run_logs` (`EtlRunLog` in `etl_run_log.py`):** Civic data pipeline ingestion runs, records added, and execution latencies.
- **`update_releases` (`UpdateRelease` in `update_management.py`):** Over-the-air firmware/bundle releases and integrity hashes.
