# SafeVixAI - Contributing Guide

How the team works together on this project.

---

## Before You Start

1. Read `AGENTS.md` - agent quick-reference
2. Read `docs/Agent.md` - complete app overview
3. Read `docs/Architecture.md` - understand the system design
4. Read `docs/API.md` - all endpoints with request/response examples
5. Read `docs/Database.md` - all 7 tables with PostGIS column definitions
6. Read `docs/AI_Instructions.md` - how each AI layer works
7. Read `SETUP.md` - step-by-step local setup with exact commands
8. Read `docs/Deployment.md` - deploy to Vercel/Render/Supabase

---

## Branch Strategy

We use a simple feature branch workflow:

```
main
  |-- feature/emergency-api
  |-- feature/chat-ui
  |-- feature/offline-challan
  |-- fix/map-not-loading
  |-- fix/encoding-issue
```

### Rules

- **Never commit directly to `main`**
- Create a new branch for every feature or fix
- Branch name format: `feature/short-description` or `fix/short-description`
- Open a Pull Request to merge into `main`
- At least one teammate reviews before merging

### Daily Workflow

```bash
# 1. Always pull latest main before starting
git checkout main
git pull origin main

# 2. Create your feature branch
git checkout -b feature/emergency-api

# 3. Make your changes and commit often
git add .
git commit -m "feat: add PostGIS ST_DWithin query for nearby hospitals"

# 4. Push your branch
git push origin feature/emergency-api

# 5. Open a Pull Request on GitHub
# 6. After review, merge to main and delete the branch
```

---

## Commit Message Format

Use this format for all commits:

```
type: short description of what changed
```

Types:
| Type | When to use |
|---|---|
| `feat` | New feature or endpoint |
| `fix` | Bug fix |
| `docs` | Documentation changes only |
| `refactor` | Code reorganization, no behavior change |
| `test` | Adding or updating tests |
| `chore` | Config, deps, tooling changes |
| `style` | CSS or formatting only |

Examples:
```bash
git commit -m "feat: add challan calculator API with DuckDB SQL"
git commit -m "fix: maplibre map not rendering on SSR"
git commit -m "docs: update API.md with new road reporter endpoints"
git commit -m "test: add pytest for emergency nearby endpoint"
```

---

## Who Works on What

Assign yourself to a module to avoid conflicts:

| Module | Backend file | Frontend file |
|---|---|---|
| Emergency Locator | api/v1/emergency.py | app/emergency/page.tsx |
| AI Chatbot | api/v1/chat.py | app/assistant/page.tsx |
| Challan Calculator | api/v1/challan.py | app/challan/page.tsx |
| Road Reporter | api/v1/roadwatch.py | app/report/page.tsx |

Shared files (coordinate before editing):
- `backend/main.py`
- `backend/core/database.py`
- `frontend/app/layout.tsx`
- `frontend/lib/store.ts`

---

## Code Style

### Backend (Python)

- Follow PEP 8
- Use `async def` for all route handlers and DB calls
- Use Pydantic models for all request and response bodies
- Add docstring to every function
- Use type hints everywhere

```python
# Good
async def get_nearby_services(
    lat: float,
    lon: float,
    radius: int = 5000,
    db: AsyncSession = Depends(get_db)
) -> EmergencyResponse:
    """Return emergency services within radius meters of lat/lon."""
    ...

# Bad
def getNearby(lat, lon):
    ...
```

### Frontend (TypeScript)

- Use TypeScript strict mode - no `any` types
- Use `const` over `let`, never `var`
- One component per file
- Component files: PascalCase (EmergencyMap.tsx)
- Utility files: camelCase (store.ts, api.ts)
- Use SWR for all API calls - no raw fetch in components

```typescript
// Good
const { data, error, isLoading } = useSWR<EmergencyResponse>(
  `/api/v1/emergency/nearby?lat=${lat}&lon=${lon}`,
  fetcher
)

// Bad
const [data, setData] = useState(null)
useEffect(() => { fetch(...).then(setData) }, [])
```

---

## Testing Requirements

- Every new backend endpoint needs at least one test in `backend/tests/`
- Run tests before opening a PR:

```bash
# Backend
cd backend && .venv\Scripts\activate && pytest tests/ -q

# Chatbot Service
cd chatbot_service && .venv\Scripts\activate && pytest tests/ -q

# Frontend
cd frontend && npm test && npm run lint
```

Do not open a PR if tests are failing.

---

## Pull Request Checklist

Before opening a PR, confirm:

- [ ] Tests pass locally
- [ ] No lint errors
- [ ] Works offline (for frontend features)
- [ ] No hardcoded API keys or secrets
- [ ] `.env` values are in `.env.example` with placeholder values
- [ ] Added comments to non-obvious code
- [ ] PR description explains what changed and why

---

## Environment Variables

- Never commit `.env` or `.env.local` files (both are in .gitignore)
- If you add a new env variable, add it to `.env.example` with a placeholder
- Tell teammates in the group chat when you add a new required variable

---

## Asking for Help

- Create a GitHub Issue for bugs you find but cannot fix right now
- Use Issue labels: `bug`, `enhancement`, `question`, `blocked`
- Tag teammates in Issues and PRs using @username

---

*SafeVixAI | AI-powered road safety platform*

## Related

- [TESTING.md](../TESTING.md) — Testing standards and coverage
- [STYLE_GUIDE.md](../STYLE_GUIDE.md) — Coding style conventions
- [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) — Contributor Covenant
- [docs/DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Developer onboarding and workflow
