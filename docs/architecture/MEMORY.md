# Memory Systems

> Version 1.0 | 2026-07-29

## Complete Storage Architecture

```mermaid
flowchart TD
    subgraph Browser["Browser — Client Side"]
        subgraph IDB_Profile["IndexedDB — User Profile"]
            IDB1[Blood Group]
            IDB2[Emergency Contacts]
            IDB3[Vehicle Number]
            IDB4[Display ID]
            IDB5[Medical Info<br/>Allergies, Insurance]
        end

        subgraph IDB_Queue["IndexedDB — Offline Queues"]
            Q1[SOS Queue<br/>Pending Emergency Alerts]
            Q2[Road Report Queue<br/>Pending Issue Reports]
        end

        subgraph Zustand["Zustand — Frontend State"]
            Z1[auth Slice<br/>User, JWT, Session]
            Z2[map Slice<br/>Center, Zoom, Layers]
            Z3[settings Slice<br/>Theme, Language, Toggles]
            Z4[ui Slice<br/>Modals, Panels, Sidebar]
            Z5[data Slice<br/>Services, Issues, Cache]
            Z6[providers Slice<br/>LLM Provider Config]
        end

        subgraph Cache["Browser Cache"]
            C1[Service Worker Cache<br/>Static Assets, API Responses]
            C2[DuckDB-Wasm<br/>Offline Challan Data]
            C3[WebLLM Model Cache<br/>Phi-3 Mini 2.2GB]
        end
    end

    subgraph Server["Server Side"]
        subgraph Redis["Redis — Cache & Session"]
            R1[Chat History<br/>24h TTL]
            R2[Rate Limiter<br/>Token Bucket State]
            R3[Distributed Lock<br/>Redlock Pattern]
            R4[JWKS Cache<br/>1h TTL]
            R5[Idempotency Keys<br/>24h TTL]
            R6[Domain Events<br/>Event Bus Buffer]
        end

        subgraph PG["PostgreSQL — Persistent"]
            P1[Users & Profiles<br/>Auth, Roles]
            P2[Municipalities<br/>Wards, Boundaries]
            P3[Road Issues & Reports<br/>PostGIS Location]
            P4[Emergency Services<br/>Hospitals, Police, Fire]
            P5[Officer Dispatches<br/>SLA Tracking]
            P6[SOS Events<br/>Audit Log]
        end
    end

    Browser -->|JWT Bearer Token| Server
    IDB_Profile -.->|Never Leaves Device| Browser
    Q1 -.->|Online Event Sync| P6
    Q2 -.->|Online Event Sync| P3

    subgraph EventBus["Domain Event Bus"]
        E1[EventBus.publish]
        E2[EventBus.subscribe]
        E3[Dead Letter Queue]
    end

    Server --> EventBus
```

## Data Locality Rules

| Data | Location | TTL | Privacy |
|------|----------|-----|---------|
| Blood Group | IndexedDB only | Permanent | Never leaves device |
| Emergency Contacts | IndexedDB only | Permanent | Never leaves device |
| Chat History | Redis | 24h | Auto-deleted |
| SOS Events | PostgreSQL | Permanent | Encrypted |
| Location | In-memory | Session | Not persisted |
| Analytics | PostHog | 90 days | Opt-in only |
| JWKS | Redis | 1h | Public keys |

## Conversation Memory

Redis-backed with in-memory fallback. TTL: 24h. Session key: `chat_session:{session_id}`.

## User Profile (IndexedDB)

Blood group, emergency contacts, medical conditions — never transmitted to server.

## Frontend State (Zustand)

6 slices: auth, map, settings, ui, data, providers. Persisted via localStorage.

## Offline Queues (IndexedDB)

- SOS Queue: flushes on `online` event
- Road Report Queue: auto-submits when connected

## Redis Cache Keys

- `emergency:{lat}:{lon}:{radius}` (1h)
- `geocode:search:{query}` (24h)
- `route:{start}:{end}:{profile}` (15m)
- `circuit_breaker:{name}` (∞)

## Event Bus (Domain Events)

Events: user.sos_triggered, user.report_submitted, user.challan_calculated, llm.fallback_triggered, cache.stampede, circuit_breaker.state_change
