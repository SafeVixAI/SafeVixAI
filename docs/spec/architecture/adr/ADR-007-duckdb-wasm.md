# ADR-007: DuckDB-Wasm for Offline Challan Calculation

**Date:** 2026-06-22
**Status:** ✅ Accepted
**Author:** SafeVixAI Frontend Team

## Context

Challan (traffic fine) calculation requires deterministic, accurate results. The Motor Vehicles Act 2019 has complex rules with state-specific overrides for 36 states/UTs. Using an LLM for this is dangerous — LLMs hallucinate fine amounts and cite wrong sections.

The app must work offline. The calculation must be 100% accurate.

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **DuckDB-Wasm (chosen)** | SQL database compiled to WebAssembly, runs in browser | Deterministic, fast, full SQL, offline | 5MB WASM download, complex setup |
| **Server-side API** | Django/FastAPI endpoint | Simple client | Doesn't work offline |
| **LLM-based** | Ask the chatbot | No client-side data | Hallucinates amounts, not deterministic |
| **JavaScript switch** | Hardcode all rules in JS | No dependencies | 36 states × 100+ violations = 3600+ rules, unmaintainable |

## Decision

Use DuckDB-Wasm (`@duckdb/duckdb-wasm@1.29.0`) executing the same SQL and CSV data sources as the Python backend:
- `violations_seed.csv` — base violation codes and fines
- `state_overrides.csv` — state-specific amendments
- SQL queries: parameterized, exact same logic as `backend/services/challan_service.py`

## Consequences

- Identical results online and offline (same SQL, same data)
- 5MB WASM file loaded lazily on first challan calculation
- CSV data (~200KB) bundled in `public/offline-data/`
- DuckDB loaded via async import — non-blocking, cached after first load
