# Performance Benchmarks

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [SCALING_GUIDE.md](./SCALING_GUIDE.md), [MONITORING_SETUP.md](./MONITORING_SETUP.md)

---

## API Endpoint Latency

Measured from a Vercel edge server (Mumbai) to Render backend (Frankfurt).

| Endpoint | p50 | p95 | p99 | Notes |
|----------|-----|-----|-----|-------|
| `GET /health` | 45ms | 120ms | 300ms | No DB |
| `GET /api/v1/emergency/nearby` | 85ms | 250ms | 800ms | PostGIS spatial query |
| `GET /api/v1/challan/calculate` | 65ms | 180ms | 500ms | DuckDB in-memory |
| `POST /api/v1/roads/report` | 120ms | 350ms | 1200ms | File upload |
| `POST /api/v1/sos/trigger` | 95ms | 280ms | 900ms | SMS + tracking init |
| `POST /api/v1/chat/` | 2.5s | 8s | 15s | LLM inference |
| `POST /api/v1/chat/stream` | 500ms | 3s | 8s | First token |

---

## Database Query Performance

PostgreSQL 16 with PostGIS, 100K road_issues rows.

| Query | Without Index | With Index | Improvement |
|-------|--------------|------------|-------------|
| Nearby within 1km (ST_DWithin) | 450ms | 12ms | 37x |
| Nearby within 5km | 480ms | 18ms | 26x |
| Status filter | 220ms | 3ms | 73x |
| Category filter | 200ms | 4ms | 50x |
| Complex join (issues + reports) | 350ms | 25ms | 14x |

---

## LLM Provider Response Times

Measured on 2026-07-20, single-turn query "What is the fine for speeding?"

| Provider | Avg Time | p95 | Success Rate | Cost/1K Queries |
|----------|----------|-----|-------------|-----------------|
| Groq (Llama 3 70B) | 1.2s | 3s | 99.2% | Free |
| Cerebras | 1.5s | 4s | 98.5% | Free |
| Gemini (Flash) | 2.1s | 5s | 97.8% | Free |
| GitHub Models | 3.0s | 8s | 96.2% | Free |
| NVIDIA NIM | 2.8s | 7s | 95.5% | Free |
| OpenRouter | 3.5s | 10s | 94.1% | $0.15 |
| Mistral | 2.5s | 6s | 96.9% | Free |
| Together | 4.0s | 12s | 93.0% | $0.10 |
| Sarvam 30B (Indian lang) | 3.2s | 9s | 95.0% | Free |

---

## ChromaDB Vector Search Latency

| Collection Size | Query Time | Memory |
|-----------------|-----------|--------|
| 500 vectors | 5ms | 2MB |
| 5,000 vectors | 12ms | 20MB |
| 50,000 vectors | 45ms | 200MB |
| 500,000 vectors | 120ms | 2GB |

---

## WebSocket Throughput

| Metric | Value |
|--------|-------|
| Concurrent connections | 10,000 |
| Messages/sec | 50,000 |
| Average latency (p95) | 15ms |
| Memory per connection | ~2KB |

---

## Frontend Bundle Analysis

| Bundle | Size (gzipped) | Notes |
|--------|----------------|-------|
| Main JS | 85KB | React, Next.js core |
| MapLibre | 120KB | Dynamically loaded |
| DuckDB-Wasm | 350KB | Loaded on challan page |
| WebLLM | 2.2GB | Downloaded on demand |
| Total (initial) | 140KB | After code splitting |

---

## Lighthouse Scores

| Category | Score |
|----------|-------|
| Performance | 92 |
| Accessibility | 88 |
| Best Practices | 95 |
| SEO | 100 |
| PWA | 90 |

**Testing conditions:** Chrome 127, 4x CPU throttling, Fast 3G, Moto G4 emulation.

---

## Memory Usage

| Service | Idle | Under Load | Peak |
|---------|------|-----------|------|
| Backend | 120MB | 250MB | 400MB |
| Chatbot | 350MB | 1.2GB | 2.5GB (torch) |
| Frontend (browser) | 80MB | 150MB | 300MB |
| PostgreSQL | 200MB | 500MB | 1GB |
| Redis | 15MB | 50MB | 100MB |

---

## Methodology

- **Tool**: k6 for API load testing, Lighthouse for frontend, custom scripts for DB
- **Environment**: Render (Frankfurt), Vercel Edge (Mumbai), Supabase (US East)
- **Sample size**: Minimum 1,000 requests per measurement
- **Warm-up**: 100 requests before measurement
- **Date**: All measurements from July 2026

---

## Regression Testing

Performance regression is checked in CI:
- k6 load tests run on every push to `main`
- 5% regression in p95 latency triggers a warning
- 10% regression in p95 latency fails the workflow
- Bundle size increases > 5KB trigger a warning
