# New Contributor Guide

> Welcome! Here's how to make your first contribution to SafeVixAI.

---

## Quick Start

```bash
git clone https://github.com/safevixai/safevixai.git
cd safevixai
make setup
```

See [`SETUP.md`](SETUP.md) for detailed environment setup instructions.

## Finding Your First Task

We label issues by difficulty to help you find something that matches your skill level:

| Label | Description | Example |
|-------|-------------|---------|
| `good first issue` | Well-scoped, minimal codebase familiarity needed | Fix a typo, add a test, improve error message |
| `help wanted` | Moderate effort, some domain knowledge needed | Add a new API endpoint, create a UI component |
| `backend` | Python / FastAPI / PostgreSQL | Write a query, add a validation rule |
| `frontend` | TypeScript / React / Next.js | Style a component, add a form field |
| `chatbot` | Python / LLMs / RAG | Add a new tool, improve prompt |
| `docs` | Documentation improvements | Fix a broken link, add code example |
| `test` | Testing improvements | Add unit tests, improve coverage |

### Good First Issues

Look for issues tagged with `good first issue` in the [issue tracker](https://github.com/SafeVixAI/SafeVixAI/issues). These typically involve:

- **Documentation:** Fix a broken link, clarify an instruction, add a missing example
- **Testing:** Add a unit test for an uncovered function or edge case
- **Bug fixes:** Simple, well-scoped bugs with reproduction steps
- **UI polish:** Improve an error message, add a loading state, fix a spacing issue
- **Dependencies:** Update a pinned dependency, resolve a Dependabot alert

### 15-Minute Tasks

- [ ] Add a docstring to an undocumented function
- [ ] Add type hints to a Python function
- [ ] Fix a lint warning in a file
- [ ] Improve an error message to be more descriptive
- [ ] Add a test for an edge case

### 1-Hour Tasks

- [ ] Implement a new test suite for an existing module
- [ ] Add a new Pydantic validator for an API input
- [ ] Create a new UI component following existing patterns
- [ ] Write or update API documentation for an endpoint

## Making Changes

1. **Find or create an issue** — Comment on it to express interest.
2. **Fork and branch** — Create a branch from `main`: `git checkout -b feat/my-change`.
3. **Make your change** — Follow the code standards in `CONTRIBUTING.md`.
4. **Add tests** — See `TESTING_POLICY.md` for requirements.
5. **Commit with DCO** — Use `git commit -s` to add the Signed-off-by trailer.
6. **Push and open a PR** — Reference the issue number in the PR description.
7. **Respond to review** — Address reviewer feedback with additional commits.

## Getting Help

- **Issue comments** — Ask questions directly on the relevant issue.
- **GitHub Discussions** — Use [Discussions](https://github.com/SafeVixAI/SafeVixAI/discussions) for general questions.
- **Code review** — Reviewers will provide specific guidance on your PR.

## Service Overview

```
SafeVixAI/
├── backend/           FastAPI + PostgreSQL (port 8000)
├── chatbot_service/   FastAPI + LLM providers (port 8010)
├── frontend/          Next.js 15 PWA (port 3000)
├── scripts/           Data pipeline / tooling
├── docs/              Documentation
└── .github/           CI/CD + governance
```

Pick the service that matches your interest:
- **Backend:** Python, PostgreSQL, GIS — good for systems programmers
- **Chatbot:** Python, LLMs, RAG — good for AI/ML enthusiasts
- **Frontend:** TypeScript, React, maps — good for UI developers
- **Infra:** Docker, Terraform, CI/CD — good for DevOps

## Community

- **Code of Conduct:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **Governance:** [GOVERNANCE.md](GOVERNANCE.md)
- **Roadmap:** [ROADMAP.md](ROADMAP.md)
- **Discussions:** [GitHub Discussions](https://github.com/SafeVixAI/SafeVixAI/discussions)

We're glad you're here!
