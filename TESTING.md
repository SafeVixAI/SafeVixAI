# Testing

> **Testing standards, coverage targets, and CI integration across all 3 services.**

SafeVixAI maintains 7,687+ unit tests across backend, chatbot, and frontend with enterprise-grade coverage thresholds.

---

## Quick Links

| Area | Documentation |
|------|---------------|
| Testing Policy | [`TESTING_POLICY.md`](TESTING_POLICY.md) |
| Testing Policy (detailed) | [`docs/TESTING_POLICY.md`](docs/TESTING_POLICY.md) |
| Code Review Guide | [`docs/CODE_REVIEW_GUIDE.md`](docs/CODE_REVIEW_GUIDE.md) |
| Style Guide | [`STYLE_GUIDE.md`](STYLE_GUIDE.md) |
| CI Workflows | [`.github/workflows/`](.github/workflows/) |

---

## Test Counts

| Service | Framework | Tests | Coverage Threshold |
|---------|-----------|-------|--------------------|
| Backend | pytest + hypothesis + testcontainers | 2,912 | 100% lines, 100% branches |
| Chatbot | pytest + pytest-httpx + ChromaDB | 1,819 | 97%+ lines |
| Frontend | Jest + RTL + jest-axe | 2,956 | 86% lines, 72% branches |
| E2E | Playwright | 55 | — |
| Mutation | mutmut (backend) | — | CI (informational) |

---

## Running Tests

```bash
# Backend (asyncio_mode = auto)
cd backend && pytest tests/ -v --cov

# Chatbot (asyncio_mode = strict — requires @pytest.mark.asyncio)
cd chatbot_service && pytest tests/ -v --cov

# Frontend
cd frontend && npm test && npm run lint && npx tsc --noEmit
```

---

## Related

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to write and run tests
- [`CI/CD workflows`](.github/workflows/) — automation in CI
- [`STYLE_GUIDE.md`](STYLE_GUIDE.md) — coding standards
