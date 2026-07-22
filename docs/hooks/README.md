# Git Hooks

This directory contains custom Git hooks for SafeVixAI repository automation.

## Contents

Pre-commit hooks, commit-msg hooks, and other lifecycle scripts that enforce:
- Code quality checks (linting, formatting)
- Commit message conventions
- Pre-push validation

## Related

The project also uses a `.pre-commit-config.yaml` at the repository root for pre-commit framework integration, covering ruff (backend/chatbot) and eslint (frontend).
