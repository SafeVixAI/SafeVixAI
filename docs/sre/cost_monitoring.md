# SafeVixAI â€" Cost Monitoring

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

**Date:** 2026-05-18
**Review cadence:** Weekly

---

## API Cost Tracking

### LLM Providers
| Provider | Free Tier | Paid Tier | Current Monthly Cost |
|----------|-----------|-----------|---------------------|
| Groq | 30 req/min | $0.90/1M tokens | $0 (within free) |
| Gemini | 1,500 req/day | $0.35/1M tokens | $0 (within free) |
| Cerebras | Unlimited (beta) | Pay per use | $0 (free tier) |
| OpenRouter | $1 credit | Varies by model | $0 (within credit) |
| Mistral | Free tier | â‚¬0.25/1M tokens | $0 (within free) |
| Sarvam | Free tier | Pay per use | $0 (within free) |

### Map & Geocoding
| Provider | Free Tier | Paid Tier | Current Monthly Cost |
|----------|-----------|-----------|---------------------|
| MapTiler | 100K tiles/mo | $10/mo for 500K | $0 (within free) |
| TomTom | 2,500 req/day | $12.50/mo | $0 (within free) |
| BigDataCloud | 10K req/mo | Pay per use | $0 (within free) |
| Photon | Free (fair use) | N/A | $0 |
| Nominatim | Free (fair use) | N/A | $0 |

### Other Services
| Provider | Free Tier | Paid Tier | Current Monthly Cost |
|----------|-----------|-----------|---------------------|
| OpenWeather | 1,000 req/day | $40/mo | $0 (within free) |
| What3Words | 2,500 req/day | $20/mo | $0 (within free) |
| Supabase | 500MB DB | $25/mo Pro | $0 (within free) |
| Upstash Redis | 256MB, 10K ops/day | $10/mo | $0 (within free) |
| Render | 750 hrs/mo | $7/mo Starter | $0 (within free) |
| Vercel | 100GB bandwidth | $20/mo Pro | $0 (within free) |
| Sentry | 5K errors/mo | $26/mo Team | $0 (within free) |

---

## Total Monthly Cost: $0

### Budget Alerts
Set up alerts in each provider's console at 80% of free tier limit.

### Cost Optimization Tips
1. Use TemplateProvider as fallback (deterministic, $0 cost)
2. Cache LLM responses in Redis (reduces API calls by ~20%)
3. Use Photon/Nominatim before paid geocoding APIs
4. Use MapLibre GL (free) instead of Google Maps ($200+/mo)
5. Keep ChromaDB pre-built (avoids 10-min rebuild cost)
