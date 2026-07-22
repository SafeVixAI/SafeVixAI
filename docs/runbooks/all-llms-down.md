# SafeVixAI — Runbook: All LLM Providers Down

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** P1  
**Service:** Chatbot  
**Last Updated:** 2026-06-09

---

## Symptoms
- Chat endpoint returns `{"detail": "All LLM providers exhausted"}` or 503
- All 9+ providers are circuit-broken simultaneously
- Alert email: "LLM provider failure: all providers exhausted"

## Provider Fallback Chain (Groq → Cerebras → Gemini → GitHub Models → NVIDIA NIM → OpenRouter → Mistral → Together → Template)

The system has a **10-provider fallback chain** + a **template provider** of last resort that returns a static message. Complete failure (all providers + template returning errors) should not occur in normal operation.

## Immediate Response

1. **Check provider statuses:**
   ```
   GET /admin/providers/health   [X-Admin-Key: $ADMIN_SECRET]
   ```
   Identify which providers have `"status": "disabled"` (circuit breaker open)

2. **Check individual provider dashboards:**
   - Groq: https://console.groq.com
   - Gemini: https://ai.google.dev/status
   - Cerebras: https://cerebras.ai/status
   - Gemini: https://ai.google.dev/status
   - GitHub Models: https://github.com/marketplace/models
   - NVIDIA NIM: https://www.nvidia.com/en-us/ai/
   - OpenRouter: https://openrouter.ai
   - Mistral: https://mistral.ai
   - Together: https://together.ai

3. **Reset circuit breakers** (if provider is actually healthy):
   ```
   POST /admin/rebuild-index   [X-Admin-Key: $ADMIN_SECRET]
   ```
   *(This restarts the provider router, resetting cooldowns)*

4. **Rotate API keys** if a provider returns 401/403:
   - Update the relevant `*_API_KEY` env var in Render
   - Redeploy the chatbot service

## Recovery Validation
- `POST /api/v1/chat/` returns a valid response (not 503)
- `GET /admin/providers/health` shows at least 1 provider `"status": "healthy"`

## RTO: 30 minutes | RPO: N/A (stateless inference)
