# Monitoring

> **Metrics collection, dashboard setup, uptime monitoring, and performance tracking.**

SafeVixAI uses Prometheus for metric collection and Grafana for visualization - both provisioned as code.

## Monitoring Stack

```mermaid
flowchart TD
    subgraph Services["Instrumented Services"]
        BE[Backend :8000<br/>/metrics endpoint]
        CB[Chatbot :8010<br/>/metrics endpoint]
        FE[Frontend :3000<br/>Web Vitals]
    end

    subgraph Collection["Metrics Collection"]
        PROM[Prometheus<br/>Pull-based scraping]
        PROM_CONFIG[prometheus-config.yml<br/>Scrape configs]
    end

    subgraph Visualization["Visualization & Alerting"]
        GRAF[Grafana<br/>Provisioned dashboards]
        ALERT[Alert Rules<br/>prometheus-rules.yml]
        EMAIL[Email Alerts<br/>SMTP with 5-min cooldown]
    end

    subgraph Logs["Logging"]
        STRUCT[Structured JSON Logs<br/>NDJSON stdout]
        SENTRY[Sentry Error Tracking<br/>0.05 sample rate]
    end

    BE --> PROM
    CB --> PROM
    FE -->|RUM| SENTRY

    PROM --> GRAF
    PROM --> ALERT
    ALERT --> EMAIL

    BE --> STRUCT
    CB --> STRUCT
    FE --> SENTRY
```

## Alert Lifecycle

```mermaid
stateDiagram-v2
    [*] --> OK: All thresholds normal

    OK --> Pending: Metric exceeds threshold<br/>(within 1m window)
    Pending --> Firing: Threshold exceeded for 5m

    Firing --> Alerting: Send notification
    Alerting --> Acknowledged: Operator acknowledges

    Acknowledged --> Investigating: Operator investigates
    Investigating --> Resolved: Root cause fixed
    Resolved --> OK: Metrics return to normal

    Firing --> OK: Metric recovers<br/>(auto-resolve)
    Alerting --> OK: False alarm

    note right of Firing
        Triggers: email alert
        Channels: SMTP
        Cooldown: 5 minutes
    end note
```

---

## Quick Links

| Area | Documentation |
|------|---------------|
| Setup Guide | [`docs/MONITORING_SETUP.md`](docs/MONITORING_SETUP.md) |
| Grafana Dashboard | [`docs/observability/grafana-dashboard.json`](docs/observability/grafana-dashboard.json) |
| Prometheus Config | [`docs/observability/prometheus-config.yml`](docs/observability/prometheus-config.yml) |
| Alert Rules | [`docs/observability/alerts/`](docs/observability/alerts/) |
| Telemetry Guide | [`docs/TELEMETRY.md`](docs/TELEMETRY.md) |
| Performance Benchmarks | [`docs/PERFORMANCE_BENCHMARKS.md`](docs/PERFORMANCE_BENCHMARKS.md) |
| Observability Overview | [`OBSERVABILITY.md`](OBSERVABILITY.md) |

---

## Metrics Dashboard

The Grafana dashboard covers four golden signals for every service:

| Signal | Metric | Target |
|--------|--------|--------|
| Latency | `http_request_duration_seconds` | P95 < 500ms (backend), P95 < 5s (chatbot) |
| Traffic | `http_requests_total` | Per-endpoint rate |
| Errors | `http_requests_total{status=~"5.."}` | < 1% of total |
| Saturation | `memory_usage_bytes`, `db_connection_pool_size` | < 80% utilization |

---

## Alert Thresholds

| Alert | Threshold | Action |
|-------|-----------|--------|
| High Error Rate | > 5% 5xx in 5 min | Check runbook |
| High Latency | P95 > 2s (backend) | Scale up / optimize query |
| Circuit Breaker Open | Any breaker open for > 1 min | Investigate provider |
| DB Connection Pool | > 80% utilized | Increase pool / optimize |
| Memory | > 85% RSS | Restart / scale |

---

## Related

- [`OBSERVABILITY.md`](OBSERVABILITY.md) — logging, metrics, alerting
- [`OPERATIONS.md`](OPERATIONS.md) — deployment, scaling
- [`RUNBOOKS.md`](RUNBOOKS.md) — incident response
