# SafeVixAI API Reference

## Base URLs

| Environment | URL |
|---|---|
| Development (Backend) | `http://localhost:8000` |
| Development (Chatbot) | `http://localhost:8010` |
| Development (Frontend) | `http://localhost:3000` |
| Production (Backend) | `https://safevixai-api.onrender.com` |
| Production (Frontend) | `https://safevixai.vercel.app` |

Auto-generated Swagger docs: `{BASE_URL}/docs`

---

## Authentication

Most endpoints require **JWT Bearer tokens** (HS256). Supabase-compatible via `SUPABASE_JWT_SECRET`.

| Mechanism | Detail |
|---|---|
| JWT Access Token | Bearer token in `Authorization` header |
| Refresh Token | 30-day expiry, one-time use |
| Guest Auth | Anonymous UUID via `X-Guest-ID` header |
| Service-to-Service | `X-Internal-Api-Key` header for chatbot?backend |
| Public Endpoints | Use `get_current_user_optional` � returns `None` if unauthenticated |
| Frontend AuthGuard | Bypassed in E2E via `localStorage.__E2E_SKIP_AUTH__` |

---

## Response Format

All API responses use an envelope format:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": { "timestamp": "...", "request_id": "..." }
}
```

Error responses:

```json
{
  "success": false,
  "data": null,
  "error": { "code": "NOT_FOUND", "message": "Resource not found" },
  "meta": { "timestamp": "...", "request_id": "..." }
}
```

---

## System Endpoints

#### `GET /`

Root info.

#### `GET /health`

Returns backend health status with dependency checks (DB, Redis, chatbot).

**Response:**
```json
{
  "status": "ok",
  "chatbot_ready": true,
  "environment": "production",
  "version": "1.0.0"
}
```

#### `GET /metrics`

Prometheus metrics.

#### `POST /api/v1/csp-report`

CSP violation report collector.

---

## Authentication (`/api/v1/auth`)

#### `POST /api/v1/auth/login`

Login via email/OTP. Returns JWT access + refresh tokens.

#### `POST /api/v1/auth/signup`

Register a new user.

#### `POST /api/v1/auth/refresh`

Refresh an expired access token using a refresh token.

#### `POST /api/v1/auth/logout`

Invalidate the current session/token.

---

## Admin (`/api/v1/admin`)

Protected by `ADMIN_SECRET`. Admin-only operations.

#### `GET /api/v1/admin/health`

Full system health with per-service status.

#### `GET /api/v1/admin/stats`

System statistics (users, reports, sessions, etc.).

Various CRUD operations for system administration.

#### `GET /api/v1/admin/cache/status`

Cache status � returns `{"status": "online"}` if Redis is available, `{"status": "fallback_in_memory"}` if not.

#### `POST /api/v1/admin/cache/purge?key_prefix=...`

Purge cache entries. Optional `key_prefix` query param to filter keys (e.g., `?key_prefix=waze`). Without prefix, flushes entire cache (`flushdb`).

#### `GET /api/v1/admin/cache/status`

Cache status � returns `{"status": "online"}` if Redis is available, `{"status": "fallback_in_memory"}` if not.

#### `POST /api/v1/admin/cache/purge?key_prefix=...`

Purge cache entries. Optional `key_prefix` query param to filter keys (e.g., `?key_prefix=waze`). Without prefix, flushes entire cache (`flushdb`).

---

## Analytics (`/api/v1/analytics`)

#### `GET /api/v1/analytics/heatmap?type=...&bbox=...`

Heatmap data for a given type and bounding box.

#### `GET /api/v1/analytics/summary`

Aggregated summary statistics.

#### `GET /api/v1/analytics/ward/{ward_id}`

Ward-level analytics data.

---

## Authority (`/api/v1/authority`)

#### `GET /api/v1/authority/nearby?lat=...&lon=...`

Find nearby government authorities (police stations, municipal offices).

**Query Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `lat` | float | required | Latitude |
| `lon` | float | required | Longitude |

#### `GET /api/v1/authority/{authority_id}`

Get details for a specific authority.

---

## Challan (`/api/v1/challan`)

#### `GET /api/v1/challan/calculate?violation_code=...&state=...&vehicle_type=...`

Calculate fine for a traffic violation. DuckDB-based, deterministic (no LLM).

**Query Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `violation_code` | string | required | e.g., `MVA_185` |
| `vehicle_type` | string | `all` | `2w`, `lmv`, `commercial`, `bus` |
| `state_code` | string | None | `TN`, `KA`, `MH`, `DL`, `AP` etc. |
| `is_repeat` | bool | false | Repeat offence flag |

**Response:**
```json
{
  "violation_code": "MVA_185",
  "section": "185",
  "description_en": "Drunk driving � first offence",
  "base_fine_inr": 10000,
  "state_override_fine": null,
  "final_fine_inr": 10000,
  "repeat_fine_inr": 15000,
  "imprisonment": "6 months",
  "dl_points": 0,
  "state_code": null
}
```

#### `GET /api/v1/challan/violations`

List all violations. Filterable by `vehicle_type` or `search` (searches `description_en`).

#### `GET /api/v1/challan/state-overrides`

List all state-specific fine overrides.

#### `POST /api/v1/challan/dispute`

Draft a challan dispute (via `challan_dispute_service`).

---

## Chat (`/api/v1/chat`)

#### `POST /api/v1/chat/`

Send a message to the AI chatbot. Forwards to chatbot service at port 8010.

**Request Body:**
```json
{
  "message": "nearest hospital to my location",
  "session_id": "uuid-v4-string",
  "lat": 13.0827,
  "lon": 80.2707,
  "language": "en"
}
```

**Response:**
```json
{
  "answer": "The nearest trauma centre is Apollo Hospital, 2.3km away. Call +91-44-28291919. For emergency, dial 112 immediately.",
  "intent": "FIND_HOSPITAL",
  "sources": [
    {"document": "who_trauma_care_guidelines.pdf", "page": 45}
  ],
  "model_used": "groq-llama-3.3-70b",
  "latency_ms": 1240
}
```

#### `POST /api/v1/chat/stream`

Streaming chat response via Server-Sent Events (SSE). Tokens delivered as generated.

**Send:** `{"message": "...", "session_id": "...", "lat": 0.0, "lon": 0.0}`

**Receive:** `{"token": "The ", "done": false}` ? `{"token": "", "done": true, "intent": "LEGAL_INFO"}`

---

## Circuit Breaker (`/api/v1/circuit-breaker`)

#### `GET /api/v1/circuit-breaker/status`

View current circuit breaker states for external service calls.

#### `POST /api/v1/circuit-breaker/reset/{name}`

Manually reset a tripped circuit breaker by name.

---

## Citizen (`/api/v1/citizen`)

#### `GET /api/v1/citizen/dashboard`

Citizen dashboard data (reports, status, notifications).

#### `GET /api/v1/citizen/reports`

List the citizen's own submitted reports.

---

## Civic Intel (`/api/v1/civic-intel`)

#### `GET /api/v1/civic-intel/lgd/hierarchy`

Local Government Directory (LGD) administrative hierarchy.

#### `GET /api/v1/civic-intel/municipality/{id}`

Municipality details by ID.

#### `GET /api/v1/civic-intel/boundaries`

Administrative boundary data.

---

## Command Center (`/api/v1/command-center`)

#### `GET /api/v1/command-center/dashboard`

Command center overview (live incidents, resource status).

#### `GET /api/v1/command-center/alerts`

Active alerts and notifications.

#### `GET /api/v1/command-center/deploy`

Deploy resources to incident locations.

---

## Emergency (`/api/v1/emergency`)

#### `GET /api/v1/emergency/nearby?lat=...&lon=...&category=...&radius=...`

Find nearest emergency services. Uses radius expansion algorithm with PostGIS `ST_DWithin`.

**Query Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `lat` | float | required | Latitude |
| `lon` | float | required | Longitude |
| `radius` | int | 5000 | Search radius in meters |
| `category` | string | all | `hospital`, `police`, `ambulance`, `fire`, `towing` |
| `limit` | int | 20 | Max results |

**Response:**
```json
{
  "services": [
    {
      "name": "Apollo Hospital",
      "category": "hospital",
      "sub_category": "trauma_centre",
      "phone": "+91-44-28291919",
      "lat": 13.0621,
      "lon": 80.2812,
      "distance_meters": 2300,
      "has_trauma": true,
      "has_icu": true,
      "is_24hr": true,
      "address": "21 Greams Lane, Thousand Lights, Chennai"
    }
  ],
  "count": 15,
  "radius_used": 5000,
  "source": "database"
}
```

**Redis cache key:** `nearby:{lat:.4f}:{lon:.4f}:{radius}:{category}`  
**Cache TTL:** 3600 seconds

#### `GET /api/v1/emergency/numbers`

Returns all national emergency numbers (112, 102, 100, 1033, 108, etc.).

#### `GET /api/v1/emergency/services`

Emergency service catalog with categories and sub-categories.

#### `POST /api/v1/emergency/sos`

Trigger an SOS alert. Rate limited to 3 requests/min per IP.

#### `POST /api/v1/emergency/sos/broadcast`

Broadcast SOS alert to emergency contacts.

---

## Field Workflow (`/api/v1/field-workflow`)

#### `GET /api/v1/field-workflow/tasks`

List tasks assigned to field workers.

#### `POST /api/v1/field-workflow/checkin`

Check-in at a task location (with GPS coordinates).

#### `POST /api/v1/field-workflow/checkout`

Check-out from a task.

---

## Garage (`/api/v1/garage`)

#### `GET /api/v1/garage/vehicles`

List the current user's registered vehicles.

#### `POST /api/v1/garage/vehicles`

Register a new vehicle.

#### `GET /api/v1/garage/vehicles/{id}`

Get details for a specific vehicle.

---

## Geocoding (`/api/v1/geocode`)

#### `GET /api/v1/geocode/search?q=...&limit=...`

Forward geocoding � text address to GPS coordinates. Uses Nominatim/Photon with Redis caching.

**Query Parameters:** `q` (address string), `limit` (max results, default 5)

#### `GET /api/v1/geocode/reverse?lat=...&lon=...`

Reverse geocoding � GPS coordinates to address.

**Response:**
```json
{
  "display_name": "Tambaram, Chennai, Tamil Nadu, India",
  "city": "Chennai",
  "state": "Tamil Nadu",
  "state_code": "TN",
  "country_code": "IN",
  "postcode": "600045"
}
```

---

## Live Tracking (`/api/v1/tracking`)

#### `WebSocket /api/v1/tracking/{group_id}`

Real-time location sharing via WebSocket. Connect, send location updates, receive positions of other group members.

#### `POST /api/v1/tracking/start`

Start a new tracking session.

#### `POST /api/v1/tracking/stop`

Stop the current tracking session.

---

## MCP Server (`/mcp`)

Enabled via `MCP_ENABLED=true` setting.

#### `GET /mcp/sse`

MCP Server-Sent Events endpoint for external agent integration.

#### `POST /mcp/messages`

MCP message endpoint for tool calls.

#### `GET /health`

MCP server health check � returns `{"status": "healthy", "mcp_server": "online"}`.

---

## Officers (`/api/v1/officers`)

#### `GET /api/v1/officers`

List traffic officers.

#### `GET /api/v1/officers/{id}`

Officer details and assignment info.

#### `POST /api/v1/officers/checkin`

Officer check-in at duty location. Uses route optimizer for patrol planning.

---

## Offline (`/api/v1/offline`)

#### `GET /api/v1/offline/bundle`

Download offline data bundle (GeoJSON of emergency services for offline pre-loading in PWA).

#### `GET /api/v1/offline/sync`

Sync queued offline actions submitted while disconnected.

---

## Public (`/api/v1/public`)

Unauthenticated public endpoints.

#### `GET /api/v1/public/emergency-numbers`

Public emergency phone numbers (no auth required).

#### `GET /api/v1/public/health`

Public health check endpoint.

---

## RoadWatch (`/api/v1/roads`)

#### `GET /api/v1/roads/issues?bbox=...&status=...`

Get community-reported road issues. Filterable by bounding box and status.

**Query Parameters:** `bbox` (comma-separated coordinates), `status` (`open`, `acknowledged`, `resolved`)

#### `POST /api/v1/roads/report`

Submit a new road issue report. Supports anonymous submissions via `get_current_user_optional`.

**Request:** Multipart form data
| Field | Type | Required | Description |
|---|---|---|---|
| `issue_type` | string | Yes | `pothole`, `flood`, `broken`, `missing_signage`, `no_lighting`, `accident_prone` |
| `severity` | int (1-5) | Yes | 1=minor, 5=impassable |
| `lat` | float | Yes | GPS latitude |
| `lon` | float | Yes | GPS longitude |
| `description` | string | No | Optional description |
| `photo` | file | No | Photo of road issue |

**Response:**
```json
{
  "uuid": "rs-2026-03-tn-00847",
  "authority_name": "NHAI",
  "authority_phone": "1033",
  "complaint_portal": "https://nhai.gov.in/complaint",
  "road_type": "National Highway",
  "road_number": "NH-44",
  "exec_engineer": "Mr. Rajesh Kumar",
  "exec_engineer_phone": "+91-44-28263851"
}
```

#### `GET /api/v1/roads/report/{id}`

Get details for a specific road issue report.

#### `GET /api/v1/roads/feed`

Feed of recent road issue reports.

#### `GET /api/v1/roads/infrastructure?lat=...&lon=...`

Road infrastructure data (contractor, budget, engineer) at given coordinates.

---

## Routing (`/api/v1/routing`)

#### `GET /api/v1/routing/directions?start=...&end=...&profile=...`

Get route directions between two points. Uses OpenRouteService.

**Query Parameters:** `start` (`lat,lon`), `end` (`lat,lon`), `profile` (`driving`, `walking`, `cycling`)

#### `GET /api/v1/routing/safe-route?start=...&end=...`

Crime-aware safe routing that avoids accident blackspots and high-crime areas.

#### `GET /api/v1/routing/nearby-spaces?lat=...&lon=...&type=...`

Find nearby safe spaces (well-lit areas, police presence, etc.).

---

## Tracking (`/api/v1/tracking`)

#### `GET /api/v1/tracking/session/{session_id}`

Get tracking session metadata and position history.

#### `POST /api/v1/tracking/location`

Update the current GPS position in an active tracking session.

---

## User (`/api/v1/user`)

#### `GET /api/v1/user/profile`

Get the authenticated user's profile.

#### `PUT /api/v1/user/profile`

Update user profile fields.

#### `DELETE /api/v1/user/profile`

Delete user account and associated data (GDPR compliance).

#### `GET /api/v1/user/export`

Export all user data as JSON.

#### `GET /api/v1/user/emergency-contacts`

List the user's emergency contacts.

#### `POST /api/v1/user/emergency-contacts`

Add a new emergency contact.

---

## Wards (`/api/v1/wards`)

#### `GET /api/v1/wards`

List all municipal wards.

#### `GET /api/v1/wards/{id}`

Get ward details.

#### `GET /api/v1/wards/{id}/stats`

Ward-level statistics (report counts, resolved rates, etc.).

---

## Waze Feed (`/api/v1/waze`)

> **Note:** The Waze feed endpoint uses a TokenBucket rate limiter. When rate-limited (2 requests per IP), returns `{"note": "Rate limit exceeded. Token bucket depleted."}`.

#### `GET /api/v1/waze/feed?bbox=...`

CIFS-compliant community hazard feed for Waze integration.

#### `GET /api/v1/waze/alerts`

Waze alert data.

---

## Speech Endpoints (Chatbot Service � port 8010)

#### `POST /speech/translate`

Indian language ASR/TTS pipeline. Uses IndicSeamlessService.

**Request:** Audio file or text with source/target language codes.

#### `GET /speech/status`

Speech service health and available language pairs.

---

## Chatbot Service (port 8010)

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Chatbot health check |
| `/` | GET | Root info |
| `/metrics` | GET | Prometheus metrics |
| `/api/v1/chat/` | POST | Chat message (same as backend proxy) |
| `/api/v1/chat/stream` | POST | Streaming chat (SSE) |
| `/speech/translate` | POST | Speech translation |
| `/speech/status` | GET | Speech service status |

---

## Rate Limits

### Server-Side (slowapi � IP-based)

| Endpoint | Limit |
|---|---|
| General API | 100 requests/min per IP |
| Auth endpoints | 5 attempts/min per IP |
| `POST /api/v1/emergency/sos` | 3 requests/min per IP |
| `GET /api/v1/challan/calculate` | 60 requests/min per IP |
| `POST /api/v1/chat/` | 30 requests/min per IP |
| `POST /api/v1/chat/stream` | 30 requests/min per IP |
| `GET /api/v1/geocode/*` | 30 requests/min per IP |

### External Service Constraints

| Service | Limit | Our Handling |
|---|---|---|
| Main LLM APIs | Varies per provider | 10-provider fallback chain + offline AI |
| Nominatim geocoder | 1 req/sec | Redis cache (86400s TTL) + rate limiter |
| Overpass API | Fair use ~1 req/sec | Redis cache (3600s TTL) per coordinate |
| OpenRouteService | Varies per plan | Circuit breaker + Redis cache |

---

## Error Responses

| Status | Meaning |
|---|---|
| 200 | Success |
| 400 | Bad request (invalid params) |
| 401 | Unauthorized (missing/invalid JWT) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 422 | Validation error |
| 429 | Rate limited (slowapi) |
| 500 | Internal server error |
| 503 | LLM service unavailable (all 10 providers down) |

---

*Document version: 3.4 | AI-powered road safety platform | 28 backend route modules + chatbot + MCP*

## Related

- [BENCHMARKS.md](../BENCHMARKS.md) — API performance benchmarks
- [OPERATIONS.md](../OPERATIONS.md) — Production operations and scaling
- [SDK_GUIDE.md](../SDK_GUIDE.md) — SDK usage, auth patterns, rate limits
- [ERROR_CODES.md](../ERROR_CODES.md) — Complete error code reference
