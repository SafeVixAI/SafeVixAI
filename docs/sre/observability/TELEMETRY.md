# Telemetry & Analytics

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [PRIVACY.md](../../compliance-and-reports/PRIVACY.md), [Security.md](../../architecture/Security.md)

---

## What Data Is Collected

### Frontend Analytics (PostHog)
With user consent:
- Page views and navigation
- Feature usage (SOS activation, challan calculation, reporting)
- Error events (console errors, API failures)
- Browser and device information (OS, screen size, language)
- Performance metrics (page load, API latency)

### Server Logs (Structured JSON)
- Request method, path, status code, duration
- Error messages and stack traces (no user data)
- LLM provider call count and latency
- Database query performance

---

## What Data Is NOT Collected

- **No personal information** (name, email, phone) in analytics events
- **No blood group or medical data** — these never leave the device
- **No location history** — only current SOS activation coordinates
- **No chat message content** — only anonymized interaction counts
- **No IP addresses stored** in analytics (anonymized)

---

## Opt-In / Opt-Out

### Framework
PostHog analytics waits for user consent before initialization:

```typescript
// frontend/lib/client-logger.ts
if (userConsented) {
  posthog.init(env.NEXT_PUBLIC_POSTHOG_KEY, {
    api_host: env.NEXT_PUBLIC_POSTHOG_HOST,
    autocapture: false,
    opt_out_capturing_by_default: true,
  });
}
```

### User Controls
- Settings page: "Share anonymous usage data" toggle
- Cookie banner on first visit
- No data sent until explicitly consented
- Revocable at any time

---

## GDPR Compliance

The telemetry system follows GDPR principles:

| Principle | Implementation |
|-----------|---------------|
| Lawfulness | Consent-based opt-in |
| Purpose limitation | Product improvement only |
| Data minimization | Minimal event properties |
| Accuracy | No personal data stored |
| Storage limitation | 90-day retention |
| Integrity/confidentiality | HTTPS transport |
| Accountability | Documented in PRIVACY.md |

---

## Self-Hosting Analytics

To disable all external telemetry:

### Option 1: Disable PostHog
```bash
# frontend/.env.local
# Leave NEXT_PUBLIC_POSTHOG_KEY unset — client-logger.ts skips init
```

### Option 2: Self-host PostHog
```yaml
# docker-compose.yml
services:
  posthog:
    image: posthog/posthog:latest
    environment:
      - POSTHOG_SECRET=<your-secret>
```

### Option 3: Remove Analytics
Remove the `posthog-js` dependency and `hooks/analytics.py` hook.

---

## Data Retention

| Data Type | Retention | Deletion |
|-----------|-----------|----------|
| PostHog events | 90 days | Automatic |
| Server logs | 30 days | Log rotation |
| Error reports (Sentry) | 90 days | Automatic |
| User data | Until account deletion | On request |

---

## Analytics Pipeline

```
Frontend → PostHog JS SDK → PostHog Cloud (or self-hosted)
Server   → Structured Logs → File → Log rotation
Server   → /metrics        → Prometheus → Grafana
```

---

## Disabling Telemetry Entirely

Add to your deployment config:
```bash
# frontend/.env.local
NEXT_PUBLIC_DISABLE_ANALYTICS=true
```

```python
# backend/core/config.py
ENABLE_METRICS: bool = False
```

**Note:** This also disables metrics needed for monitoring. In production, metrics are strongly recommended.
