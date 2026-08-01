# Contributors Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [CONTRIBUTING.md](Contributing.md), [SETUP.md](SETUP.md), [STYLE_GUIDE.md](STYLE_GUIDE.md), [TESTING_POLICY.md](TESTING_POLICY.md)

---

## Project Overview

SafeVixAI is a three-service monorepo:
- **backend/**: FastAPI Python API (emergency, challan, SOS, reports, civic intel)
- **chatbot_service/**: FastAPI Python service (AI chatbot with 10 LLM providers)
- **frontend/**: Next.js + React PWA (maps, SOS, chatbot UI, offline support)

See [Architecture.md](chatbot/architecture.md) for system architecture and data flows.

---

## Development Workflow

### 1. Find an Issue
- **Good First Issues**: Tagged `good first issue` — small scope, mentor available
- **Help Wanted**: Tagged `help wanted` — any skill level
- **Feature Requests**: Tagged `enhancement` — discuss before implementing
- **Bugs**: Tagged `bug` — clear reproduction steps

Comment on the issue to express interest and ask questions.

### 2. Set Up Your Environment
```bash
git clone https://github.com/SafeVixAI/SafeVixAI.git
cd SafeVixAI

# Backend
cd backend && python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Chatbot
cd ../chatbot_service && python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Frontend
cd ../frontend && npm ci
cp .env.local.example .env.local
```

See [SETUP.md](SETUP.md) for detailed setup instructions.

### 3. Create a Branch
```bash
git checkout -b feature/42-add-sos-cancel
```
Branch naming: `feature/<issue>-<description>`, `fix/<issue>-<description>`, `docs/<description>`, `test/<description>`, `chore/<description>`

### 4. Make Changes

**For Python changes (backend/chatbot):**
- Follow PEP 8, Black (88 chars), Ruff linting
- Add type hints to all public functions
- Use Google-style docstrings for new functions/classes

**For TypeScript/React changes (frontend):**
- Follow ESLint + Prettier config
- Use functional components with hooks
- Add `'use client'` for interactive components
- Use Tailwind CSS (no inline styles)
- Use Lucide icons

See [STYLE_GUIDE.md](STYLE_GUIDE.md) for detailed coding standards.

### 5. Write Tests

| Service | Framework | Coverage Target |
|---------|-----------|-----------------|
| Backend | pytest (asyncio_mode=auto) | 100% lines/branches |
| Chatbot | pytest (asyncio_mode=strict) | 97%+ lines |
| Frontend | Jest + React Testing Library | 86% lines, 72% branches |

**Test patterns:**
```python
# Backend test
async def test_emergency_nearby(client, db_session):
    response = await client.get("/api/v1/emergency/nearby?lat=13.08&lon=80.27")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
```

```typescript
// Frontend test
it('renders SOS button', () => {
  render(<SosButton onActivate={jest.fn()} />);
  expect(screen.getByRole('button', { name: /activate sos/i })).toBeInTheDocument();
});
```

### 6. Run Lint + Tests
```bash
# Backend
cd backend && ruff check . && pytest tests/ -v

# Chatbot
cd chatbot_service && ruff check . && pytest tests/ -v

# Frontend
cd frontend && npm run lint && npm test && npx tsc --noEmit
```

### 7. Commit
```bash
git add .
git commit -m "feat(backend): add SOS cancel endpoint"
```
Use Conventional Commits: `type(scope): description`

See [STYLE_GUIDE.md](STYLE_GUIDE.md#commit-conventions) for commit types and scopes.

### 8. Push and Create PR
```bash
git push origin feature/42-add-sos-cancel
```
Open a pull request on GitHub with:
- Clear description of changes
- Reference to the issue (Closes #42)
- Screenshots for UI changes
- Test results summary

### 9. Code Review
- A maintainer will review your PR
- Address feedback with additional commits
- Once approved, your PR will be squash-merged

---

## Codebase Navigation

### Backend (`backend/`)
| Directory | Contents |
|-----------|----------|
| `api/v1/` | 25 FastAPI route modules (endpoints) |
| `core/` | Config, database, Redis, security, CQRS, caching |
| `services/` | 16 domain services (challan, emergency, routing, etc.) |
| `models/` | 20 SQLAlchemy ORM models + Pydantic schemas |
| `migrations/` | Alembic migration files |

### Chatbot (`chatbot_service/`)
| Directory | Contents |
|-----------|----------|
| `agent/` | ChatEngine, IntentDetector, SafetyChecker |
| `providers/` | 9 LLM providers + routing + language detection |
| `rag/` | ChromaDB vector store, retriever, embeddings |
| `tools/` | 13 agent tools (SOS, Challan, Legal, FirstAid, etc.) |
| `memory/` | Redis conversation memory |

### Frontend (`frontend/`)
| Directory | Contents |
|-----------|----------|
| `app/` | 28 Next.js routes (pages) |
| `components/` | 91 React components (maps, chat, SOS, etc.) |
| `lib/` | 28 modules (API client, state, offline AI, tracking) |
| `tests/` | Jest test suites |

---

## Issue Triage

| Label | Meaning | Action |
|-------|---------|--------|
| `bug` | Confirmed bug | Reproduce, fix, add regression test |
| `enhancement` | Feature request | Discuss, scope, implement |
| `good first issue` | Beginner-friendly | Mentor available |
| `help wanted` | Needs contributor | Pick up if interested |
| `needs-reproduction` | Unconfirmed | Try to reproduce |
| `blocked` | Waiting on dependency | Check status |

---

## Performance Considerations

- **Database**: Add indexes for new query patterns
- **API**: Use cursor pagination for list endpoints
- **Frontend**: Lazy load heavy components (MapLibre, WebLLM)
- **Chatbot**: Keep tool responses concise to reduce LLM token usage
- **Build**: Monitor bundle size with `ANALYZE=true npm run build`

---

## Security Considerations

- **Never commit secrets** — gitleaks pre-commit hook checks for this
- **Validate all inputs** — use Pydantic/Zod schemas at API boundaries
- **Sanitize outputs** — escape user-generated content
- **Rate limits** — apply to new endpoints
- **Prompt injection** — run through SafetyChecker for chatbot changes

---

## Documentation Contributions

- Keep docs close to code (docstrings, JSDoc, README)
- Update existing docs when changing behavior
- Add examples for new API endpoints
- Run `mkdocs serve` to preview documentation site

---

## Getting Help

- Comment on your issue or PR — a mentor will respond
- Join [GitHub Discussions](https://github.com/SafeVixAI/SafeVixAI/discussions)
- Email `safevixai@googlegroups.com` for project-level questions
- See [SUPPORT.md](../../SUPPORT.md) for all support channels
