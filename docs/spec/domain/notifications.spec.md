# Enterprise Notification System

## Overview

The SafeVixAI notification system is a comprehensive, multi-channel enterprise notification platform supporting real-time delivery, digest mode, DND scheduling, retry logic, localization, and full audit logging.

## Architecture

```
User Action / System Event
        │
        ▼
┌───────────────────┐
│ NotificationService│
│  (services/        │
│   notification_    │
│   service.py)      │
└───────┬───────────┘
        │
        ├──► In-App (WebSocket)
        ├──► Email (SMTP)
        ├──► SMS (Provider API)
        ├──► Push (FCM/APNs)
        ├──► Slack (Webhook)
        ├──► Discord (Webhook)
        ├──► Teams (Webhook)
        └──► Webhook (Generic)
              │
              ▼
        ┌──────────┐
        │ Audit Log│
        │ (notifi- │
        │ cation_  │
        │ events)  │
        └──────────┘
```

## Database Schema

### notifications
Core table storing all notification records across channels.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | VARCHAR(255) | Target user |
| org_id | VARCHAR(36) | Tenant scope |
| channel | ENUM | in_app, email, sms, push, slack, discord, webhook, teams |
| category | ENUM | system_health, ai, security, performance, update, maintenance, incident, deployment, usage, billing, issue, sos, emergency, challan, general |
| priority | ENUM | low, normal, high, critical |
| status | ENUM | pending, sent, delivered, read, failed, cancelled |
| title | VARCHAR(512) | Notification title |
| body | TEXT | Notification body |
| metadata | JSON | Arbitrary metadata |
| source | VARCHAR(128) | Source service name |
| correlation_id | VARCHAR(128) | Correlation ID for grouping |
| read_at | TIMESTAMPTZ | When user read it |
| delivered_at | TIMESTAMPTZ | When delivered |
| scheduled_for | TIMESTAMPTZ | Future delivery |
| expires_at | TIMESTAMPTZ | Expiry |
| retry_count | INTEGER | Current retry attempt |
| max_retries | INTEGER | Max retry attempts (default 3) |
| last_error | TEXT | Last error message |

### notification_preferences
Per-user notification preferences.

| Column | Type | Description |
|--------|------|-------------|
| channels_enabled | JSON | Per-channel toggle |
| categories_enabled | JSON | Per-category toggle |
| digest_enabled | BOOLEAN | Digest mode |
| digest_frequency | VARCHAR | hourly, daily, weekly |
| dnd_enabled | BOOLEAN | Do Not Disturb |
| dnd_start_hour | INTEGER | DND start (0-23) |
| dnd_end_hour | INTEGER | DND end (0-23) |
| quiet_hours_enabled | BOOLEAN | Quiet hours |
| quiet_hours_start | VARCHAR(5) | HH:MM format |
| quiet_hours_end | VARCHAR(5) | HH:MM format |
| push_token | TEXT | FCM/APNs token |
| locale | VARCHAR(10) | Language (default: 'en') |
| ...webhook_urls | TEXT | Channel-specific URLs |

### notification_templates
Reusable notification templates with variable substitution.

### notification_digests
Tracks digest periods and aggregated notifications.

### webhook_endpoints
Registered webhook endpoints with event filtering.

### notification_events
Audit log of all notification delivery attempts.

## Channels

| Channel | Method | Configuration |
|---------|--------|---------------|
| In-App | WebSocket (real-time) | Auto-enabled via NotificationManager |
| Email | SMTP | SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD |
| SMS | Provider API | SMS_PROVIDER_URL, SMS_API_KEY |
| Push | FCM/APNs | PUSH_ENABLED, PUSH_SERVICE_URL |
| Slack | Incoming Webhook | User's slack_webhook_url or global SLACK_WEBHOOK_URL |
| Discord | Webhook | User's discord_webhook_url or global DISCORD_WEBHOOK_URL |
| Teams | MessageCard Webhook | User's teams_webhook_url |
| Webhook | Generic POST | User's webhook_url |

## API Endpoints

All endpoints under `/api/v1/notifications`:

### Notification CRUD
- `GET /notifications?user_id=xxx` — List notifications with filtering
- `GET /notifications/{id}` — Get single notification
- `POST /notifications/{id}/read` — Mark as read
- `POST /notifications/read-all` — Mark all as read
- `DELETE /notifications/{id}` — Delete notification

### Send
- `POST /notifications/send` — Send a notification (all channels supported)

