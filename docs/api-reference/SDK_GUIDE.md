# SDK Guide — API Integration

> Version 1.0 | 2026-07-29

## API Call Flow

```mermaid
sequenceDiagram
    participant Client as Client App
    participant Auth as Auth Gateway
    participant API as "API Gateway :8000"
    participant Chatbot as "Chatbot :8010"
    participant DB as PostgreSQL
    participant Cache as Redis

    Note over Client,Cache: REST API Flow

    Client->>Auth: POST /api/v1/auth/login
    Auth->>DB: Verify credentials
    DB-->>Auth: User + role
    Auth-->>Client: JWT Access Token + Refresh Token

    Client->>API: GET /api/v1/emergency/nearby?lat=13.08&lon=80.27
    Note right of Client: Authorization: Bearer <JWT>
    API->>Cache: Check cache (1h TTL)
    alt Cache Hit
        Cache-->>API: Cached response
    else Cache Miss
        API->>DB: PostGIS ST_DWithin query
        DB-->>API: Nearby services
        API->>Cache: SETEX (3600s)
    end
    API-->>Client: 200 { status, data, meta }

    Client->>API: POST /api/v1/challan/calculate
    Note right of Client: { violation_code, state, vehicle_class }
    API->>API: DuckDB SQL calculation
    API-->>Client: 200 { fine_amount, sections, sources }

    Client->>Chatbot: POST /api/v1/chat/
    Note right of Client: { message, provider_hint, user_id }
    Chatbot->>Chatbot: Safety to Intent to RAG to LLM
    Chatbot-->>Client: 200 { response, sources, intent }

    Client->>API: POST /api/v1/roads/report
    Note right of Client: Multipart: image + location + description
    API->>DB: INSERT road_issue
    API-->>Client: 201 { id, status: "submitted" }

    Client->>API: GET /api/v1/officer/dispatches
    Note right of Client: Authorization: Bearer <Officer JWT>
    API->>DB: Query active dispatches
    DB-->>API: Dispatch list with SLA
    API-->>Client: 200 { dispatches, sla_remaining }
```

## WebSocket Tracking Lifecycle

```mermaid
sequenceDiagram
    participant Client as SOS Initiator
    participant WS as "WebSocket :8000/ws"
    participant Tracker as Family Tracking
    participant DB as PostgreSQL
    participant Cache as Redis

    Client->>WS: CONNECT /api/v1/tracking/{group_id}
    Note right of Client: Authorization: Bearer <JWT>
    WS->>WS: Validate token + group membership
    WS-->>Client: 101 Switching Protocols

    par Location Broadcast (every 5s)
        Client->>WS: { type: "location", lat, lon, speed, battery }
        WS->>Cache: Update latest position
        WS->>Tracker: Notify group members
        Tracker-->>WS: { type: "update", members: [...] }
        WS-->>Client: Relay to all group members
    and Heartbeat (every 30s)
        Client->>WS: { type: "ping" }
        WS-->>Client: { type: "pong" }
    and Emergency Alert
        Client->>WS: { type: "emergency", sos: true }
        WS->>DB: Log SOS event
        WS->>Tracker: Emergency broadcast
        Tracker-->>WS: { type: "emergency_ack", dispatch_id }
        WS-->>Client: Confirmation
    end

    Client->>WS: DISCONNECT
    WS->>Cache: Remove group membership
    WS-->>Tracker: Member left notification
```

## Base URLs

- Development: `http://localhost:8000` (backend), `http://localhost:8010` (chatbot)
- Production: Render/Vercel URLs

## Auth

JWT Bearer token in `Authorization` header.

## Response Envelope

```json
{"success": true, "data": {...}, "error": null, "meta": {"timestamp": "...", "request_id": "..."}}
```

## Rate Limits

- General: 100/min
- Chat: 30/min
- SOS: 3/min

## Key Endpoints

- `GET /api/v1/emergency/nearby?lat=13.0827&lon=80.2707` — Nearby hospitals/police
- `POST /api/v1/challan/calculate` — Fine calculation
- `POST /api/v1/chat` — Chat (blocking)
- `POST /api/v1/chat/stream` — Chat (SSE streaming)
- `POST /api/v1/roads/report` — Submit road issue
- `POST /api/v1/emergency/sos` — Trigger SOS

## WebSocket

`ws://host/api/v1/tracking/{group_id}` — Live family tracking
