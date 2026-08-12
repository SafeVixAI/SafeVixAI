# Privacy Policy

> Version 1.0 | 2026-07-29

## Data Flow & Compliance Diagram

```mermaid
flowchart TD
    subgraph Device[" Device — Private Zone "]
        IDB["IndexedDB<br/>Blood Group<br/>Emergency Contacts<br/>Medical Info<br/>Vehicle Number"]

        LOC["In-Memory Location<br/>GPS Coordinates<br/>Session Only, Not Persisted"]

        SW["Service Worker<br/>Static Assets Cache<br/>Offline Pages"]

        DUCK["DuckDB-Wasm<br/>Offline Challan Data<br/>Public Violation Codes"]

        WEBLLM["WebLLM Phi-3<br/>2.2GB Model<br/>Local Inference Only"]
    end

    subgraph Network[" Network — Transient Zone "]
        JWT["JWT Auth Token<br/>Bearer in Headers"]
        API["API Request/Response<br/>HTTPS Encrypted"]
        WS["WebSocket Tracking<br/>Encrypted Stream"]
    end

    subgraph Server[" Server — Processing Zone "]
        subgraph PG[" PostgreSQL — GDPR/DPDP Compliant "]
            PG1["User Profile<br/>Name, Email, Role"]
            PG2["Service Requests<br/>SOS, Reports, Dispatches"]
            PG3["Audit Logs<br/>Non-repudiation"]
        end

        subgraph Redis[" Redis — Ephemeral "]
            R1["Chat History<br/>24h TTL ✓ Auto-forget"]
            R2["Rate Limiter State<br/>Session-bound"]
        end

        subgraph Analytics[" Analytics — Opt-in "]
            PH["PostHog<br/>Usage Stats, Error Tracking"]
            PH -->|"Opt-in Required"| USER{"User Consent"}
            USER -->|No| PH_BLOCK[No Data Collected]
            USER -->|Yes| PH_SEND[Anonymized Events]
        end
    end

    Device -->|Necessary| Network
    Network -->|"Encrypted TLS 1.3"| Server

    IDB -.->|NEVER uploaded| IDB
    LOC -.->|Transient only| LOC

    PG -.->|Compliant| GDPR["GDPR<br/>Right to Erasure"]
    PG -.->|Compliant| DPDP["DPDP<br/>Data Principal Rights"]


    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b
    classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#7c2d12
    classDef neutral fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b

    class Device neutral
    class IDB data
    class LOC neutral
    class SW data
    class DUCK data
    class WEBLLM ai
    class Network neutral
    class JWT security
    class API edge
    class WS neutral
    class Server control
    class PG data
    class PG1 ai
    class PG2 control
    class PG3 neutral
    class Redis data
    class R1 neutral
    class R2 neutral
    class Analytics neutral
    class PH action
    class USER neutral
    class PH_BLOCK neutral
    class PH_SEND neutral
    class GDPR neutral
    class DPDP neutral```

## Privacy Principles

| Principle | Implementation |
|-----------|---------------|
| **Data Minimization** | Only essential data collected; blood group never leaves device |
| **Purpose Limitation** | Each data point has explicit processing purpose |
| **Storage Limitation** | 24h TTL on Redis chat history; 90-day analytics retention |
| **Consent** | PostHog analytics requires explicit opt-in |
| **Right to Erasure** | User can purge all server data via settings page |
| **Right to Portability** | Export profile data in JSON format |

## Data Collection

| Data | Storage | Purpose |
|------|---------|---------|
| Email/Phone | PostgreSQL | Account, emergency sharing |
| Location | Transient | Emergency locator |
| Blood group | IndexedDB only | Never leaves device |
| Chat history | Redis (24h TTL) | Conversation continuity |
| Road reports | PostgreSQL (anonymized) | Infrastructure improvement |
| Analytics | PostHog (opt-in) | Product improvement |

## Compliance

- **GDPR**: Export (`GET /api/v1/user/export`) and delete endpoints
- **DPDP Act 2023**: Data localization, consent management
- **Security headers**: CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **Contact DPO**: `dpo@safevixai.gov.in`
