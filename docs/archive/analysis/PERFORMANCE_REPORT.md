# SafeVixAI — Performance Report

> **SNAPSHOT**: This document reflects the state as of 2026-05-26. For current state see [AGENTS.md](../../AGENTS.md).

**Date:** 2026-05-26

---

## 1. Frontend Performance

### Current State
| Metric | Target | Status | Notes |
|--------|--------|--------|-------|
| First Load JS | < 300KB gzipped per route | ✅ | Dynamic imports for MapLibre, DuckDB, QR |
| LCP | < 2.5s | ⚠️ | MapLibre loads ~200KB, SSR-disabled |
| CLS | < 0.1 | ✅ | AppFrame layout, no layout shift |
| INP | < 200ms | ⚠️ | GSAP animations on input may affect INP |
| Lighthouse Perf | ≥ 85 | ⚠️ | Need audit (Render cold start affects scores) |
| Lighthouse A11y | ≥ 90 | ⚠️ | Skip links OK, aria labels partial |
| Bundle size (main) | ~280KB | ✅ | Next.js code splitting good |

### Optimization Applied
- ✅ Dynamic imports for MapLibre, DuckDB-Wasm, QR code
- ✅ GSAP only animates transform/opacity (GPU-composited)
- ✅ `will-change` cleared in onComplete
- ✅ `prefers-reduced-motion` → `timeScale(1000)`
- ✅ Zustand granular selectors (30+) prevent re-render
- ✅ GSAP tweens killed on route change
- ✅ No continuous animations (width/height/top/left)

### Optimization Needed
- ❌ Convert Axios to SWR for caching/revalidation (90% of pages)
- ❌ React.memo on: ServiceCard, MessageBubble, MapMarker
- ❌ useCallback on all callback props
- ❌ useMemo on expensive computations (distance sort)
- ❌ `dvh` instead of `vh` for mobile viewport

---

## 2. Backend Performance

| Metric | Current | Notes |
|--------|---------|-------|
| API response (cached) | < 200ms | Redis + in-memory cache |
| API response (cold) | < 2s | DB query + spatial index |
| Emergency locator | < 500ms | GIST index + radius stepping |
| Overpass API call | 1-3s | Depends on server load |
| PostGIS query | < 50ms | GIST index on location |
| Rate limit detection | < 1ms | In-memory + optional Redis |

### Bottlenecks
1. **Single worker** on Render free — no request parallelism
2. **No connection pooling** — Render pool=1
3. **Synced LLM calls** — `asyncio.wait_for` blocks provider API
4. **Render cold start** — 5-15s for first request after idle

---

## 3. Chatbot Performance

| Metric | Provider | Latency |
|--------|----------|---------|
| Groq Llama-3.1-8B | Fastest | 200-500ms |
| Cerebras | Fast | 300-800ms |
| Gemini 1.5 Flash | Moderate | 500ms-1.5s |
| Sarvam (Indic) | Slow | 1-5s |
| Template (fallback) | Instant | < 10ms |

### LLM Fallback Timing
When all providers fail (worst case): ~45-60s total before Template response
- 30s timeout × 10 providers = 270s theoretical max
- Circuit breakers + skip-on-error reduce to ~45-60s actual

### ChromaDB RAG
- Query time: < 100ms (HNSW index, cosine similarity)
- Embedding: ~50ms (sentence-transformers MiniLM)
- Total retrieval: < 200ms

---

## 4. Database Performance

| Query | Index | Time |
|-------|-------|------|
| Emergency near lat/lon | GIST on location | < 50ms |
| Road issues by status | B-tree on status + city | < 20ms |
| Chat logs by session | B-tree on session_id | < 10ms |
| State override lookup | Composite on (section, state) | < 5ms |
| Traffic violations by section | B-tree on section_number | < 5ms |

---

## 5. Lighthouse Targets

| Page | Est. Performance | Est. Accessibility | Notes |
|------|-----------------|--------------------|-------|
| / | 65-75 | 75-85 | MapLibre heavy, skip SSR |
| /emergency | 80-90 | 85-95 | Static data, light JS |
| /challan | 85-95 | 85-95 | SWR caches, simple UI |
| /assistant | 55-65 | 75-85 | SSE streaming, large bundle |
| /first-aid | 90-100 | 85-95 | Static content |

**Need real Lighthouse CI run to confirm.**
