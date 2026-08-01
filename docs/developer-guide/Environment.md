# SafeVixAI — Environment Variables

All environment variables needed to run the project's **three services** locally and in production.

---

## Backend — `backend/.env`

Copy `backend/.env.example` to `backend/.env`.

| Variable | Required | Default / Notes |
|----------|----------|-----------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@localhost:5432/safevixai` — auto-normalized from `postgres://` |
| `REDIS_URL` | No | Falls back to in-memory cache if missing |
| `CHATBOT_SERVICE_URL` | Yes | `http://localhost:8010/api/v1` |
| `JWT_SECRET_KEY` | No | Auto-generated in dev |
| `SUPABASE_JWT_SECRET` | No | For Supabase token validation |
| `SUPABASE_JWT_AUDIENCE` | No | Supabase audience |
| `ALLOWED_HOSTS` | No | Host header whitelist (production) |
| `ADMIN_SECRET` | Yes | Protects admin-only endpoints; set in Render env vars |
| `SENTRY_DSN` | No | Error tracking |
| `OPENROUTESERVICE_API_KEY` | No | Route calculation (free tier available) |
| `DATA_GOV_API_KEY` | No | Government data endpoints |
| `CPGRAMS_API_KEY` | No | Civic intel integration |
| `LGD_API_KEY` | No | Local Government Directory |
| `FRONTEND_URL` | No | CORS origin |
| `CORS_ORIGINS` | No | CORS origins override |
| `JWKS_URL` | No | JWKS endpoint for key validation |
| `ENABLE_MCP` | No | MCP server toggle |
| `ENVIRONMENT` | No | `development` (default) |

### Backend External APIs

| Variable | Required | Notes |
|----------|----------|-------|
| `OVERPASS_URLS` | No | Comma-separated; falls back to `https://overpass-api.de/api/interpreter` |
| `DATA_GOV_API_KEY` | No | For government data endpoints |

---

## Chatbot Service — `chatbot_service/.env`

Copy `chatbot_service/.env.example` to `chatbot_service/.env`.

| Variable | Required | Default / Notes |
|----------|----------|-----------------|
| `DEFAULT_LLM_PROVIDER` | Yes | `groq` |
| `DEFAULT_LLM_MODEL` | Yes | `deterministic-rag` |
| `HF_TOKEN` | No | HuggingFace token — used as Sarvam fallback, Shuka, BharatGen, Whisper via HF Inference API. Not needed for core chatbot flow |
| `CHROMA_PERSIST_DIR` | No | `./data/chroma_db` |
| `EMBEDDING_MODEL` | No | Config hint: `LocalHashEmbeddingFunction` — runtime uses hash-based 384-dim embeddings |
| `REDIS_URL` | No | Falls back to in-memory store |
| `MAIN_BACKEND_BASE_URL` | Yes | `http://localhost:8000` |
| `OPENWEATHER_API_KEY` | No | For WeatherTool in agent |
| `W3W_API_KEY` | No | For What3Words tool |
| `OPENCAGE_API_KEY` | No | Geocoding fallback |
| `ALERT_EMAIL` | No | Email for LLM failure alerts |
| `ALERT_EMAIL_PASSWORD` | No | Email password/app password |
| `ADMIN_SECRET` | No | Admin operations |
| `SENTRY_DSN` | No | Error tracking |
| `ENVIRONMENT` | No | `development` (default) |

### LLM Provider API Keys

| Variable | Required | Provider |
|----------|----------|----------|
| `GROQ_API_KEY` | Varies | Groq — primary English provider (300+ tok/s) |
| `GEMINI_API_KEY` | Varies | Google Gemini 1.5 Flash (1M context) |
| `CEREBRAS_API_KEY` | Varies | Cerebras — speed overflow (2000+ tok/s) |
| `GITHUB_TOKEN` | Varies | GitHub Models — free with GitHub account |
| `NVIDIA_NIM_API_KEY` | Varies | NVIDIA NIM — GPU-optimized inference |
| `OPENROUTER_API_KEY` | Varies | OpenRouter — gateway to 20+ models |
| `MISTRAL_API_KEY` | Varies | Mistral — 1B tokens/month free |
| `TOGETHER_API_KEY` | Varies | Together AI — $25 free credit |
| `SARVAM_API_KEY` | Varies | Sarvam AI — Indian language specialist |

> You only need keys for providers you want to enable. The ProviderRouter auto-skips providers without keys.

---

## Frontend — `frontend/.env.local`

Copy `frontend/.env.local.example` to `frontend/.env.local`.

| Variable | Required | Default |
|----------|----------|---------|
| `NEXT_PUBLIC_BACKEND_URL` | Yes | `http://localhost:8000` |
| `NEXT_PUBLIC_CHATBOT_URL` | Yes | `http://localhost:8010` |
| `NEXT_PUBLIC_POSTHOG_KEY` | No | PostHog analytics key |
| `NEXT_PUBLIC_POSTHOG_HOST` | No | `https://app.posthog.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | No | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | No | Supabase anonymous key |

> **IMPORTANT:** All frontend env variables must start with `NEXT_PUBLIC_` to be accessible in the browser.

---

## Security Notes

- `.env` and `.env.local` are in `.gitignore` — they will never be committed
- Never log or print API keys in your code
- Never put secrets in frontend code — only `NEXT_PUBLIC_*` vars in frontend
- Backend and chatbot service each have their **own** `.env` — don't mix them

---

*For full setup steps, see `SETUP.md`*
*For deployment steps, see `docs/Deployment.md`*
