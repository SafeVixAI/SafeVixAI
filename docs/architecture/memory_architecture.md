# Memory Systems

> Version 1.0 | 2026-07-29

## Complete Storage Architecture

```mermaid
flowchart TD
    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b

    subgraph Browser["Browser — Client Side"]
        subgraph IDB_Profile["IndexedDB — User Profile"]
            IDB1["Blood Group"]:::data
            IDB2["Emergency Contacts"]:::data
            IDB3["Vehicle Number"]:::data
            IDB4["Display ID"]:::data
            IDB5["Medical Info<br/>Allergies, Insurance"]:::data
        end

        subgraph IDB_Queue["IndexedDB — Offline Queues"]
            Q1["SOS Queue<br/>Pending Emergency Alerts"]:::data
            Q2["Road Report Queue<br/>Pending Issue Reports"]:::data
        end

        subgraph Zustand["Zustand — Frontend State"]
            Z1["auth Slice<br/>User, JWT, Session"]:::edge
            Z2["map Slice<br/>Center, Zoom, Layers"]:::edge
            Z3["settings Slice<br/>Theme, Language, Toggles"]:::edge
            Z4["ui Slice<br/>Modals, Panels, Sidebar"]:::edge
            Z5["data Slice<br/>Services, Issues, Cache"]:::edge
            Z6["providers Slice<br/>LLM Provider Config"]:::edge
        end

        subgraph Cache["Browser Cache"]
            C1["Service Worker Cache<br/>Static Assets, API Responses"]:::data
            C2["DuckDB-Wasm<br/>Offline Challan Data"]:::data
            C3["WebLLM Model Cache<br/>Phi-3 Mini 2.2GB"]:::ai
        end
    end

    subgraph Server["Server Side"]
        subgraph Redis["Redis — Cache & Session"]
            R1["Chat History<br/>24h TTL"]:::data
            R2["Rate Limiter<br/>Token Bucket State"]:::security
            R3["Distributed Lock<br/>Redlock Pattern"]:::control
            R4["JWKS Cache<br/>1h TTL"]:::security
            R5["Idempotency Keys<br/>24h TTL"]:::control
            R6["Domain Events<br/>Event Bus Buffer"]:::control
        end

        subgraph PG["PostgreSQL — Persistent"]
            P1["Users & Profiles<br/>Auth, Roles"]:::data
            P2["Municipalities<br/>Wards, Boundaries"]:::data
            P3["Road Issues & Reports<br/>PostGIS Location"]:::data
            P4["Emergency Services<br/>Hospitals, Police, Fire"]:::data
            P5["Officer Dispatches<br/>SLA Tracking"]:::data
            P6["SOS Events<br/>Audit Log"]:::data
        end
    end

    Browser -->|"JWT Bearer Token"| Server
    IDB_Profile -.->|"Never Leaves Device"| Browser
    Q1 -.->|"Online Event Sync"| P6
    Q2 -.->|"Online Event Sync"| P3

    subgraph EventBus["Domain Event Bus"]
        E1["EventBus.publish"]:::control
        E2["EventBus.subscribe"]:::control
        E3["Dead Letter Queue"]:::data
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
