# SafeVixAI — Runbook: Post-Deploy Smoke Tests

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** Standard procedure  
**When:** After every production deployment  
**Last Updated:** 2026-05-18

---

## Purpose
Validate that a deployment did not break critical user journeys before declaring it healthy.

## Automated Checks (CI — run automatically on deploy)
These are triggered by the GitHub Actions workflow on push to `main`:
- Backend: `pytest tests/ -v --tb=short`
- Chatbot: `pytest tests/ -v --tb=short`
- Frontend: `npm run build` (TypeScript + lint checks)

## Manual Smoke Tests (< 5 min total)

Run these after every Render/Vercel deployment:

### 1. Health Checks
```bash
curl https://safevixai-backend.onrender.com/health
# Expected: {"status": "ok", "database_available": true}

curl https://safevixai-chatbot.onrender.com/health
# Expected: {"status": "ok", "memory_available": true}
```

### 2. Emergency Locator (core feature)
```bash
curl "https://safevixai-backend.onrender.com/api/v1/emergency/nearby?lat=13.0827&lon=80.2707"
# Expected: {"services": [...], "count": N, "source": "..."}
```

### 3. Chatbot (agentic RAG)
```bash
curl -X POST https://safevixai-chatbot.onrender.com/api/v1/chat/ \
  -H 'Content-Type: application/json' \
  -d '{"message": "What is the speed limit on NH44?", "session_id": "smoke-test"}'
# Expected: {"response": "...", "intent": "...", "sources": [...]}
```

### 4. Frontend
- Open https://safevixai.vercel.app
- Check map loads with tiles visible
- Verify SOS button is present on the home screen

## On Failure
- Immediately initiate rollback → see deployment-rollback.md
- Do NOT leave a broken deployment live for more than 5 minutes

## RTO: Rollback within 10 minutes of detecting failure
