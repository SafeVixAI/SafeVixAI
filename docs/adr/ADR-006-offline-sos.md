# ADR-006: Offline-First SOS with IndexedDB Queue

**Date:** 2026-06-22
**Status:** ✅ Accepted
**Author:** SafeVixAI Frontend Team

## Context

SOS alerts are the most critical feature — they must work even when the user has no internet connection. The app cannot rely on server-side processing during network outages.

Design requirements:
- SOS must trigger and capture GPS even offline
- Family notification must happen when connectivity is restored
- User must see feedback that their SOS was queued

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **IndexedDB queue (chosen)** | Queue SOS payloads in IndexedDB, flush on `online` event | Works offline, survives page reload, no server needed | ~100 lines of custom queue logic |
| **Service Worker** | Intercept fetch, queue in SW cache | SW can retry in background | SW lifecycle complexity, harder to debug |
| **Heartbeat server** | Client sends periodic pings, server infers SOS | No client queue | Doesn't work offline at all |

## Decision

Implement `offline-sos-queue.ts` with:
1. SOS payload (GPS, blood group, vehicle, contacts) stored in IndexedDB
2. `navigator.onLine` check determines online vs offline path
3. Background Sync API (`SyncManager`) for automatic retry when online
4. IndexedDB as persistence layer (survives tab close, crash, browser restart)
5. Proactive flush on `window.online` event in addition to SyncManager

## Consequences

- SOS latency: 0ms offline (queued instantly) vs ~500ms online (HTTP round trip)
- Offline SOS visualized with "Dispatch Armed" badge in UI
- IndexedDB queue survives browser restart
- Background Sync may not fire in all browsers — `online` event listener provides fallback
