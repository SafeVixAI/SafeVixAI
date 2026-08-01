# Third-Party Integrations

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [Environment.md](../developer-guide/Environment.md), [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md), [Security.md](../architecture/Security.md)

---

## LLM Providers

SafeVixAI integrates with 10 LLM providers in a cascading fallback chain.

| Provider | Config Key | Auth Method | Rate Limit | Cost | Fallback Order |
|----------|-----------|-------------|------------|------|----------------|
| [Groq](https://groq.com) | `GROQ_API_KEY` | API Key | 30 req/min (free) | Free tier | 1 |
| [Cerebras](https://cerebras.ai) | `CEREBRAS_API_KEY` | API Key | 50 req/min | Free tier | 2 |
| [Gemini](https://ai.google.dev) | `GEMINI_API_KEY` | API Key | 60 req/min | Free tier | 3 |
| [GitHub Models](https://github.com/marketplace/models) | `GITHUB_TOKEN` | Token | 100 req/min | Free | 4 |
| [NVIDIA NIM](https://build.nvidia.com) | `NVIDIA_API_KEY` | API Key | 20 req/min | Free tier | 5 |
| [OpenRouter](https://openrouter.ai) | `OPENROUTER_API_KEY` | API Key | 20 req/min | Pay-per-use | 6 |
| [Mistral AI](https://mistral.ai) | `MISTRAL_API_KEY` | API Key | 30 req/min | Free tier | 7 |
| [Together AI](https://together.ai) | `TOGETHER_API_KEY` | API Key | 10 req/min | Free credits | 8 |
| [Sarvam AI](https://sarvam.ai) | `SARVAM_API_KEY` | API Key | 20 req/min | Free tier | Indian lang |
| Template | — | None | Unlimited | Free | Last resort |

Sarvam AI is **not** in the numeric fallback chain. It is used exclusively for Indian language routing (auto-detected via Unicode script ranges).

---

## Mapping & Geocoding

| Service | Purpose | Config | Auth | Rate Limit | Fallback |
|---------|---------|--------|------|------------|----------|
| [OpenStreetMap Overpass](https://overpass-api.de) | Road/feature data | `OVERPASS_URLS` | None | Varies by instance | Multi-URL fallback |
| [Nominatim](https://nominatim.org) | Geocoding (address ↔ coords) | Built-in | User-Agent header | 1 req/sec | None (required) |
| [OpenRouteService](https://openrouteservice.org) | Route optimization | `OPENROUTESERVICE_API_KEY` | API Key | 40 req/min (free) | OSRM |
| [Photon](https://photon.komoot.io) | Geocoding (chatbot tool) | — | None | Unclear | BigDataCloud |
| [BigDataCloud](https://www.bigdatacloud.com) | Geocoding (chatbot tool) | — | API Key (optional) | 5K/day (free) | Photon |

---

## Weather

| Service | Purpose | Config | Auth | Rate Limit | Cost |
|---------|---------|--------|------|------------|------|
| [OpenWeather](https://openweathermap.org) | Weather data for chatbot | `OPENWEATHER_API_KEY` | API Key | 60 req/min | Free tier |
| [Open-Meteo](https://open-meteo.com) | Weather (visibility, precipitation) | — | None | Unlimited | Free |

---

## Analytics & Error Tracking

| Service | Purpose | Config | Auth | Cost |
|---------|---------|--------|------|------|
| [PostHog](https://posthog.com) | Product analytics | `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST` | API Key | Free tier |
| [Sentry](https://sentry.io) | Error tracking | `SENTRY_DSN` (config) | DSN | Free tier |

---

## Infrastructure

| Service | Purpose | Cost | Notes |
|---------|---------|------|-------|
| [Vercel](https://vercel.com) | Frontend hosting | Free (Hobby) | Auto-deploys from `main` |
| [Render](https://render.com) | Backend + Chatbot hosting | Free (Web Services) | 750 hours/month each |
| [Supabase](https://supabase.com) | PostgreSQL + PostGIS | Free tier | 500MB database |
| [Upstash](https://upstash.com) | Redis | Free tier | 10MB, 1000 commands/day |

---

## Other Integrations

| Service | Purpose | Config | Notes |
|---------|---------|--------|-------|
| [What3Words](https://what3words.com) | Location resolution (chatbot) | `W3W_API_KEY` | For precise location sharing |
| [OpenFDA](https://open.fda.gov) | Drug/medical information (chatbot) | — | Free API, no key needed |
| [Data.gov.in](https://data.gov.in) | Government open data | `DATA_GOV_API_KEY` | Road/accident datasets |
| [Hugging Face](https://huggingface.co) | Model inference (Sarvam fallback) | `HF_TOKEN` | Fallback when Sarvam API is unavailable |

---

## Email Alerts

| Service | Purpose | Config | Notes |
|---------|---------|--------|-------|
| SMTP (configurable) | Critical failure alerts | `ALERT_EMAIL`, `ALERT_EMAIL_PASSWORD` | 5-min cooldown, 3 diagnostic solutions |

---

## Fallback Behavior

All external integrations have fallbacks:

| Integration | Primary | Fallback |
|-------------|---------|----------|
| LLM providers | Groq → Cerebras → ... → Template | Deterministic fallback always works |
| Route optimization | OpenRouteService | OSRM |
| Geocoding | Photon | BigDataCloud |
| Redis | External Redis | In-memory (graceful degradation) |
| ChromaDB | Persistent DB | Graceful error with clear message |

---

## Integration Status

SafeVixAI uses **circuit breakers** for all 8 external API calls. After 3 consecutive failures, the circuit opens for 30 seconds before allowing a retry. This prevents cascading failures when an external service is degraded.
