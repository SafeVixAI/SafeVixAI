# Developer Experience Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [SETUP.md](SETUP.md), [STYLE_GUIDE.md](STYLE_GUIDE.md), [TESTING_POLICY.md](TESTING_POLICY.md)

---

## VS Code Setup

### Recommended Extensions
- **Python** (ms-python.python) — IntelliSense, linting, debugging
- **Pylance** (ms-python.vscode-pylance) — Fast type checking
- **Ruff** (charliermarsh.ruff) — Python linting/formatting
- **ESLint** (dbaeumer.vscode-eslint) — TypeScript/JavaScript linting
- **Prettier** (esbenp.prettier-vscode) — Code formatter
- **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss) — Tailwind class completion
- **GitLens** (eamodio.gitlens) — Git blame, history, annotations
- **Jest** (orta.vscode-jest) — Inline test results
- **Docker** (ms-azuretools.vscode-docker) — Docker management
- **YAML** (redhat.vscode-yaml) — YAML validation

### Workspace Settings (`settings.json`)
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "python.terminal.activateEnvironment": true,
  "python.testing.pytestEnabled": true,
  "python.testing.cwd": "${workspaceFolder}/backend",
  "jest.runMode": "on-demand"
}
```

### Debug Configurations (`launch.json`)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "env": { "PYTHONPATH": "${workspaceFolder}/backend" }
    },
    {
      "name": "Chatbot",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--port", "8010"],
      "cwd": "${workspaceFolder}/chatbot_service"
    },
    {
      "name": "Frontend",
      "type": "node",
      "request": "launch",
      "command": "npm run dev",
      "cwd": "${workspaceFolder}/frontend"
    },
    {
      "name": "Backend Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Tasks (`tasks.json`)
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start All Services",
      "dependsOn": ["Backend", "Chatbot", "Frontend"],
      "runOptions": { "runOn": "default" }
    },
    {
      "label": "Backend",
      "type": "shell",
      "command": ".venv/Scripts/activate; uvicorn main:app --reload --port 8000",
      "options": { "cwd": "${workspaceFolder}/backend" }
    },
    {
      "label": "Run All Tests",
      "dependsOn": ["Backend Tests", "Frontend Tests", "Chatbot Tests"]
    }
  ]
}
```

---

## Debugging

### Backend
- Set breakpoints in VS Code and use the "Backend" debug configuration
- FastAPI auto-reload restarts the server on file changes
- Check server logs for `INFO` level request details

### Chatbot Service
- LLM provider responses are logged at `DEBUG` level
- Enable debug logging: `export LOG_LEVEL=DEBUG`
- Test individual providers: `python -c "from providers.router import test_provider; print(test_provider('groq'))"`

### Frontend
- **React DevTools**: Component tree, props, state, hooks
- **Redux DevTools**: Zustand state changes (Zustand supports Redux DevTools)
- **Network tab**: API request/response inspection
- **Application tab**: IndexedDB, Service Worker, Cache storage

---

## Hot Reload

| Service | How it works | Notes |
|---------|-------------|-------|
| Backend | Uvicorn `--reload` flag | Auto-restarts on `.py` change |
| Chatbot | Uvicorn `--reload` flag | Auto-restarts on `.py` change |
| Frontend | Next.js Fast Refresh | Preserves state across React component edits |

---

## Database Migrations During Development

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# View history
alembic history

# View current
alembic current
```

---

## Seed Data

```bash
# City centers for routing
cd backend && python scripts/data/seed_city_centers.py

# Emergency services (requires DB)
cd backend && python scripts/app/seed_emergency.py

# Hospitals from NHP
cd backend && python scripts/app/seed_nhp_hospitals.py

# ChromaDB vectorstore (requires PDFs)
cd chatbot_service && python data/build_vectorstore.py
```

---

## Testing Workflows

```bash
# Run specific backend test
cd backend && pytest tests/test_challan.py -v

# Run with coverage
cd backend && pytest tests/ -v --cov --cov-report=term-missing

# Run frontend tests with watch mode
cd frontend && npm test -- --watch

# Run specific frontend test file
cd frontend && npx jest tests/sos.test.tsx

# Run lint only
cd frontend && npm run lint
```

### CI Simulation Locally
```bash
# Pre-commit checks
pip install pre-commit
pre-commit run --all-files

# Full CI pipeline (requires Docker)
# See .github/workflows/ for individual workflow commands
```

---

## Performance Profiling

### Backend
```bash
# Profile a single test
cd backend && pytest tests/test_challan.py --profile
```

### Frontend
- **Lighthouse**: `npx lighthouse http://localhost:3000 --view`
- **Bundle Analyzer**: `ANALYZE=true npm run build`
- **React Profiler**: React DevTools → Profiler tab

### Database
```bash
# Enable query logging
echo "ALTER DATABASE safevixai SET log_statement = 'all';" | psql -h localhost
```

---

## API Testing

### Bruno Collection
An API testing collection for [Bruno](https://www.usebruno.com/) is available at `docs/api/bruno-collection.json`.

### cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Emergency services
curl "http://localhost:8000/api/v1/emergency/nearby?lat=13.0827&lon=80.2707"

# Chatbot
curl -X POST http://localhost:8010/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the fine for speeding?"}'
```

---

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

The pre-commit configuration runs:
1. **ruff** — Python linting and formatting
2. **eslint** — TypeScript/JavaScript linting
3. **gitleaks** — Secret detection
4. **trailing-whitespace** — Clean up whitespace
5. **end-of-file-fixer** — Ensure files end with newline

---

## Troubleshooting Development Issues

See [TROUBLESHOOTING.md](../sre/TROUBLESHOOTING.md) for detailed issue resolution.

Common issues:
- **Virtual environment not activated** — Run `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
- **Port already in use** — Kill the existing process or change the port
- **Database connection refused** — Start PostgreSQL or check `DATABASE_URL`
- **Node.js version mismatch** — Use `nvm use 20` or install Node.js 20+
