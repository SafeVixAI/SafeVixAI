# ADR-010: Service Worker Caching Strategy

**Date:** 2026-06-25
**Status:** ✅ Accepted
**Author:** SafeVixAI Frontend Team

## Context

The app is a PWA that must work offline. Service Workers are the standard mechanism for caching assets and API responses. The caching strategy must balance:
- Offline functionality (core pages must render without network)
- Freshness (SOS endpoint must always hit the network)
- Storage limits (~50MB quota in most browsers)

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Cache-First then Network (chosen)** | Serve from cache, update from network | Fastest offline, always fresh eventually | Slightly stale data until network responds |
| **Network-Only** | Never cache dynamic data | Always fresh | No offline functionality |
| **Stale-While-Revalidate** | Serve cached immediately, fetch update in background | Best UX, instant responses | Implementation complexity |
| **Workbox** | Google's SW library | Pre-built strategies, easy setup | ~50KB added to bundle |

## Decision

Use a custom Service Worker with tiered strategy:
- **Static assets** (JS, CSS, fonts, images): Cache-first with versioned cache
- **App shell** (HTML shell): Network-first with cache fallback (offline page)
- **API responses** (emergency numbers, challan data): Stale-while-revalidate
- **SOS endpoint**: Network-only (never cache emergency data)
- **User data**: Network-only with offline queue (see ADR-006)

## Consequences

- Full offline experience for app shell + cached data
- SOS alerts never delayed by cache staleness
- Service Worker registered in `layout.tsx`, activates on first load
- Cache storage ~15-20MB for full offline experience
- SW only activates in production (`npm run build && npm start`)
