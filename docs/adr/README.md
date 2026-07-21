# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for SafeVixAI.
Each ADR documents a significant architectural decision, the context, options considered, and the chosen approach.

## Index

| ADR | Title | Date | Status |
|-----|-------|------|--------|
| [ADR-001](./ADR-001-two-service-architecture.md) | Two-Service Architecture (Backend + Chatbot) | 2026-05-19 | ✅ Accepted |
| [ADR-002](./ADR-002-llm-fallback-chain.md) | 9-Provider LLM Fallback Chain | 2026-05-20 | ✅ Accepted |
| [ADR-003](./ADR-003-postgis-over-mongo.md) | PostGIS for Geospatial Queries | 2026-05-21 | ✅ Accepted |
| [ADR-004](./ADR-004-cqrs.md) | CQRS for Write-Heavy Operations | 2026-06-28 | ✅ Accepted |
| [ADR-005](./ADR-005-redlock.md) | Distributed Locking with Redlock | 2026-06-28 | ✅ Accepted |
| [ADR-006](./ADR-006-offline-sos.md) | Offline-First SOS with IndexedDB Queue | 2026-06-22 | ✅ Accepted |
| [ADR-007](./ADR-007-duckdb-wasm.md) | DuckDB-Wasm for Offline Challan Calculation | 2026-06-22 | ✅ Accepted |
| [ADR-008](./ADR-008-maplibre.md) | MapLibre GL over Google Maps / Leaflet | 2026-05-25 | ✅ Accepted |
| [ADR-009](./ADR-009-jwks.md) | JWKS-Based JWT Verification | 2026-06-28 | ✅ Accepted |
| [ADR-010](./ADR-010-service-worker.md) | Service Worker Caching Strategy | 2026-06-25 | ✅ Accepted |
| [ADR-011](./ADR-011-websocket.md) | WebSocket-Based Live Family Tracking | 2026-06-22 | ✅ Accepted |
| [ADR-012](./ADR-012-rag-vectorstore.md) | ChromaDB for Legal RAG Vector Store | 2026-05-26 | ✅ Accepted |

## What is an ADR?

An Architecture Decision Record is a short document capturing:
- **Context**: Why this decision needed to be made
- **Options**: Alternatives considered
- **Decision**: What was chosen and why
- **Consequences**: Trade-offs and implications

## Status Meanings

- **Proposed**: Under discussion, not yet accepted
- **Accepted**: Agreed upon and implemented
- **Deprecated**: Superseded by a newer ADR
- **Superseded**: Replaced by a newer ADR
