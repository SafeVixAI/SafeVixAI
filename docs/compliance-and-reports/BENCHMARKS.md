# Benchmarks

> **Performance benchmarks, latency targets, throughput measurements, and SLA commitments.**

Formal benchmarks for all SafeVixAI services, measured via k6 load testing and pytest performance tests.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [`docs/PERFORMANCE_BENCHMARKS.md`](../sre/PERFORMANCE_BENCHMARKS.md) | Detailed latency, throughput, resource benchmarks |
| [`backend-smoke.js`](https://github.com/SafeVixAI/SafeVixAI/blob/main/k6/backend-smoke.js) | k6 smoke test — 1 VU, all 25 endpoints |
| [`backend-load.js`](https://github.com/SafeVixAI/SafeVixAI/blob/main/k6/backend-load.js) | k6 load test — 100 VU, 5 min |
| [`backend-stress.js`](https://github.com/SafeVixAI/SafeVixAI/blob/main/k6/backend-stress.js) | k6 stress test — ramp to 500 VU |
| [`chatbot-smoke.js`](https://github.com/SafeVixAI/SafeVixAI/blob/main/k6/chatbot-smoke.js) | k6 chatbot — 20 VU chat, 10 VU stream |

---

## Service Level Targets

```mermaid
flowchart LR
    subgraph BackendSLAs[" Backend SLAs "]
        H["/health<br/>1000 rps | 100ms"]
        E["/emergency/nearby<br/>500 rps | 200ms"]
        C["/challan/calculate<br/>200 rps | 300ms"]
        R["/roadwatch/issues<br/>100 rps | 500ms"]
    end

    subgraph ChatbotSLAs[" Chatbot SLAs "]
        CH["/chat/<br/>20 rps | 5s"]
        ST["/chat/stream<br/>10 rps | 30s"]
    end


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

    class BackendSLAs control
    class H neutral
    class E neutral
    class C neutral
    class R neutral
    class ChatbotSLAs ai
    class CH neutral
    class ST neutral```

| Service | Endpoint | P95 Target | Throughput |
|---------|----------|------------|------------|
| Backend | `/health` | < 100ms | 1000 req/s |
| Backend | `/api/v1/emergency/nearby` | < 200ms | 500 req/s |
| Backend | `/api/v1/challan/calculate` | < 300ms | 200 req/s |
| Backend | `/api/v1/roadwatch/issues` | < 500ms | 100 req/s |
| Chatbot | `/api/v1/chat/` | < 5s | 20 req/s |
| Chatbot | `/api/v1/chat/stream` | < 30s (total) | 10 streams/s |

---

## Running Benchmarks

```bash
# k6 — requires k6 CLI
k6 run k6/backend-smoke.js
k6 run k6/backend-load.js
k6 run k6/backend-stress.js
k6 run k6/chatbot-smoke.js

# Python performance tests
cd backend && pytest tests/ -v -k "perf" --benchmark-only
```

---

## Test Results History

See [`docs/PERFORMANCE_BENCHMARKS.md`](../sre/PERFORMANCE_BENCHMARKS.md) for historical benchmark data and regression tracking.

---

## Related

- [`docs/MONITORING_SETUP.md`](../sre/observability/MONITORING_SETUP.md) — production monitoring
- [`docs/SCALING_GUIDE.md`](../sre/SCALING_GUIDE.md) — horizontal scaling
