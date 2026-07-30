# Code Review Guide

> Standards and expectations for code review in SafeVixAI.

---

## Principles

1. **Respectful and constructive** — Focus on the code, not the author.
2. **Timely** — First review within 24 hours on weekdays.
3. **Thorough** — Check for correctness, security, performance, accessibility, and maintainability.
4. **Proportionate** — Depth of review matches risk of change.

## Review Checklist

Every reviewer MUST verify these items before approving:

### Functional Correctness
- [ ] Does the code do what it claims?
- [ ] Are edge cases handled (empty states, errors, boundary conditions)?
- [ ] Do existing tests still pass?

### Security
- [ ] No hardcoded secrets, tokens, or credentials
- [ ] Input is validated, sanitized, or escaped as appropriate
- [ ] No new XSS vectors (user content rendered safely)
- [ ] Authentication/authorization checks in place for protected endpoints
- [ ] No unsafe `eval()`, `innerHTML`, `exec()`, or raw SQL concatenation
- [ ] Rate limiting considered for new public endpoints

### Performance
- [ ] No N+1 queries or inefficient loops
- [ ] Large payloads paginated or streamed
- [ ] Async operations have proper timeout handling
- [ ] Bundle size impact considered (frontend)

### Maintainability
- [ ] Code is readable and follows project conventions (see `CONTRIBUTING.md`)
- [ ] No dead code, commented-out code, or TODO comments without tracking
- [ ] Tests are added for new functionality (see `TESTING_POLICY.md`)
- [ ] Error handling is appropriate (not silently swallowed, not overly broad)

### Frontend-Specific
- [ ] Accessibility: aria attributes, keyboard navigation, focus management
- [ ] Responsive: works on mobile (375px) through desktop (1440px+)
- [ ] Loading states, error states, empty states handled
- [ ] Component follows existing patterns (see existing components in `components/`)
- [ ] No Framer Motion (use GSAP via `useGSAP` hook)

### Backend/Chatbot-Specific
- [ ] API endpoints follow RESTful conventions from existing routes
- [ ] Pydantic schemas used for request/response validation
- [ ] Database queries use async SQLAlchemy session properly
- [ ] Alembic migration included for schema changes
- [ ] LLM provider calls have timeout + fallback handling (chatbot)

## Review Process

1. **Author** opens PR with descriptive title and body explaining the change
2. **Reviewer(s)** are auto-assigned via CODEOWNERS
3. **Review** happens on the GitHub PR — inline comments, suggestions, or approval
4. **Author** addresses feedback by pushing new commits (no force-push on shared branches)
5. **Reviewer** re-reviews and approves, or requests further changes
6. **Merge** — Squash-merge with descriptive commit message following conventional commits

## Two-Person Review Rule

For Gold-tier compliance: at least **50% of all proposed modifications** MUST be reviewed by at least one person other than the author before merging. This is tracked via GitHub PR review history.

### Exemptions
- Emergency hotfixes (documented with `hotfix/` branch prefix)
- Trivial changes (typos, formatting, dependency bumps)
- Documentation-only changes
- Automated dependency updates by Dependabot

## Reviewer Assignment

| Area | Reviewer |
|------|----------|
| Backend (`backend/`) | Backend Core Contributors |
| Chatbot (`chatbot_service/`) | Chatbot Core Contributors |
| Frontend (`frontend/`) | Frontend Core Contributors |
| Infrastructure (`terraform/`, `k8s/`, `.github/`) | Infra Core Contributors |
| Security (`SECURITY.md`, auth, crypto) | Security Team + relevant area reviewer |
| Cross-cutting changes | 2 reviewers from affected areas |

## Auto-Review Tools

The following tools run automatically on every PR and may block merge:
- CodeQL — SAST for Python and JavaScript/TypeScript
- Ruff (Python) — linter and formatter check
- ESLint (TypeScript) — linter
- TypeScript type-check — `npx tsc --noEmit`
- Dependency review — supply chain attack detection
- Gitleaks — secret scanning
- Trivy — container vulnerability scanning

These tools supplement human review but do not replace it.

## Related Documents

- `CONTRIBUTING.md` — Contribution guidelines and code standards
- `TESTING_POLICY.md` — Testing requirements
- `SECURITY.md` — Security policy and vulnerability reporting
