# SafeVixAI: Disaster Recovery Plan

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

## 1. High Availability Architecture
SafeVixAI is distributed across Render (Backend, Chatbot, Frontend) and Supabase (PostgreSQL). We leverage cloud-native features to ensure high availability and minimize downtime.

## 2. Recovery Time Objective (RTO) & Recovery Point Objective (RPO)
- **RTO:** 15 minutes for complete service restoration via Render auto-deployments.
- **RPO:** 24 hours (based on Supabase free tier daily backups) or 0 hours for critical offline synchronized data, as the frontend PWA buffers SOS and road reports via IndexedDB.

## 3. Disaster Scenarios & Mitigation

### 3.1. Supabase Database Failure
- **Symptom:** API endpoints return `500 Internal Server Error` with `psycopg2.OperationalError` or connection pooling exhaustion.
- **Action:** 
  1. Login to Supabase dashboard and check Database health.
  2. If the instance is paused (free tier inactivity), manually restart it.
  3. If corrupted, restore from the latest automatic daily backup in the Supabase Dashboard -> Database -> Backups.
  4. Ensure backend services auto-reconnect via `pool_pre_ping=True` in SQLAlchemy.

### 3.2. Render Service Outage
- **Symptom:** Frontend or API is unreachable, `502 Bad Gateway`.
- **Action:**
  1. Render will automatically attempt to restart crashed containers.
  2. For regional outages, trigger a manual deploy from the Render dashboard (which grabs the latest Docker image or build).
  3. If Render itself is completely down, SafeVixAI's Frontend PWA automatically switches to Offline Mode, continuing to collect telemetry and SOS alerts into the Background Sync Queue.

### 3.3. External API Rate Limits (Overpass/Groq)
- **Symptom:** Missing map POIs, Chatbot unresponsive, `429 Too Many Requests`.
- **Action:**
  1. Geocoding / Map Data: The backend has exponential backoff and uses `photon.komoot.io` or our internal `seed_db` cache as fallbacks for Overpass.
  2. Chatbot: Switch to a fallback LLM provider in `chatbot_service/.env` (e.g., from `GROQ_API_KEY` to `GEMINI_API_KEY`) and restart the service.

## 4. Emergency Escalation
In case of a severe unrecoverable outage during the demo:
1. Hard-reload the PWA (`Ctrl+F5`) to ensure no stale cached logic.
2. Use the local offline India-Emergency GeoJSON bundle to demonstrate map capabilities without backend connectivity.
3. Show the `offline-sos-queue` functionality.
