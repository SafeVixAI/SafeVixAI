# Testing Policy

> **Last Updated:** 2026-07-21

This document defines the testing standards, thresholds, and procedures for SafeVixAI.

## Testing Philosophy

1. **Deterministic over probabilistic** — Use SQL (not LLM) for any calculation that must be 100% accurate (e.g., challan fines)
2. **Offline-first** — All critical user flows must have offline tests
3. **Defense in depth** — Unit tests + contract tests + integration tests + E2E tests
4. **Coverage thresholds** must be met before any release is cut

## Coverage Thresholds

### Frontend
| Metric | Threshold | Current |
|--------|-----------|---------|
| Lines | 86% | 87.22% |
| Branches | 72% | 73.13% |
| Functions | 80% | 81.06% |
| Statements | 85% | 85.38% |

### Backend
| Metric | Threshold | Current |
|--------|-----------|---------|
| Lines | 100% | 100% |
| Branches | 100% | 100% |

### Chatbot Service
| Metric | Threshold | Current |
|--------|-----------|---------|
| Lines | 95% | 97%+ |

## Running Tests

### Frontend
```bash
cd frontend
npm test              # Run all tests
npm test -- --watch   # Watch mode
npm run lint          # ESLint
npx tsc --noEmit      # TypeScript type-check
npm run build         # Production build (includes type-check)
```

### Backend
```bash
cd backend
.venv\Scripts\activate
pytest tests/ -v                                # All tests
pytest tests/ -v --cov --cov-report=html        # With coverage report
pytest tests/test_challan.py -v                 # Single file
```

### Chatbot Service
```bash
cd chatbot_service
.venv\Scripts\activate
pytest tests/ -v
pytest tests/ -v --cov --cov-report=html
```

## Test Types

| Type | Tool | Owner | Run Frequency |
|------|------|-------|---------------|
| Unit | Jest (frontend), pytest (backend/chatbot) | All devs | Every commit |
| Contract | pydantic schema validation | Backend devs | Every commit |
| Property-based | Hypothesis (backend) | Backend devs | Every commit |
| Integration | testcontainers-postgres, ChromaDB | Backend/chatbot devs | CI |
| Accessibility | jest-axe | Frontend devs | CI |
| E2E | Playwright | All devs | Release candidates |
| Mutation | mutmut (backend) | Backend devs | CI (informational) |

## Test File Conventions

- Place test files next to source files in `__tests__/` directories (frontend) or in `tests/` (backend/chatbot)
- Backend test files: `tests/test_<module_name>.py`
- Chatbot test files: `tests/test_<module_name>.py`
- Frontend test files: `__tests__/<ComponentName>.test.tsx`
- Use `function()` syntax (not arrow functions) in `describe`/`it`/`beforeEach` blocks
- Use `var` for module-scoped variables to avoid TDZ in hoisted `jest.mock()` factories

## CI Testing

All tests run automatically in CI via GitHub Actions:
- `backend.yml` — Backend tests + coverage
- `chatbot.yml` — Chatbot tests + coverage
- `frontend.yml` — Lint + type-check + tests + coverage

## Pre-Release Checklist

- [ ] All suites passing (0 failures)
- [ ] Frontend lint: 0 warnings, 0 errors
- [ ] TypeScript: 0 errors (strict mode)
- [ ] Backend coverage: 100% lines + branches
- [ ] Chatbot coverage: 95%+ lines
- [ ] Frontend coverage meets thresholds
- [ ] E2E tests: 55/55 passing
