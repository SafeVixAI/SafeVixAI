# Style Guide

## Code Style

### Python (Backend + Chatbot)
- **Formatter**: Ruff with `--format` (double quotes, line length 100)
- **Lint**: Ruff with rulesets E, F, I, N, W, UP, B, SIM, ARG, C4, EM, G, PIE, T20
- **Type hints**: Required for all function signatures (Python 3.11+)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Imports**: Grouped as stdlib → third-party → local, sorted by Ruff (I rule)
- **Tests**: pytest with `asyncio_mode = auto` (backend) or `strict` (chatbot)

Configuration: `backend/pyproject.toml`, `chatbot_service/pyproject.toml`, `ruff.toml`

### TypeScript/JavaScript (Frontend)
- **Formatter**: Prettier (see `.prettierrc`, `.prettierignore`)
- **Lint**: ESLint with Next.js config (`next lint`), see `.eslintrc.json`
- **TypeScript**: Strict mode enabled in `tsconfig.json`
- **Naming**: `camelCase` for functions/variables, `PascalCase` for components/types
- **Components**: React 19 functional components with TypeScript
- **Imports**: Grouped as React → next → third-party → local (`@/`)

## Documentation Style
- **Markdown**: GitHub-Flavored Markdown with SPDX license header on all files
- **Headers**: ATX-style (`#`), with space after `#`
- **Code blocks**: Fenced with language identifier
- **ADRs**: Architecture Decision Records in `docs/adr/` using standard template
- **Runbooks**: Located in `docs/runbooks/` with severity, symptoms, diagnosis, resolution

## Commit Style
- **Format**: `type(scope): description` — e.g., `fix(backend): correct haversine import`
- **Types**: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `ci`, `style`
- **Scopes**: `backend`, `frontend`, `chatbot`, `infra`, `docs`
- **Body**: Wrap at 72 characters, reference issues with `#NNN`
- **Sign-off**: All commits must include `Signed-off-by:` (see [DCO](DCO))

## Release Style
- **Versioning**: Semantic Versioning 2.0.0 (see [VERSIONING.md](VERSIONING.md))
- **Changelog**: Keep a Changelog format (see [CHANGELOG.md](CHANGELOG.md))
- **Tags**: `vMAJOR.MINOR.PATCH` — e.g., `v1.0.0`

## Infrastructure Style
- **Docker**: Multi-stage builds, non-root user, HEALTHCHECK, `.dockerignore`
- **Terraform**: HCL with consistent naming (`snake_case`), modules in `terraform/`
- **K8s**: Kustomize overlays in `k8s/`, resource quotas, network policies
