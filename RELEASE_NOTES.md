# Release Notes

## v1.0.0 — 2026-07-20

Initial production release of SafeVixAI, an AI-powered road safety PWA for the IIT Madras Road Safety Hackathon 2026.

### New Features

- **Emergency Locator**: PostGIS-powered nearest hospital/police/fire station with MapLibre GL navigation and QR-based emergency card sharing
- **AI Chatbot**: 13-tool agentic RAG system with 9-provider LLM fallback chain, Indian language support (14 languages), and offline WebLLM fallback
- **Challan Calculator**: Deterministic SQL-based fine calculation for 50+ violations across 36 states/UTs with DuckDB-Wasm offline support
- **Road Reporter**: Submit road damage reports with photo upload, auto-geotagging, and moderation verification workflow
- **SOS**: Hold-to-activate emergency alert with live family tracking via WebSocket (GPS, speed, battery)
- **Bystander Mode**: Report accidents as passerby with GPS capture, nearest hospital lookup, and first aid guidance
- **Command Center**: Real-time agency dashboard with incident timeline, resolution analytics, and escalation board
- **Crisis Landing Page**: Animated hero with Three.js globe, IIT Madras branding, and scroll-triggered section reveals
- **Offline Support**: PWA with service worker caching, IndexedDB offline SOS queue, and WebLLM Phi-3 Mini offline AI
- **Privacy Architecture**: Blood group and emergency contacts stored exclusively in IndexedDB (never leaves device)

### Enterprise Features

- CQRS command/query bus for write-heavy roadwatch operations
- Redlock distributed locking for idempotency and cache stampede protection
- Circuit breaker pattern on all 8 external API calls (3-failure threshold, 30s half-open)
- JWKS-based JWT validation with atomic key fetching and stale-while-revalidate
- Token bucket rate limiting on all API endpoints
- SLSA Level 3 provenance attestation with cosign keyless container signing
- SBOM generation (CycloneDX + SPDX formats)
- Prometheus + Grafana monitoring with alerting rules
- 12 incident response runbooks with severity matrix and escalation path

### Infrastructure

- Docker Compose (5 services: postgres, redis, backend, chatbot, frontend)
- Kubernetes manifests (kustomize: 15 resources with network policies)
- Terraform AWS modules (VPC, ECS, RDS, ElastiCache, WAF, Route53)
- Vercel (frontend) and Render (backend + chatbot) deployment configs

### Test Statistics

| Service | Tests | Coverage (Lines) |
|---------|-------|-----------------|
| Backend | 2750 | 100% |
| Chatbot | 1613 | 97%+ |
| Frontend | 2956 | 87.22% |
| E2E | 55 | — |

### Known Issues

- 10 backend tests fail in isolation (run full `pytest tests/` suite)
- 2 chatbot tests fail in isolation (run full `pytest tests/` suite)
- 8 E2E form validation tests fail in production standalone build (React 19 RSC event handler registration issue)
- 65 Dependabot vulnerabilities (1 critical, tracked via Dependabot alerts)

### Migration Notes

- First release — no migration needed
