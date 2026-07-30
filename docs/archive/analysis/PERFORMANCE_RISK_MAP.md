# SafeVixAI — Performance Risk Map

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

> Generated: 2026-05-22 | Bottlenecks, scaling limits, optimization targets

---

## 1. Critical Performance Paths

### SOS Dispatch (Latency-Sensitive)
```
Goal: <500ms end-to-end for SOS trigger → backend ack
  ├── Frontend: GlobalSOS button → haptic → POST /api/v1/emergency/sos
  ├── Backend: SosIncident record → EmergencyLocator (cached results)
  └── Expected: ~200ms (cached) / ~2s (uncached, Overpass)
Risk: Uncached SOS on cold start could take 3-5s
```

### Chatbot Streaming (Perception-Sensitive)
```
Goal: First token <2s, complete response <10s
  ├── Frontend: POST /api/v1/chat/stream → SSE proxy
  ├── Backend: LLMService → Chatbot ChatEngine
  ├── Chatbot: SafetyChecker + IntentDetector + ContextAssembler (~200ms)
  ├── Chatbot: ProviderRouter.generate() → LLM API call
  │   ├── Groq: ~300ms-2s (fastest, 300+ tok/s)
  │   ├── Gemini: ~500ms-3s
  │   └── Template: ~5ms (instant)
  └── Simulated streaming: 12ms/word (adds latency for UX)
Risk: Timeout at 20s, fallback chain adds cumulative delay
```

### Emergency Locator (Data-Heavy)
```
Goal: <2s response (cached), <5s (uncached)
  ├── Cache: Redis get → 5ms (hit)
  ├── DB: PostGIS ST_DWithin → 50-200ms
  ├── Local CSV: Haversine scan → 10-50ms
  └── Overpass: External API → 1-5s (3 mirrors with retry)
Risk: Overpass timeout can take 10s+ with retry + backoff
```

---

## 2. Bottleneck Analysis

### Backend

| Bottleneck | Impact | Current | Target | Fix |
|-----------|--------|---------|--------|-----|
| Single-threaded workers | No parallelism | 1 worker (Render) | 4+ workers | Render Starter plan |
| DB connection pool | Connection starvation | Pool=1 (Render) | Pool=10 | Remove Render override |
| Heavy service init | Cold start latency | ~2s init + 5-30s speech | <2s | Preload services async |
| No query result pagination | Memory pressure | Some endpoints unlimited | Limit 50 | Add pagination |
| Synchronous LLM proxy | Blocks request thread | 20s timeout | Streaming | Full SSE passthrough |

### Chatbot

| Bottleneck | Impact | Current | Target | Fix |
|-----------|--------|---------|--------|-----|
| Synced LLM calls | Blocks until complete | asyncio.wait_for(20s) | True streaming | Per-provider streaming |
| Simulated streaming | Adds fake latency | 12ms/word | True token streaming | Provider SSE support |
| ChromaDB init | Cold start delay | ~3s | <1s | Preload+persist connection |
| Full history on every request | Token waste | Last 12 messages | Summary-only | Upgrade summarizer |
| Python heavy inference | CPU bound | ~2GB torch | Lightweight | CPU inference optimization |

### Frontend

| Bottleneck | Impact | Current | Target | Fix |
|-----------|--------|---------|--------|-----|
| All pages client-rendered | No RSC benefit | 17 'use client' pages | Hybrid | Server components for static |
| Large globals.css | Unused CSS bytes | 1607 lines | Purged | purgeCSS in build |
| WebLLM model download | User wait time | 2.2GB (Phi-3) / 1.3GB (Gemma 4) | On-demand | Lazy load + progress |
| Service worker activation | Prod only | `npm run build && npm start` | Dev SW | Add dev SW for testing |
| Map tile load | Blank map flash | 3 backends | Parallel | Preconnect + cache |

### Infrastructure

| Bottleneck | Impact | Current | Target | Fix |
|-----------|--------|---------|--------|-----|
| Render free tier idle | 30-60s cold start | Spins down at 15min idle | Always on | Render Starter ($7) |
| Render 512MB RAM | OOM under load | 512MB | 1GB+ | Render Starter |
| Upstash 10K cmd/day | Rate limit failure | 10K/day | 100K/day | Upstash Pay-as-you-go ($5) |
| Supabase 500MB DB | Storage limit | ~50K facilities | 1M+ | Supabase Pro ($25) |
| Single region Singapore | Latency for non-Asia users | 1 region | Multi-region | Enterprise plans |

---

## 3. Scaling Limits

| Resource | Hard Limit | Soft Limit | Failure Mode |
|----------|-----------|-----------|-------------|
| Groq API | 30 RPM / 14K RPD | 20 RPM | Falls to Cerebras → Gemini → ...→ Template |
| Overpass API | 10K queries/day | 5K/day | Falls to Healthsites.io → empty results |
| Nominatim | 1 req/s | 0.5 req/s | Falls to Photon (unlimited) |
| OpenRouteService | 2K req/day | 1K/day | Falls to OSRM (free, slower) |
| What3Words | 50K req/month | 25K/month | Tool returns None |
| OpenCage | 2.5K req/day | 1K/day | Geocoding returns None |
| Supabase Storage | 2GB | 1GB | Photo uploads fail |
| Sentry | 5K errors/month | 3K/month | No error tracking |
| Vercel bandwidth | 100GB/month | 50GB/month | Site throttled |
| Render build hours | 500 min/month | 300 min/month | Deploy blocked |

---

## 4. Optimization Priority Matrix

| Priority | Optimization | Effort | Impact | Area |
|----------|-------------|--------|--------|------|
| P0 | Expose `/metrics` endpoint | 5 min | HIGH | Observability |
| P0 | Set DB pool_size >= 5 | Config change | HIGH | Backend |
| P0 | Add response pagination | 1 day | HIGH | Backend |
| P1 | True SSE streaming from providers | 3 days | HIGH | Chatbot |
| P1 | Render Starter upgrade | Config | HIGH | Infra |
| P1 | Add Redis pooling | Config | MEDIUM | Infra |
| P1 | Purge unused CSS | 1 day | MEDIUM | Frontend |
| P1 | Preconnect to map tile CDNs | 1 hour | MEDIUM | Frontend |
| P2 | Server components for static pages | 2 days | MEDIUM | Frontend |
| P2 | LLM response caching (Redis) | Implemented | MEDIUM | Chatbot |
| P2 | Conversation summarization | Implemented | MEDIUM | Chatbot |
| P2 | Async model preload | Implemented | LOW | Chatbot |
| P3 | Bundle analyzer audit | 1 day | LOW | Frontend |
| P3 | Tree-shake unused deps | 1 day | LOW | Frontend |
| P3 | WASM binary optimization | 2 days | LOW | Frontend |
