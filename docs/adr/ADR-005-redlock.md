# ADR-005: Distributed Locking with Redlock

**Date:** 2026-06-28
**Status:** ✅ Accepted
**Author:** SafeVixAI Backend Team

## Context

The application has several operations that require mutual exclusion across multiple backend instances:
- Idempotency key processing (same request must not be handled twice)
- Cache stampede protection (only one instance should rebuild a stale cache)
- ETL pipeline coordination (city center seeding, data ingestion)

Without distributed locking, concurrent requests could cause duplicate processing, race conditions, or data corruption.

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Redlock (chosen)** | Redis-based distributed lock with TTL, retry, and fencing | Industry standard, battle-tested at Redis/Reddit/Slack | Requires Redis, clock drift assumptions |
| **PostgreSQL advisory locks** | `pg_advisory_lock()` | No extra dependency | Locks held across transactions, connection pool pressure |
| **Local mutex** | `asyncio.Lock` per instance | Simple, no dependencies | Doesn't work across instances |

## Decision

Implement a `DistributedLock` class using the Redlock algorithm:
- Lock acquisition with SET NX EX + random value (for safe release)
- Automatic TTL with background refresh for long operations
- Graceful fallback to `asyncio.Lock` when Redis is unavailable
- Used by: idempotency middleware, cache stampede protection, ETL scheduler

## Consequences

- Lock TTL must be tuned per operation (default 5s, configurable)
- Clock skew between instances could theoretically break safety — mitigated by short TTLs
- Redis dependency for distributed features (falls back to local lock without Redis)
