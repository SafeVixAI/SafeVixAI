# CLI Reference

> Version 1.0.0 | Last updated: 2026-07-25

All commands are run from the repository root. The Makefile provides the primary development interface. Windows users should use WSL, Git Bash, or Docker for Makefile commands.

## Development Commands

| Command | Description | Notes |
|---------|-------------|-------|
| `make setup` | Install all dependencies + copy .env templates | Runs pip install in backend + chatbot_service, npm ci in frontend |
| `make test` | Run all tests (3 services) | Short traceback, no coverage |
| `make test-backend` | Run backend tests only | `pytest tests/ -v --tb=short -q` |
| `make test-chatbot` | Run chatbot_service tests only | `pytest tests/ -v --tb=short -q` |
| `make test-frontend` | Run frontend Jest tests | `npm test -- --watchAll=false --no-coverage` |
| `make lint` | Lint all code | ruff for Python, ESLint for frontend |
| `make typecheck` | TypeScript type-check | `npx tsc --noEmit` |
| `make build` | Build frontend production bundle | `npm run build` |

### Backend (uvicorn)

```bash
cd backend
uvicorn main:app --reload --port 8000          # Dev with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000    # Production
```

### Chatbot Service (uvicorn)

```bash
cd chatbot_service
uvicorn main:app --reload --port 8010          # Dev with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8010    # Production
```

### Frontend (Next.js)

```bash
cd frontend
npm run dev                        # Dev server (hot reload)
npm run build && npm start         # Production build (SW active)
npx tsc --noEmit                   # TypeScript check
npm run lint                       # ESLint
```

## Testing

### Backend (pytest — asyncio_mode=auto)

| Command | Description |
|---------|-------------|
| `pytest tests/ -v` | All tests verbose |
| `pytest tests/test_challan.py -v` | Single file |
| `pytest tests/ -k "sos"` | Keyword filter |
| `pytest tests/ --cov=services --cov-report=term-missing` | With coverage |
| `pytest tests/ -x --pdb` | Stop on first failure, debugger |
| `mutmut run --paths-to-infect core/` | Mutation testing |

### Chatbot Service (pytest — asyncio_mode=strict)

| Command | Description |
|---------|-------------|
| `pytest tests/ -v` | All tests |
| `pytest tests/test_providers.py -v` | Single file |
| `pytest tests/ -k "rag"` | Keyword filter |

### Frontend (Jest 30)

| Command | Description |
|---------|-------------|
| `npm test` | Watch mode |
| `npm test -- --watchAll=false` | Single run (CI) |
| `npm test -- --coverage` | With coverage report |
| `npm test -- --testPathPattern="sos"` | Pattern match |
| `npm test -- --verbose` | Verbose output |

### E2E (Playwright)

```bash
make e2e                              # Full suite (excl. visual regression)
cd frontend && npx playwright test e2e/            # All tests
npx playwright test e2e/ --headed                   # Visible browser
npx playwright show-report                          # View last report
```

## Alembic (Database Migrations)

```bash
cd backend
alembic revision --autogenerate -m "description"   # Create migration
alembic upgrade head                                # Apply all pending
alembic downgrade -1                                # Rollback one step
alembic history                                     # List history
alembic current                                     # Show current rev
```

## Docker

| Command | Description |
|---------|-------------|
| `make docker` | Build all images |
| `make docker-up` | Start all 5 services |
| `make docker-down` | Stop all containers |
| `make docker-prod` | Production overrides |
| `docker compose logs -f backend` | Tail backend logs |
| `docker compose ps` | List containers |
| `docker compose exec backend bash` | Shell into container |

Services: postgres (PostGIS 16-3.4), redis (7-alpine), backend, chatbot, frontend.

## AWS ECR

| Command | Description |
|---------|-------------|
| `make ecr-login` | Authenticate Docker to AWS ECR (ap-south-1) |
| `make ecr-build-push-backend` | Build + push backend image |
| `make ecr-build-push-chatbot` | Build + push chatbot image |
| `make ecr-build-push-frontend` | Build + push frontend image |
| `make ecr-build-push-all` | Build + push all 3 |

## Terraform

| Command | Description |
|---------|-------------|
| `make tf-fmt` | Format Terraform files |
| `make tf-validate` | Validate config |
| `make tf-plan` | Generate execution plan |
| `make tf-apply` | Apply the plan |
| `make tf-destroy` | Tear down all resources |

## Kubernetes

| Command | Description | Namespace |
|---------|-------------|-----------|
| `make k8s-apply` | Deploy all manifests | safevixai |
| `make k8s-delete` | Delete all resources | safevixai |
| `make k8s-status` | Pods, services, ingress, HPA | safevixai |
| `make k8s-logs` | Tail all pod logs | safevixai |
| `make k8s-rollout-backend` | Rolling restart backend | safevixai |
| `make k8s-rollout-chatbot` | Rolling restart chatbot | safevixai |
| `make k8s-rollout-frontend` | Rolling restart frontend | safevixai |

## Load Testing (k6)

| Command | Description |
|---------|-------------|
| `make k6-smoke` | Quick smoke test |
| `make k6-load` | Multi-scenario load test |
| `make k6-sustained` | 15-min sustained load |
| `make k6-spike` | Emergency endpoint spike |

## Quality & Security

| Command | Description |
|---------|-------------|
| `make e2e` | Playwright E2E tests |
| `make security-scan` | Gitleaks + Trivy scan |
| `make clean` | Clean build artifacts |
| `make deploy` | Full deploy (Terraform + K8s) |
