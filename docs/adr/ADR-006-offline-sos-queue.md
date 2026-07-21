# ADR-006: Offline-First SOS Queue

**Status:** Accepted
**Date:** 2026-06-29
**Deciders:** SafeVixAI Frontend Team

## Context

SOS alerts and road reports are safety-critical features that must work without internet connectivity. Users may be in areas with poor network coverage during emergencies.

Browser APIs considered:
- **Background Sync API** (`SyncManager`) -- not universally supported
- **Service Workers** -- require HTTPS and user install
- **IndexedDB** -- universally supported in modern browsers, generous storage limits (>50MB typical)

## Decision

Build an IndexedDB-backed offline queue in `frontend/lib/offline-sos-queue.ts`:

1. **Queue storage** -- SOS alerts and road reports are serialized and stored in IndexedDB
2. **Automatic flush** -- when the browser fires an `online` event, queued items are sent in order
3. **SyncManager integration** -- if available, register a sync event for more reliable delivery
4. **Periodic retry** -- if flush fails, retry on a timer (exponential backoff, max 5 attempts)
5. **No server-side changes** -- the same API endpoints handle both online and offline-delayed requests

## Consequences

**Positive:**
- Guaranteed delivery for SOS/road reports even when offline
- IndexedDB storage limits (>50MB) are sufficient for reasonable queue depth
- No server-side changes required -- same endpoints handle deferred delivery
- Backward compatible -- existing API calls work unchanged

**Negative:**
- Queue is browser-specific -- if user clears browser data, queued items are lost
- No cross-device sync -- queue is local to each device
- IndexedDB API is asynchronous and complex

## References

- `frontend/lib/offline-sos-queue.ts` -- queue implementation
- `frontend/lib/crash-detection.ts` -- triggers queue on crash
- `frontend/hooks/useClientServiceWorker.ts` -- registers offline listeners
