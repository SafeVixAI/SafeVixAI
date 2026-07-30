# SafeVixAI Operations Handbook

**Version:** 1.0
**Last Updated:** 2026-07-14

## 1. Service Overview

SafeVixAI runs three independent services communicating over REST/WebSocket with JWT Bearer authentication.

| Service | Framework | Port | Hosting |
|---------|-----------|------|---------|
| Frontend | Next.js 15 + React 19 | 3000 | Vercel |
| Backend | FastAPI | 8000 | Render.com |
| Chatbot Service | FastAPI | 8010 | Render.com |

**Dependencies:**

| Dependency | Version | Hosting | Purpose |
|------------|---------|---------|---------|
| PostgreSQL 16 + PostGIS 3.4 | 16 | Supabase | Primary data store, geospatial queries |
| Redis 7 | 7 | Upstash Serverless | Cache, rate limiting, distributed locks, conversation memory |
| ChromaDB | 0.4+ | Embedded (chatbot_service) | Vector store for RAG |
| DuckDB-Wasm | Latest | Client-side (browser) | Offline challan calculation |

## 2. SLO / SLI Targets

| SLI | Target | Measurement | Notes |
|-----|--------|-------------|-------|
| API Availability | 99.5% | Health endpoint success rate | Render free tier has no SLA |
| API Latency p95 (standard) | < 2s | Backend API response times | Excludes LLM endpoints |
| API Latency p95 (LLM) | < 5s | Chatbot /chat/stream endpoint | Includes fallback chain |
| Chatbot Response p95 | < 8s | End-to-end LLM generation | 10-provider fallback adds latency |
| Frontend TTI | < 3s | Lighthouse / Web Vitals | PWA with service worker |
| Offline Queue Delivery | > 99% | SOS/reports delivered within 5min of reconnect | IndexedDB queue |
| Database Query p99 | < 200ms | Indexed PostGIS queries | ST_DWithin with GiST index |

## 3. Error Budgets

- **Target availability:** 99.5%
- **Monthly error budget:** 0.5% of 43,200 minutes = 216 minutes (~3.6 hours)
- **Budget consumption actions:**
  - < 50%: Normal operations
  - 50-80%: Code freeze for non-critical changes
  - 80-100%: Full freeze, incident review required
  - > 100%: Emergency review, SLO renegotiation

## 4. Alerting Hierarchy

| Severity | Definition | Response Time | Notification | Examples |
|----------|-----------|---------------|-------------|---------|
| P0 | Complete service outage, data loss, security breach | < 30 min | Email alert | Both APIs down, DB corruption, PII leak |
| P1 | Major feature unavailable, partial outage | < 2 hr | Email alert | Single API down, LLM all-fail, Redis down |
| P2 | Minor feature degraded, non-critical bug | < 8 hr | Logged | Slow LLM fallback, stale cache |
| P3 | Cosmetic issue, documentation error | Next business day | Logged | Stale doc, incorrect UI text |
| P4 | Feature request, enhancement | Triage backlog | None | New provider integration |

## 5. On-Call Guide

- **Primary contact:** Email-based via `ALERT_EMAIL` env var (core/alert.py)
- **Response times:** P0 < 30min, P1 < 2hr, P2 < 8hr, P3 next business day
- **Escalation:** If no response in 15min for P0, escalate to all maintainers

## 6. Monitoring Architecture

- **Current:** No dedicated monitoring (zero-cost constraint)
- **Relies on:** Health endpoints (/health on both services), error logging via logClientError, email alerts from core/alert.py (5-min cooldown)
- **Future recommendation:** UptimeRobot free tier for external health monitoring

## 7. Capacity Planning

- **Current scale assumptions:** ~1000 DAU, ~5000 requests/day per service
- **Bottlenecks:** LLM API rate limits, free tier Render CPU limits, PostGIS query complexity
- **Scaling triggers:** >80% CPU sustained for 5min, >500 concurrent requests

## 8. Maintenance Windows

- No formal maintenance windows -- deploy during low-traffic hours (UTC 00:00-06:00)
- DB migrations require backend service restart (~30s downtime)
- ChromaDB rebuild requires chatbot restart (~10min rebuild time)
