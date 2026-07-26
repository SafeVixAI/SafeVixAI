# Update Management — API Reference

> **Base URL:** `/api/v1/updates`

---

## `GET /version`

Return current version info with update availability.

**Response 200:**
```json
{
  "current_version": "1.0.0",
  "latest_version": "1.1.0",
  "update_available": true,
  "channel": "stable",
  "last_checked_at": "2026-07-26T12:00:00Z",
  "uptime_seconds": 86400.5
}
```

---

## `GET /check`

Check for available updates on a channel.

**Query Parameters:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `channel` | string | `stable` | Release channel: `stable`, `beta`, `nightly`, `pre-release` |

**Response 200:**
```json
{
  "update_available": true,
  "current_version": "1.0.0",
  "latest_version": "1.1.0",
  "latest_release": {
    "id": 1,
    "version": "1.1.0",
    "channel": "stable",
    "title": "Feature Release",
    "is_mandatory": false,
    "is_security": false,
    "published_at": "2026-07-20T12:00:00Z",
    "created_at": "2026-07-20T12:00:00Z"
  },
  "is_mandatory": false,
  "is_security": false,
  "channel": "stable",
  "last_checked_at": "2026-07-26T12:00:00Z"
}
```

---

## `GET /releases`

List releases, optionally filtered by channel.

**Query Parameters:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `channel` | string | — | Filter by channel |
| `limit` | integer | 20 | Max results (1-100) |
| `offset` | integer | 0 | Pagination offset |

---

## `GET /releases/{version}`

Get a specific release by version string.

**Response 200:** Full release detail with download URL, checksum, etc.

**Response 404:** Release not found.

---

## `GET /history`

Return paginated installation history.

**Query Parameters:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | 20 | Max results (1-100) |
| `offset` | integer | 0 | Pagination offset |

**Response 200:**
```json
{
  "installations": [
    {
      "id": 1,
      "uuid": "abc-123",
      "release_id": 1,
      "release_version": "1.1.0",
      "previous_version": "1.0.0",
      "channel": "stable",
      "status": "installed",
      "error_message": null,
      "downloaded_bytes": 1024000,
      "total_bytes": 1024000,
      "started_at": "2026-07-26T12:00:00Z",
      "completed_at": "2026-07-26T12:01:00Z",
      "created_at": "2026-07-26T12:00:00Z",
      "is_offline": false
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

## `GET /history/status/{status}`

Get installations filtered by status.

**Path Parameters:**
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | One of: `pending`, `downloading`, `downloaded`, `verifying`, `verified`, `installing`, `installed`, `failed`, `rolled_back`, `skipped` |

**Response 200:** Array of installation records.

---

## `POST /sync`

Sync releases from GitHub Releases API.

**Response 200:**
```json
{
  "success": true,
  "new_releases": 3,
  "message": "Synced 3 new releases"
}
```

**Response 502:** GitHub API request failed.

---

## `POST /download/{version}`

Start downloading a release. Records a download intent.

**Response 200:**
```json
{
  "success": true,
  "message": "Download started for version 1.1.0",
  "installation_id": 2,
  "version": "1.1.0"
}
```

**Response 404:** Release not found.

---

## `POST /install/{version}`

Install a release. Updates current version and records installation.

**Response 200:**
```json
{
  "success": true,
  "message": "Successfully installed version 1.1.0",
  "installation_id": 3,
  "version": "1.1.0"
}
```

**Response 404:** Release not found.

---

## `POST /rollback`

Rollback to a previous version.

**Query Parameters:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | string | — | Target version to rollback to; defaults to previous |

**Response 200:**
```json
{
  "success": true,
  "message": "Rolled back to version 1.0.0",
  "installation_id": 4,
  "version": "1.0.0"
}
```

**Response 200 (no history):**
```json
{
  "success": false,
  "message": "No previous version available for rollback"
}
```

---

## `GET /channels`

List available update channels with metadata.

**Response 200:**
```json
[
  {
    "channel": "stable",
    "display_name": "Stable",
    "release_count": 5,
    "latest_version": "1.1.0",
    "latest_release_title": "Feature Release"
  },
  {
    "channel": "beta",
    "display_name": "Beta",
    "release_count": 2,
    "latest_version": "1.2.0-beta.1",
    "latest_release_title": "Beta Release"
  }
]
```

---

## `GET /settings`

Return current update settings.

---

## `PUT /settings`

Update update settings.

**Request Body:**
| Field | Type | Description |
|-------|------|-------------|
| `auto_update_enabled` | boolean | Enable automatic updates |
| `channel` | string | Release channel |
| `schedule` | string | Update schedule: `immediate`, `daily`, `weekly` |
| `background_download` | boolean | Download in background |
| `auto_restart` | boolean | Auto-restart after update |
| `notify_on_update` | boolean | Show update notifications |

**Response 200:** Updated settings object.
