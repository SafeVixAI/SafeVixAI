<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 SafeVixAI Team -->
# SafeVixAI Monitoring Setup Runbook

**Author:** DevOps Team  
**Last Updated:** 2026-07-19  

---

## 1. Prerequisites

| Service | Account | Free Tier Limit | Upgrade Cost |
|---------|---------|----------------|--------------|
| UptimeRobot | https://uptimerobot.com | 5 monitors, 5 min intervals | $5/mo for 50 |
| Grafana Cloud | https://grafana.com | 10k series, 14d retention | $29/mo for 50k |
| Sentry | https://sentry.io | 5k events/month | $29/mo for 50k |
| Axiom (optional) | https://axiom.co | 500GB/month | $49/mo for 1TB |

**Total free tier cost:** $0/mo  
**Total paid tier cost (recommended):** ~$63/mo

---

## 2. UptimeRobot Setup

### Step 1: Create Account
1. Go to https://uptimerobot.com
2. Sign up (Google or email)
3. Verify email

### Step 2: Add Monitors

Create these 5 monitors:

| Name | URL | Interval | Alert Contacts |
|------|-----|----------|----------------|
| Backend Health | `https://api.safevixai.com/health` | 5 min | Email + Slack |
| Chatbot Health | `https://chatbot.safevixai.com/health` | 5 min | Email + Slack |
| Frontend | `https://app.safevixai.com` | 5 min | Email + Slack |
| SOS Endpoint | `https://api.safevixai.com/api/v1/emergency/nearby?lat=13.08&lon=80.27` | 5 min | Email + Slack |
| SSL Certificate | `https://app.safevixai.com` | 60 min | Email + Slack |

### Step 3: Configure Alert Contacts
- Email to on-call engineer
- Slack webhook to #alerts channel
- (Optional) SMS to on-call phone

### Step 4: Status Page (Optional)
Create a public status page at https://stats.uptimerobot.com:
- List all 5 monitors
- Set to "Public" for transparency
- Custom domain: `status.safevixai.com`

---

## 3. Grafana Cloud Setup

### Step 1: Create Account
1. Go to https://grafana.com
2. Sign up → "Start free"
3. Select Grafana + Prometheus + Loki

### Step 2: Configure Data Sources

**Prometheus (metrics):**
```
URL:  https://prometheus-prod-10-prod-eu-west-0.grafana.net/api/prom
User: <instance-id>
Pass: <grafana-cloud-api-token>
```

**Loki (logs):**
```
URL:  https://logs-prod-eu-west-0.grafana.net/loki/api/v1
User: <instance-id>
Pass: <grafana-cloud-api-token>
```

### Step 3: Import Dashboard
1. In Grafana, go to "+" → Import
2. Upload `deploy/grafana-dashboard.json`
3. Select Prometheus data source
4. Click Import

### Step 4: Configure Alerts
1. Go to Alerting → Contact points
2. Add Email contact for on-call
3. Add Slack webhook contact
4. Create notification policy → route critical alerts to Slack + Email

---

## 4. Sentry Setup

### Step 1: Create Project
1. Go to https://sentry.io
2. Create new project → Python (FastAPI) for backend
3. Copy DSN

### Step 2: Configure Error Tracking
```bash
# Add to backend/.env
SENTRY_DSN=https://xyz@sentry.io/123

# Already implemented in backend/main.py:
# try: import sentry_sdk ...
```

### Step 3: Set Performance Monitoring
```python
# In backend/main.py (already configured):
import sentry_sdk
sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=0.05,      # 5% sampling for performance
    profiles_sample_rate=0.05,    # 5% profiling
    environment=ENVIRONMENT,
)
```

### Step 4: Configure Alerts
1. Go to Alerts → Create Alert Rule
2. Set: "When 10+ errors in 5 minutes"
3. Action: Send to Slack + Email
4. Set: "When no events received for 1 hour" (dead man's switch)

---

## 5. Self-Hosted Deployment (with deploy/ Configs)

For self-hosted setups, deploy these config files alongside the OTEL collector:

| Config File | Purpose |
|-------------|---------|
| `deploy/otel-collector-config.yaml` | OTEL pipeline (traces → Grafana, logs → Axiom) |
| `deploy/prometheus-rules.yaml` | Alert rules (error rate, latency, circuit breaker) |
| `deploy/logging-config.yaml` | Structured logging config (JSON format, log levels) |
| `deploy/grafana-dashboard.json` | Pre-built dashboard for Grafana Cloud |

### Verify Traces are Flowing
```bash
# From the OTEL collector:
curl http://localhost:8889/metrics | grep safevixai
# Should show counter metrics incrementing

# Check collector health:
curl http://localhost:13133  # Should return {"healthy": true}
```

### Verify Span Export
```bash
# Make a request to the backend
curl http://localhost:8000/api/v1/emergency/nearby?lat=13.08&lon=80.27

# Check collector logs for spans
docker logs safevixai-otel-collector --tail 20
```

---

## 6. Cost Management

| Tier | Monthly Cost | When to Upgrade |
|------|-------------|-----------------|
| UptimeRobot Free | $0 | >5 endpoints needed |
| Grafana Cloud Free | $0 | >10k metric series |
| Sentry Free | $0 | >5k events/month |
| Grafana Cloud Paid | $29 | >14d retention needed |
| Sentry Paid | $29 | >50k events/month |

---

## 7. Alert Thresholds (Recommended)

| Alert | Threshold | Severity | Escalate After |
|-------|-----------|----------|----------------|
| Health check down | 1 failure | CRITICAL | 5 min |
| Error rate >5% | 5 min window | CRITICAL | 15 min |
| p99 latency >2s | 5 min window | WARNING | 30 min |
| Circuit breaker open | 1 min | CRITICAL | 10 min |
| DB pool >80% | 5 min window | CRITICAL | 15 min |
| SOS endpoint failing | 3 failures in 5min | CRITICAL | 5 min |
| Certificate expiry | <30 days | WARNING | weekly |

---

## 8. On-Call Rotation

### Schedule
- **Primary:** One engineer per week (Mon → Mon)
- **Secondary:** Backup engineer for escalations
- **Schedule tool:** PagerDuty (free tier: 1 user) or Opsgenie

### Handoff Checklist
- [ ] Review unresolved alerts
- [ ] Check incident log
- [ ] Verify all monitors green
- [ ] Update on-call in README
- [ ] Brief incoming on-call on ongoing issues
