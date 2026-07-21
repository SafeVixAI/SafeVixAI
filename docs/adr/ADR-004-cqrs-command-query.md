# ADR-004: CQRS Command-Query Separation

**Status:** Accepted
**Date:** 2026-06-29
**Deciders:** SafeVixAI Backend Team

## Context

The RoadWatch service (`backend/services/roadwatch_service.py`) had grown to 880+ lines mixing read and write concerns within a single service class. This led to:

- Difficulty testing read logic without triggering write side effects
- No audit trail for which commands were executed
- Tight coupling between query formatting and command validation
- Difficulty adding cross-cutting concerns (logging, metrics, idempotency) without touching every method

## Decision

Adopt the CQRS (Command Query Responsibility Segregation) pattern with:

1. **Command Bus** (`CommandBus` in `backend/core/cqrs.py`) -- handles all mutations (SubmitReport, VerifyReport, etc.)
2. **Query Bus** (`QueryBus` in `backend/core/cqrs.py`) -- handles all read operations
3. **Middleware pipeline** -- each bus supports middleware chains for cross-cutting concerns
4. **Handler registration** -- `CommandHandler` and `QueryHandler` base classes registered during app startup via `init_cqrs_bus(app)`

Commands and queries are plain Pydantic models. Handlers are stateless service classes that receive the command and return a result.

## Consequences

**Positive:**
- Read/write separation enables independent testing
- Middleware pipeline handles logging, validation, idempotency without service changes
- Clear audit trail of all mutations
- New commands/queries can be added without modifying existing handlers

**Negative:**
- Added indirection for simple CRUD operations
- More boilerplate for trivial operations
- Learning curve for developers unfamiliar with CQRS

## References

- `backend/core/cqrs.py` -- CommandBus, QueryBus, middleware interfaces
- `backend/services/roadwatch_service.py` -- SubmitReportCommand, VerifyReportCommand implementations
- `init_cqrs_bus(app)` called in main.py app factory
