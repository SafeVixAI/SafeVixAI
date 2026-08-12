# Monitoring

> **Metrics collection, dashboard setup, uptime monitoring, and performance tracking.**

SafeVixAI uses Prometheus for metric collection and Grafana for visualization - both provisioned as code.

## Monitoring Stack

```mermaid
flowchart TD
    subgraph Services[" Instrumented Services "]
        BE["Backend :8000<br/>/metrics endpoint"]
        CB["Chatbot :8010<br/>/metrics endpoint"]
        FE["Frontend :3000<br/>Web Vitals"]
    end

    subgraph Collection[" Metrics Collection "]
        PROM["Prometheus<br/>Pull-based scraping"]
        PROM_CONFIG["prometheus-config.yml<br/>Scrape configs"]
    end

    subgraph Visualization[" Visualization & Alerting "]
        GRAF["Grafana<br/>Provisioned dashboards"]
        ALERT["Alert Rules<br/>prometheus-rules.yml"]
        EMAIL["Email Alerts<br/>SMTP with 5-min cooldown"]
    end

    subgraph Logs[" Logging "]
        STRUCT["Structured JSON Logs<br/>NDJSON stdout"]
        SENTRY["Sentry Error Tracking<br/>0.05 sample rate"]
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

    class Services control
    class BE control
    class CB ai
    class FE edge
    class Collection neutral
    class PROM edge
    class PROM_CONFIG neutral
    class Visualization neutral
    class GRAF neutral
    class ALERT neutral
    class EMAIL ai
    class Logs neutral
    class STRUCT neutral
    class SENTRY neutral```

## Alert Lifecycle

```mermaid
stateDiagram-v2
    [*] --> OK: All thresholds normal

    OK --> Pending: "Metric exceeds threshold<br/>(within 1m window)"
    Pending --> Firing: Threshold exceeded for 5m

    Firing --> Alerting: Send notification
    Alerting --> Acknowledged: Operator acknowledges

    Acknowledged --> Investigating: Operator investigates
    Investigating --> Resolved: Root cause fixed
    Resolved --> OK: Metrics return to normal

    Firing --> OK: "Metric recovers<br/>(auto-resolve)"
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
| Setup Guide | [`docs/MONITORING_SETUP.md`](observability/MONITORING_SETUP.md) |
| Grafana Dashboard | [`docs/observability/grafana-dashboard.json`](observability/observability/grafana-dashboard.json) |
| Prometheus Config | [`docs/observability/prometheus-config.yml`](observability/observability/prometheus-config.yml) |
| Alert Rules | [`docs/observability/alerts/`](observability/alerts/) |
| Telemetry Guide | [`docs/TELEMETRY.md`](observability/TELEMETRY.md) |
| Performance Benchmarks | [`docs/PERFORMANCE_BENCHMARKS.md`](PERFORMANCE_BENCHMARKS.md) |
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
