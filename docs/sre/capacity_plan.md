# SafeVixAI â€" Capacity Planning Document

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

**Date:** 2026-05-18
**Review cadence:** Monthly

---

## API Rate Limits (Free Tiers)

| Provider | Limit | Current Usage | Alert at 80% |
|----------|-------|---------------|--------------|
| Groq | 30 req/min | Track via logs | 24 req/min |
| Gemini | 1,500 req/day | Track via logs | 1,200 req/day |
| OpenWeather | 1,000 req/day | Track via logs | 800 req/day |
| Overpass | No hard limit (fair use) | Track response times | >5s avg |
| Photon | No hard limit (fair use) | Track response times | >3s avg |
| Nominatim | 1 req/sec | Track via logs | 0.8 req/sec |
| What3Words | 2,500 req/day (free) | Track via logs | 2,000 req/day |

---

## Infrastructure Limits

### Render Free Tier
| Resource | Limit | Current | Alert at 80% |
|----------|-------|---------|--------------|
| RAM per service | 512MB | Monitor | 410MB |
| CPU | Shared | Monitor | N/A |
| Bandwidth | 100GB/month | Monitor | 80GB |
| Hours | 750/month | Monitor | 600 |

### Supabase Free Tier
| Resource | Limit | Current | Alert at 80% |
|----------|-------|---------|--------------|
| Database size | 500MB | Monitor | 400MB |
| API requests | Unlimited | Monitor latency | >500ms avg |
| Realtime connections | 200 | Monitor | 160 |

### Upstash Redis Free Tier
| Resource | Limit | Current | Alert at 80% |
|----------|-------|---------|--------------|
| Max clients | 10 | Monitor | 8 |
| Max memory | 256MB | Monitor | 205MB |
| Daily operations | 10K | Monitor | 8K |

---

## Growth Projections

| Metric | Current | 1 Month | 3 Months | 6 Months |
|--------|---------|---------|----------|----------|
| Daily active users | ~50 | ~200 | ~500 | ~1,000 |
| API requests/day | ~500 | ~2,000 | ~5,000 | ~10,000 |
| Chat queries/day | ~100 | ~400 | ~1,000 | ~2,000 |
| DB size | ~50MB | ~100MB | ~250MB | ~500MB |
| ChromaDB index | ~100MB | ~150MB | ~200MB | ~300MB |

---

## Scaling Triggers

| Trigger | Action | Cost Impact |
|---------|--------|-------------|
| RAM > 410MB on any service | Upgrade to Render Starter ($7/mo) | +$7/mo |
| Chatbot OOM kills | Upgrade to Render Standard ($25/mo) | +$25/mo |
| DB size > 400MB | Upgrade Supabase Pro ($25/mo) | +$25/mo |
| API rate limits hit | Add API key rotation or upgrade plan | Variable |
| Daily users > 500 | Add caching layer, optimize queries | +$0 (optimization) |
| Daily users > 1,000 | Add read replicas, CDN | +$10/mo |

---

## Monthly Cost Estimates

| Scenario | Cost |
|----------|------|
| Current (all free) | $0 |
| Starter (backend upgraded) | $7/mo |
| Standard (backend + chatbot) | $32/mo |
| Pro (all services upgraded) | $57/mo |
| Pro + Supabase + Redis | $82/mo |

---

## Monitoring Commands

```bash
# Check Render service memory
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/$SERVICE_ID/metrics"

# Check Supabase database size
SELECT pg_size_pretty(pg_database_size('postgres'));

# Check Redis memory usage
redis-cli INFO memory | grep used_memory_human

# Check ChromaDB index size
du -sh chatbot_service/data/chroma_db/
```
