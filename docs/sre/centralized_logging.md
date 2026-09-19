# SafeVixAI â€" Centralized Logging Configuration (Grafana Loki)

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

#
# This file configures log shipping from all services to Grafana Loki
# for centralized log aggregation, search, and alerting.

## Architecture
```
Backend (FastAPI) â"€â"€â"
Chatbot (FastAPI) â"€â"€â"¼â"€â"€â--¶ Promtail â"€â"€â--¶ Grafana Loki â"€â"€â--¶ Grafana Dashboard
Frontend (Next.js) â"€â"˜
```

## Loki Configuration

### 1. Install Promtail
```bash
# Docker Compose (recommended)
# Add to docker-compose.yml:
promtail:
  image: grafana/promtail:latest
  volumes:
    - ./promtail-config.yml:/etc/promtail/config.yml
    - /var/log:/var/log
  command: -config.file=/etc/promtail/config.yml
```

### 2. Promtail Config (`promtail-config.yml`)
```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: safevixai
    static_configs:
      - targets:
          - localhost
        labels:
          job: safevixai
          __path__: /var/log/safevixai/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            ts: ts
            request_id: request_id
            method: method
            path: path
            status: status
            duration_ms: duration_ms
      - labels:
          level:
          request_id:
          method:
          path:
          status:
```

### 3. Loki Config (`loki-config.yml`)
```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

### 4. Grafana Dashboard
Import dashboard JSON from `docs/grafana-dashboard.json` or create manually:
- Panel 1: Error rate over time (filter by `level="ERROR"`)
- Panel 2: Request latency p95 (extract `duration_ms`)
- Panel 3: Provider failure rate (filter by `provider_*`)
- Panel 4: Active sessions (from Redis memory)

### 5. Log Format
All services already emit structured JSON logs in production:
```json
{
  "ts": "2026-05-18T12:00:00",
  "level": "INFO",
  "logger": "safevixai.chatbot",
  "msg": "POST /api/v1/chat/ â†' 200 (45.2ms)",
  "request_id": "abc-123",
  "method": "POST",
  "path": "/api/v1/chat/",
  "status": 200,
  "duration_ms": 45.2
}
```

### 6. Alerting Rules
Configure in Grafana:
- Error rate > 5% over 5 minutes â†' Page on-call
- Provider failure rate > 50% over 10 minutes â†' Slack alert
- P95 latency > 2s over 5 minutes â†' Warning
- Memory usage > 80% â†' Warning

## Local Testing
```bash
docker compose -f docker-compose.yml -f docker-compose.loki.yml up
# Access Grafana at http://localhost:3001 (admin/admin)
# Access Loki at http://localhost:3100
```
