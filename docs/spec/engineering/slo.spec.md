# SafeVixAI â€" Service Level Objectives (SLOs)

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

**Date:** 2026-05-18
**Owner:** Engineering Team
**Review cadence:** Monthly

---

## Service Level Indicators (SLIs)

| SLI | Target | Measurement | Alert Threshold |
|-----|--------|-------------|-----------------|
| **Availability** | 99.5% | Uptime monitoring (UptimeRobot) | < 99% over 1 hour |
| **p95 API Latency** | < 2s | Backend request histogram | > 3s for 5 min |
| **p95 Chatbot Latency** | < 10s | Chatbot request histogram | > 15s for 5 min |
| **Error Rate** | < 1% | 5xx / total requests | > 5% for 5 min |
| **SOS Trigger Success** | 99.9% | `/api/v1/emergency/sos` success rate | < 99% over 1 hour |
| **Offline Queue Flush** | 95% | IndexedDB queue success rate | < 80% over 24h |
| **WebSocket Connections** | < 1% drop | Active WS connections | > 10% drop in 1 min |

---

## Error Budgets

| Service | Annual Error Budget | Monthly Budget |
|---------|-------------------|----------------|
| Backend API | 43.8 minutes downtime | 3.65 minutes |
| Chatbot | 43.8 minutes downtime | 3.65 minutes |
| Frontend PWA | 43.8 minutes downtime | 3.65 minutes |

---

## Severity Definitions

| Severity | Description | Response Time | Resolution Time |
|----------|-------------|---------------|-----------------|
| **SEV1** | Complete outage, data loss, safety feature broken | 15 minutes | 1 hour |
| **SEV2** | Major feature degraded, partial outage | 30 minutes | 4 hours |
| **SEV3** | Minor feature broken, workaround available | 2 hours | 24 hours |
| **SEV4** | Cosmetic issue, documentation error | Next business day | 1 week |

### SEV1 Examples
- SOS endpoint returning errors
- Backend completely down
- Database corruption
- SafetyChecker bypassed

### SEV2 Examples
- Chatbot slow (>15s response)
- Map tiles not loading
- One LLM provider down (fallback working)
- Offline queue not flushing

### SEV3 Examples
- Challan calculator showing wrong amount
- Profile page errors
- Non-critical UI bugs

### SEV4 Examples
- Typo in documentation
- Color mismatch in UI
- Missing alt text

---

## Availability Calculation

```
Availability = (Total Time - Downtime) / Total Time Ã-- 100

Target: 99.5% over 30-day rolling window
= 216 minutes of allowed downtime per month
```

---

## Monitoring

| Tool | Purpose | Free Tier |
|------|---------|-----------|
| UptimeRobot | External health checks | 50 monitors, 5-min interval |
| Render logs | Service logs + metrics | 3-day retention |
| Sentry | Error tracking + performance | 5K errors/month |
| Custom `/health` | Readiness + liveness probes | Free |

---

## Review Process

1. **Weekly:** Check SLI dashboards, review error budget burn rate
2. **Monthly:** SLO review meeting, adjust targets if needed
3. **Quarterly:** Full reliability review, update runbooks
4. **Post-incident:** Update SLOs based on incident learnings
