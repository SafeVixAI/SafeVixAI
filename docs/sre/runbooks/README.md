# Runbooks

This directory contains operational runbooks for SafeVixAI production incidents.

## Index

| Runbook | Description | Severity |
|---------|-------------|----------|
| [RB-001: LLM Provider Outage](RB-001-llm-outage.md) | All 10 providers down | P0 |
| [RB-002: Database Failover](RB-002-db-failover.md) | Primary RDS unavailable | P0 |
| [RB-003: Redis Cache Failure](redis-down.md) | Redis unreachable | P1 |
| [RB-004: Service Degradation](high-error-rate.md) | High latency / 5xx errors | P1 |
| [RB-005: Deployment Rollback](RB-005-rollback.md) | Failed deployment | P1 |
| [RB-006: Secrets Rotation Failure](api-key-rotation.md) | Secrets rotation failed | P2 |
| [RB-007: CI/CD Pipeline Failure](smoke-tests.md) | CI/CD broken | P2 |

## Severity Levels

| Level | Response Time | Example |
|-------|--------------|---------|
| **P0** | Immediate (< 15 min) | Complete outage, data loss |
| **P1** | < 1 hour | Partial outage, degraded performance |
| **P2** | < 4 hours | Non-critical, no user impact |
| **P3** | < 24 hours | Cosmetic, minor bugs |
