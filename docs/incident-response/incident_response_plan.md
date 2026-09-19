# SafeVixAI â€" Incident Response Plan

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

**Date:** 2026-05-18  
**Version:** 1.0  
**Owner:** SafeVixAI Engineering

---

## Purpose

This document defines how to detect, respond to, and learn from incidents affecting the SafeVixAI platform. Given the safety-critical nature of the system (SOS, emergency locator), incident response is treated with high urgency.

---

## Severity Levels

| Severity | Definition | Response Time | Examples |
|----------|-----------|---------------|---------|
| **P0 â€" Critical** | Safety-critical feature broken (SOS, emergency locator down) | Immediate (< 5 min) | SOS endpoint returning 5xx, emergency nearby broken |
| **P1 â€" High** | Core functionality degraded for all users | < 15 min | Auth broken, chatbot down, map not loading |
| **P2 â€" Medium** | Partial degradation (some users affected) | < 1 hour | Road report submission failing, one LLM provider down |
| **P3 â€" Low** | Minor degradation, no user impact | < 1 business day | Slow geocoding, bundle size regression |

---

## Incident Response Workflow

### 1. Detection
Incidents can be detected via:
- Automated health check failures (`/health` returning non-200)
- Alert emails from `alert_service.py`
- User reports via Project judges or team communication
- Render service status notifications

### 2. Triage (< 5 min)
1. **Determine severity** using the table above
2. **Notify team** on Discord/WhatsApp with: *"P[N] Incident: [brief description]. Investigating."*
3. **Assign incident commander** (person who detected it owns it until resolved)

### 3. Investigation (per runbooks)
Refer to the specific runbook for the affected component:

| Component | Runbook |
|-----------|---------|
| Database | `docs/runbooks/db-down.md` |
| Redis | `docs/runbooks/redis-down.md` |
| All LLMs | `docs/runbooks/all-llms-down.md` |
| High error rate | `docs/runbooks/high-error-rate.md` |
| Bad deployment | `docs/runbooks/deployment-rollback.md` |

### 4. Mitigation
Options in order of preference:
1. **Fix forward** â€" deploy a hotfix if root cause is clear and fix is < 30 min
2. **Rollback** â€" revert to previous working deployment (see deployment-rollback.md)
3. **Disable feature** â€" set feature flag / remove broken route temporarily
4. **Failover** â€" switch to backup provider / fallback mode

### 5. Recovery Validation
- Run smoke tests from `docs/runbooks/smoke-tests.md`
- Confirm error rate returns to normal (< 1% for 5 min)
- Notify team: *"P[N] Incident RESOLVED: [what was done]. Duration: [X min]."*

### 6. Post-Mortem (for P0/P1)
Must be completed within 24 hours of resolution:

**Post-Mortem Template:**
```
## Incident: [Short description]
**Date:** [YYYY-MM-DD]
**Duration:** [X minutes]
**Severity:** P[N]
**Services affected:** [Backend / Chatbot / Frontend]

## Timeline
- [HH:MM] - Incident detected
- [HH:MM] - Root cause identified
- [HH:MM] - Mitigation applied
- [HH:MM] - Recovery confirmed

## Root Cause
[What caused the incident?]

## Impact
[How many users were affected? What features were broken?]

## What Went Well
[What worked during the response?]

## What Could Be Improved
[What would have made detection/resolution faster?]

## Action Items
- [ ] [Action] â€" Owner â€" Due date
```

---

## Contact List (project team)

> Update this with actual team contacts before the demo.

| Role | Name | Contact |
|------|------|---------|
| Backend Lead | [Team Member] | [Contact] |
| Frontend Lead | [Team Member] | [Contact] |
| AI/Chatbot Lead | [Team Member] | [Contact] |
| Incident Commander (default) | First responder | â€" |

---

## Key URLs

| Resource | URL |
|----------|-----|
| Backend health | https://safevixai-backend.onrender.com/health |
| Chatbot health | https://safevixai-chatbot.onrender.com/health |
| Frontend | https://safevixai.vercel.app |
| Render dashboard | https://dashboard.render.com |
| Supabase dashboard | https://app.supabase.com |
| Upstash Redis | https://console.upstash.com |
| GitHub Actions | https://github.com/[org]/SafeVixAI/actions |
