# Incident Severity Matrix

## Definitions

| Severity | Label | Response Time | Example |
|----------|-------|---------------|---------|
| **P0** | Critical | < 15 min | SOS system down, all LLM providers failing, data breach |
| **P1** | High | < 1 hour | Chatbot unavailable, backend 5xx, database slow |
| **P2** | Medium | < 4 hours | Single LLM provider down, non-critical endpoint broken |
| **P3** | Low | < 24 hours | Bug in admin UI, cosmetic issue, documentation error |
| **P4** | Informational | No SLA | Feature request, question, feedback |

## Escalation Path

```
P4 → Triage team (GitHub Issues)
P3 → Core contributor on duty
P2 → Core contributor lead
P1 → Security Team (if security) or Core Contributor lead
P0 → Project Lead + Security Team + all Core Contributors
```

## Response Playbooks

| Runbook | Covers |
|---------|--------|
| [RB-001](../runbooks/RB-001-llm-outage.md) | LLM Provider Outage (P0) |
| [RB-002](../runbooks/RB-002-db-failover.md) | Database Failover (P0) |
| [RB-003](../runbooks/redis-down.md) | Redis Cache Failure (P1) |
| [RB-005](../runbooks/RB-005-rollback.md) | Deployment Rollback (P1) |
| [All runbooks](README.md) | Complete index |
