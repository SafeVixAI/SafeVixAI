# SafeVixAI Incident Response Plan

**Version:** 1.0
**Last Updated:** 2026-07-14

## 1. Severity Classification

| Severity | Definition | Examples | Response Time |
|----------|-----------|----------|---------------|
| P0-Critical | Complete service outage, data loss, security breach | Both API services down, DB corruption, user PII leak | < 30 min |
| P1-High | Major feature unavailable, partial outage | Single API down, LLM all-fail, Redis down | < 2 hr |
| P2-Medium | Minor feature degraded, non-critical bug | Slow LLM fallback, stale cache, single endpoint degraded | < 8 hr |
| P3-Low | Cosmetic issue, documentation error | Stale doc, incorrect UI text, non-functional preference | Next business day |
| P4-Wish | Feature request, enhancement | New provider integration, UI polish | Triage backlog |

## 2. Incident Lifecycle

### Detection
- **Automated:** Health check failures on /health endpoints, email alerts from core/alert.py (5-min cooldown), CI pipeline failures
- **Manual:** User reports, maintainer observation, E2E test suite failures

### Triage (within severity response time)
1. Identify affected service (backend, chatbot, frontend, DB, Redis)
2. Determine severity based on user impact
3. Assign incident owner
4. Create incident entry in CHANGELOG

### Mitigation
1. Apply runbook if one exists for the failure pattern (see playbooks/)
2. If no runbook: stabilize first (rollback, restart, failover), investigate later
3. Document actions taken for postmortem

### Resolution
1. Verify fix with health endpoints
2. Run relevant test suites (pytest for backend/chatbot, npm test for frontend)
3. Deploy fix via standard CI pipeline
4. Monitor for 15 minutes post-deploy

### Postmortem (required for P0, recommended for P1)
- Create postmortem document
- Identify root cause with timeline
- List action items to prevent recurrence
- Share with maintainers

## 3. Escalation Matrix

| When | Escalate To | Method |
|------|-------------|--------|
| P0 no response in 15 min | All maintainers | Email via ALERT_EMAIL |
| P1 no response in 1 hr | Project lead | Email + phone if available |
| Security incident (any severity) | Security contact | Email with [SECURITY] prefix |
| Insufficient runbook coverage | Backend or chatbot lead | GitHub issue with runbook label |

## 4. Communication Templates

### Incident Acknowledgment
```
Subject: [INCIDENT] <P0/P1/P2> - <Brief description>
Service: <backend/chatbot/frontend/db/redis>
Impact: <what is broken>
Started: <timestamp>
Owner: <name>
Status: Investigating / Mitigating / Resolved / Monitoring
```

### Resolution Notice
```
Subject: [RESOLVED] <P0/P1/P2> - <Brief description>
Duration: Xh Ym
Root Cause: <one line>
Action: <rolled back / fixed / restarted>
Verification: <tests passed / health check OK>
```

## 5. Postmortem Template

```markdown
# Postmortem: <Title>

Date: YYYY-MM-DD
Severity: P0/P1
Duration: Xh Ym
Owner: <name>

## Summary
One paragraph describing what happened.

## Timeline
- HH:MM - Incident detected (method)
- HH:MM - Triage started
- HH:MM - Mitigation applied
- HH:MM - Service verified healthy

## Root Cause
What caused the incident.

## Resolution
What was done to fix it.

## Action Items
- [ ] Item 1 (@owner, ETA)
- [ ] Item 2 (@owner, ETA)

## Lessons Learned
What would prevent this in the future.
```

## 6. Testing Verification After Incident

```bash
curl -f http://localhost:8000/health
curl -f http://localhost:8010/health
curl -f "http://localhost:8000/api/v1/emergency/nearby?lat=13.0827&lon=80.2707"
cd backend && pytest tests/ -q --tb=short
cd chatbot_service && pytest tests/ -q --tb=short
cd frontend && npm test -- --watchAll=false
```