### Preferences
- `GET /notifications/preferences` — Get user preferences
- `PUT /notifications/preferences` — Update preferences

### Webhooks
- `GET /notifications/webhooks` — List webhook endpoints
- `POST /notifications/webhooks` — Register webhook
- `DELETE /notifications/webhooks/{id}` — Delete webhook
- `POST /notifications/webhooks/test` — Test webhook URL

### Stats & Admin
- `GET /notifications/stats` — Notification statistics
- `GET /notifications/digests` — List notification digests
- `GET /notifications/admin/retry` — Retry failed (admin only)
- `POST /notifications/admin/process-digests` — Process digests (admin only)
- `POST /notifications/admin/cleanup` — Cleanup expired (admin only)

### WebSocket
- `WS /notifications/ws?user_id=xxx` — Real-time notification stream

## Frontend Components

### NotificationBell
Bell icon button in navigation that shows unread count badge and opens the notification center slide-over panel.

### NotificationCenter
Full notification list with:
- Category/status filters
- Real-time updates via WebSocket
- Mark read / mark all read
- Delete notifications
- Stats summary

### NotificationPreferencesPanel
User preference management:
- Channel toggles (in-app, email, SMS, push, Slack, Discord, Teams, webhook)
- Category toggles (15 categories)
- DND scheduling with hour range
- Quiet hours with HH:MM format
- Digest mode (hourly/daily/weekly)
- Contact info (email, phone)
- Locale selection

## Alert Categories

| Category | Priority | Description |
|----------|----------|-------------|
| system_health | High | Server health, DB connections, cache |
| ai | Normal | AI model updates, training status |
| security | Critical | Auth failures, suspicious activity |
| performance | Normal | Response times, resource usage |
| update | Normal | Version releases, patches |
| maintenance | Low | Scheduled downtime |
| incident | High | Active incidents, SLA breaches |
| deployment | Normal | Deploy status, rollbacks |
| usage | Normal | API usage, limits |
| billing | Normal | Invoices, payment status |
| issue | Normal | Road issues, reports |
| sos | Critical | Emergency SOS alerts |
| emergency | Critical | Emergency services |
| challan | Normal | Fine calculations |
| general | Normal | Uncategorized |

## DND & Quiet Hours Logic

- **DND**: Blocks ALL non-critical notifications during specified hours
- **Quiet Hours**: Blocks non-high/critical notifications during specified hours
- Critical notifications always bypass DND and quiet hours
- High priority notifications bypass quiet hours but NOT DND
- Queued notifications are held and delivered when DND/quiet hours end

## Retry Logic

- Failed notifications are retried up to `max_retries` (default: 3)
- `retry_failed()` processes up to 50 failed notifications per call
- Admin can trigger retry via `/admin/retry` endpoint
- Exponential backoff is NOT implemented (immediate retry) — the service layer is designed to be extended

## Digest Mode

- Low/normal priority notifications are batched when digest is enabled
- Digest frequency: hourly, daily, or weekly
- `process_digests()` runs on a schedule and sends summary notifications
- Includes per-category counts and time period

## Cleanup

- `cleanup_expired()` marks expired notifications as cancelled
- Default expiry cleanup runs on configurable interval
- Expired notifications are not deleted (kept for audit)

## Localization

- `locale` field on preferences (default: 'en')
- Templates support per-locale variants
- i18n keys in frontend components
- Supported: en, hi, ta, te, bn, mr, gu, kn, ml, pa

## Testing

```bash
# Backend tests (51 tests)
cd backend
pytest tests/test_notification_service.py -v --cov=services.notification_service

# Expected output: 51 passed, 0 failed
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SMTP_HOST | smtp.gmail.com | SMTP server |
| SMTP_PORT | 587 | SMTP port |
| SMTP_USER | — | SMTP username |
| SMTP_PASSWORD | — | SMTP password |
| PUSH_ENABLED | false | Enable push notifications |
| PUSH_SERVICE_URL | — | Push service URL |
| SMS_PROVIDER_URL | — | SMS provider URL |
| SMS_API_KEY | — | SMS API key |
| NOTIFICATION_RETRY_MAX | 3 | Max retry attempts |
| NOTIFICATION_RETRY_DELAY_SECONDS | 300 | Retry delay |
| NOTIFICATION_DIGEST_HOUR | 8 | Digest processing hour |
| NOTIFICATION_CLEANUP_DAYS | 90 | Cleanup threshold |
