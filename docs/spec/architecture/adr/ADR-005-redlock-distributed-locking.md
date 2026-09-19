# ADR-005: Redlock Distributed Locking

**Status:** Accepted
**Date:** 2026-06-29
**Deciders:** SafeVixAI Backend Team

## Context

Several backend operations required distributed mutual exclusion:

- **Idempotency keys** -- prevent duplicate processing of the same request across multiple workers
- **City center seeding** -- ensure seed scripts run exactly once even if deployed to multiple replicas
- **Cache stampede protection** -- prevent concurrent cache rebuilds under high load

Redis provides the `SET NX EX` pattern for simple locks, but this is not safe across multiple Redis nodes or when a lock holder crashes without releasing.

## Decision

Implement the Redlock distributed lock algorithm in `backend/core/distributed_lock.py`:

1. **LockManager** -- main interface with `acquire()` and `release()` methods
2. **Redlock** -- distributed lock using Redis `SET NX EX` with automatic key expiry
3. **Local fallback** -- when Redis is unavailable, falls back to `asyncio.Lock` for single-process correctness
4. **Lock context manager** -- `async with lock_manager.acquire("key"):` pattern

Each lock has a configurable TTL (default 30s) and a unique random value to prevent accidental release by other workers.

## Consequences

**Positive:**
- Safe distributed mutual exclusion across multiple worker processes
- Graceful degradation to local locks when Redis is unavailable
- Automatic lock expiry prevents deadlocks

**Negative:**
- Minor latency overhead (~5ms per lock acquisition)
- Clock drift between Redis nodes could theoretically cause safety violation (acceptable risk for single Redis instance)
- Requires careful TTL estimation to prevent premature expiry

## References

- `backend/core/distributed_lock.py` -- LockManager, Redlock implementation
- `backend/core/idempotency.py` -- uses Redlock for idempotency key isolation
