# Testing Policy

## Policy Statement

All major new functionality MUST include automated tests before being merged into `main`.

## Scope

This policy applies to all three codebases in this repository:

| Service | Language | Test Framework | Coverage Tool |
|---------|----------|----------------|---------------|
| `backend/` | Python (FastAPI) | pytest | pytest-cov |
| `chatbot_service/` | Python (FastAPI) | pytest | pytest-cov |
| `frontend/` | TypeScript (Next.js) | Jest | jest --coverage |

## Requirements

### 1. New Feature Tests
- **Backend/Chatbot (Python):** Add unit tests for all new API endpoints, service functions, and utility modules. Use pytest fixtures for database/Redis mocking where applicable.
- **Frontend (TypeScript):** Add unit tests for new components, hooks, and utility functions. Use React Testing Library for component tests.
- **E2E (Playwright):** Add Playwright E2E tests for new user-facing flows (required for UI changes).

### 2. Coverage Targets
| Target | Current | Badge Level |
|--------|---------|-------------|
| Backend: 100% lines + branches | 100% / 100% | 🥇 Gold |
| Chatbot: ≥97% lines | 97%+ | 🥇 Gold |
| Frontend: ≥86% lines, ≥72% branches | 87.22% / 73.13% | 🥈 Silver |
| Backend: ≥90% statement, ≥80% branch | 100% / 100% | 🥇 Gold (achieved) |
| Chatbot: ≥90% statement, ≥80% branch | 97%+ / ~85%+ | 🥇 Gold (achieved) |
| Frontend: ≥90% statement, ≥80% branch | 87.22% / 73.13% | 🥇 Gold (target for v1.1) |

Coverage thresholds are enforced in CI via `--cov-fail-under` (Python) and `jest --coverage` thresholds. Branch coverage (`--cov-branch`) is measured for Python services.

### 3. Regression Tests
- At least 50% of bugs fixed in the last 6 months MUST have a regression test added (Silver tier requirement).

### 4. CI Enforcement
All tests run automatically via GitHub Actions on every push/PR:
- `backend.yml` — pytest + fuzz tests
- `chatbot.yml` — pytest
- `frontend.yml` — Jest
- `e2e.yml` — Playwright E2E

All CI checks must pass before merge.

### 5. PR Checklist
Every pull request MUST confirm:
- [ ] Tests added/updated for new/modified functionality
- [ ] All CI checks pass (or known failures documented)
- [ ] Coverage has not regressed below threshold

## Exceptions

Minor changes (typo fixes, refactoring without behavior change, dependency bumps, documentation-only changes) may be exempted at the reviewer's discretion.

## Enforcement

This policy is enforced through:
1. CI pipeline (automated test execution + coverage thresholds)
2. Code review process (PR checklist in CONTRIBUTING.md)
3. CODEOWNERS approval requirements

## References

- `CONTRIBUTING.md` — Contribution guidelines with PR checklist
- `.github/workflows/backend.yml` — Backend CI with coverage enforcement
- `.github/workflows/chatbot.yml` — Chatbot CI with coverage enforcement
- `.github/workflows/frontend.yml` — Frontend CI
- `.github/workflows/e2e.yml` — E2E test workflow
