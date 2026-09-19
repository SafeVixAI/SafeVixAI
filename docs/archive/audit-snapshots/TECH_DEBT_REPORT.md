# SafeVixAI â€" Technical Debt Report

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

**Date:** 2026-05-19  
**Scope:** Code quality, outdated patterns, unused dependencies, architectural compromises  
**Auditor:** Staff Engineer

---

## HIGH Technical Debt

### 1. `sys.path.insert` Anti-Pattern
**Estimated Cost:** 2 hours  
**Files:** `backend/main.py`, `chatbot_service/providers/router.py`

**Problem:** `sys.path.insert(0, ...)` used to import `alert_service` from project root. Fragile, breaks in containerized deployments.

**Risk:** Deployment failures, import errors in production.

**Fix:** Move `alert_service.py` into `backend/services/` or use `PYTHONPATH`.

---

### 2. Duplicate Chat Implementations
**Estimated Cost:** 4 hours  
**Files:** `components/ChatInterface.tsx`, `app/assistant/page.tsx`

**Problem:** Two separate chat implementations with duplicated streaming logic.

**Risk:** Maintenance nightmare, divergence over time.

**Fix:** Extract shared `useChatStream` hook and `ChatMessageList` component.

---

### 3. Service Injection via `app.state`
**Estimated Cost:** 8 hours  
**Scope:** Both FastAPI services

**Problem:** Services stored on `app.state`, not using FastAPI's dependency injection.

**Risk:** Harder to test, implicit dependencies.

**Fix:** Migrate to FastAPI `Depends()` pattern.

---

## MEDIUM Technical Debt

### 4. Orphaned Dependencies
**Estimated Cost:** 1 hour  
**File:** `frontend/package.json`

**Problem:** `framer-motion` in `package-lock.json` but no source imports.

**Fix:** Run `npm uninstall framer-motion`.

### 5. Multiple Dockerfiles for Frontend
**Estimated Cost:** 30 minutes  
**Files:** `frontend/Dockerfile`, `frontend/Dockerfile.frontend`

**Problem:** Two Dockerfiles for same service. Confusing which one to use.

**Fix:** Consolidate to single Dockerfile.

### 6. Config Pattern Inconsistency
**Estimated Cost:** 2 hours  
**Scope:** Backend vs Chatbot

**Problem:** Backend uses `pydantic-settings`, chatbot uses `dataclass` + `os.getenv()`.

**Fix:** Standardize on `pydantic-settings` for both.

---

## LOW Technical Debt

### 7. Root-Level Scripts
**Estimated Cost:** 4 hours  
**Scope:** `alert_service.py`, `safevixai_verify.py`, `patch.py`, `fix_ui.js`

**Problem:** Root-level scripts should be in dedicated directories.

**Fix:** Move to `scripts/` or `tools/` directory.

### 8. Duplicate Documentation
**Estimated Cost:** 2 hours  
**Scope:** `docs/` vs `chatbot_docs/`

**Problem:** Similar docs in two locations.

**Fix:** Consolidate to single docs directory.

---

## Technical Debt Score Summary

| Area | Score | Grade |
|------|-------|-------|
| Code Quality | 7/10 | B- |
| Dependencies | 6/10 | C+ |
| Architecture | 7/10 | B- |
| Documentation | 6/10 | C+ |
| **Overall** | **7.0/10** | **B-** |
