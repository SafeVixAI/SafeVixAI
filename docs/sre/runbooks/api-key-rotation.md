# Runbook: API Key Rotation

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** SEV2 | **Service:** All | **Time to execute:** 15 minutes

## When to rotate
- Key exposed in logs or commits
- Key compromised or suspected leak
- Scheduled rotation (quarterly)
- Team member departure

## Steps

### 1. Generate new key
- Go to provider dashboard (Groq, Gemini, etc.)
- Create new API key
- Copy to secure location

### 2. Update environment variables
```bash
# backend/.env
GROQ_API_KEY=new_key_here
GEMINI_API_KEY=new_key_here

# chatbot_service/.env
GROQ_API_KEY=new_key_here
GEMINI_API_KEY=new_key_here

# Update Render environment variables
# Render dashboard → Environment → update key → Save
```

### 3. Redeploy affected services
```bash
# Render auto-deploys on env var change
# Or trigger manual deploy from dashboard
```

### 4. Verify services
```bash
curl http://localhost:8000/health
curl http://localhost:8010/health
# Test chat endpoint with a simple query
```

### 5. Revoke old key
- Go to provider dashboard
- Delete/revoke the old key
- Verify no services are using it

### 6. Update documentation
- Update `.env.example` if key format changed
- Update any runbooks referencing the key

## Emergency rotation (compromised key)
1. Revoke old key immediately
2. Generate new key
3. Update env vars and redeploy
4. Verify all services functional
