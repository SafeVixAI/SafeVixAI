# Incident Response Playbooks

## Quick Reference Card

| Symptom | Likely Cause | Immediate Action | Runbook |
|---------|-------------|-----------------|---------|
| Both APIs unreachable | Render outage or deploy issue | Check Render dashboard, rollback | RB-005 |
| Backend API down, chatbot up | Backend crash or DB issue | Check backend logs, restart | RB-003, RB-002 |
| Chatbot API down, backend up | Chatbot crash or ChromaDB issue | Restart chatbot, check ChromaDB | RB-003, RB-004 |
| LLM responses failing | Provider API key expired or rate limit | Check provider keys, fallback auto-activates | RB-001 |
| Slow responses | Redis down or DB degradation | Check Redis, check query performance | RB-007, RB-002 |
| DB connection errors | Postgres down or pool exhausted | Restart Postgres, check connection count | RB-003 |
| Redis cache misses | Redis down | In-memory fallback auto-activates | RB-007 |
| Frontend not loading | Vercel build failure or DNS | Check Vercel deploy log, re-deploy | RB-005 |
| Email alerts not sending | SMTP config or alert.py error | Check ALERT_EMAIL/ALERT_EMAIL_PASSWORD env vars | core/alert.py |
