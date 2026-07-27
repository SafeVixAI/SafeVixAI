# Monitoring Setup

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [Observability](./observability/), [ADVANCED_SETUP.md](./ADVANCED_SETUP.md)

---

## Architecture

```
Your App
  ├── /metrics (Prometheus endpoint)
  ├── Structured JSON logs → File/Loki
  └── Sentry SDK (frontend errors)

Prometheus → Grafana
Loki       → Grafana (logs)
Alertmanager → Email/Slack/PagerDuty
```

---

## Prometheus Metrics

### Backend Metrics
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | Counter | method, path, status | Total HTTP requests |
| `http_request_duration_ms` | Histogram | method, path | Request latency |
| `db_query_duration_ms` | Histogram | query_name | Database query latency |
| `redis_operations_total` | Counter | operation | Redis operation count |
| `llm_provider_calls_total` | Counter | provider, status | LLM provider call count |

### Endpoint
```python
# backend/main.py
from prometheus_fastapi_instrumentator import Instrumentator

@app.on_event("startup")
async def setup_metrics():
    Instrumentator().instrument(app).expose(app)
```

**Metrics endpoint:** `GET /metrics`

---

## Grafana Dashboards

### Provisioned Dashboards

| Dashboard | Panels | Refresh |
|-----------|--------|---------|
| **Backend Overview** | Request rate, latency (p50/p95/p99), error rate, active connections | 15s |
| **Resource Usage** | CPU, memory, disk, network per service | 30s |
| **Database** | Connection count, query latency, cache hit ratio, replication lag | 30s |
| **LLM Providers** | Call rate, error rate, latency per provider, fallback events | 60s |
| **Redis** | Memory usage, hit rate, command rate, connected clients | 30s |
| **Saturation** | CPU throttling, OOM events, disk I/O wait | 60s |

### Dashboard Location
Grafana dashboards are defined in `monitoring/grafana/dashboards/` and auto-provisioned.

---

## Loki Log Aggregation

### Log Format
All services emit structured JSON logs:
```json
{
  "timestamp": "2026-07-26T10:00:00Z",
  "level": "INFO",
  "service": "backend",
  "request_id": "req_abc123",
  "method": "GET",
  "path": "/api/v1/emergency/nearby",
  "duration_ms": 45,
  "status_code": 200,
  "message": "Request completed"
}
```

### Log Levels
| Level | When to Use |
|-------|-------------|
| DEBUG | Development only, disabled in production |
| INFO | Normal operation, request lifecycle |
| WARNING | Unexpected but handled (rate limit, fallback) |
| ERROR | Operation failure (DB error, provider failure) |
| CRITICAL | Service cannot function (all providers down) |

---

## Alertmanager Rules

### Critical Alerts
```yaml
# monitoring/prometheus/alerts.yml
groups:
  - name: critical
    rules:
      - alert: BackendDown
        expr: up{job="backend"} == 0
        for: 1m
        annotations:
          summary: "Backend service is down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Error rate > 5% over 5 minutes"

      - alert: AllLLMProvidersDown
        expr: llm_provider_calls_total{status="success"} == 0
        for: 2m
        annotations:
          summary: "All LLM providers are failing"
```

### Warning Alerts
```yaml
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 50
        for: 5m

      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.8
        for: 5m
```

---

## Notification Channels

| Channel | Critical | Warning | Info |
|---------|----------|---------|------|
| Email | ✅ | ✅ | ❌ |
| Slack | ✅ | ✅ | ✅ |
| PagerDuty | ✅ | ❌ | ❌ |

Configure in `monitoring/alertmanager.yml`.

---

## Health Check Endpoints

| Endpoint | Service | Returns |
|----------|---------|---------|
| `GET /health` | Backend | `{"status": "ok", "version": "...", "db": "connected", "redis": "connected"}` |
| `GET /ready` | Backend | `{"status": "ok"}` (readiness probe) |
| `GET /health` | Chatbot | `{"status": "ok", "providers": 9}` |

---

## SLI / SLO Definitions

| SLI | Target | Measurement |
|-----|--------|-------------|
| API availability | 99.9% | Successful requests / total requests |
| API latency (p95) | < 500ms | HTTP request duration |
| API latency (p99) | < 2s | HTTP request duration |
| LLM response time | < 10s | Time to first token |
| Uptime | 99.9% | Health check pass rate |
| Error rate | < 0.1% | 5xx / total requests |

### Error Budget
Monthly error budget = (1 - SLO) × total requests. At current SLO of 99.9%:
- 100K requests/month → 100 errors allowed
- If budget exhausted: freeze feature releases, focus on reliability

---

## Synthetic Monitoring

Use [Checkly](https://checklyhq.com) or GitHub Actions scheduled workflows:

```yaml
# .github/workflows/synthetic-monitoring.yml
on:
  schedule:
    - cron: '*/5 * * * *'
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - run: curl --fail http://api.safevixai.gov.in/health
      - run: curl --fail http://safevixai.vercel.app
```

---

## Runbook Integration

When alerts fire, the dashboard should link directly to the relevant runbook:
- Backend down → [runbooks/service-restart.md](./runbooks/service-restart.md)
- All LLMs down → [runbooks/all-llms-down.md](./runbooks/all-llms-down.md)
- Database down → [runbooks/db-down.md](./runbooks/db-down.md)
- High error rate → [runbooks/high-error-rate.md](./runbooks/high-error-rate.md)

## Related

- [MONITORING.md](../MONITORING.md) — Monitoring overview and dashboards
- [OBSERVABILITY.md](../OBSERVABILITY.md) — Observability architecture
- [OPERATIONS.md](../OPERATIONS.md) — Operations and incident response
- [TELEMETRY.md](TELEMETRY.md) — Telemetry configuration and data collection
