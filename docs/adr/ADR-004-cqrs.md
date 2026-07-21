# ADR-004: CQRS for Write-Heavy Operations

**Date:** 2026-06-28
**Status:** ✅ Accepted
**Author:** SafeVixAI Backend Team

## Context

The roadwatch service handles both read-heavy queries (browsing reports, moderation feeds) and write-heavy operations (submitting reports, verifying photos, updating statuses). The original monolithic service had:
- 880+ lines in a single `roadwatch_service.py`
- Mixed read/write concerns in the same functions
- No clear separation between commands and queries

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **CQRS (chosen)** | Separate Command and Query message buses | Clear separation, independent scaling, audit trail | More boilerplate, learning curve |
| **Repository pattern** | Standard CRUD repositories | Simpler, well-understood | Doesn't solve mixed concerns |
| **Service layer only** | Keep as-is with refactoring | Lowest effort | Still mixed concerns |

## Decision

Implement a lightweight CQRS bus without external dependencies:
- `Command` / `Query` base classes with typed payloads
- `CommandBus` and `QueryBus` singletons with middleware support
- Middleware chain: logging → validation → security → handler
- Applied to `SubmitReportCommand`, `VerifyReportCommand` in roadwatch

## Consequences

- `roadwatch_service.py` split: 880 → 1095 lines (roadwatch + roadwatch_photos + moderation)
- Each command/query is independently testable
- Middleware can be added (metrics, idempotency) without touching handlers
- Slightly more files to maintain per feature
