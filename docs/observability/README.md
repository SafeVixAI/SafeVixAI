# Observability

Monitoring, logging, tracing, and alerting configuration for SafeVixAI.

## Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Logging | Structured JSON logging | `core/structured_logging.py`, `core/logging.py` |
| Tracing | OpenTelemetry | `core/tracing.py`, `core/service_tracing.py` |
| Metrics | Prometheus | `core/metrics.py` |
| Alerting | Email alerts | `core/alert.py` (5-min cooldown, 3 diagnostic solutions) |
| Health Checks | `/health` endpoints | Backend :8000, Chatbot :8010 |

## Configuration

Environment variables for observability are documented in `docs/Environment.md`.
