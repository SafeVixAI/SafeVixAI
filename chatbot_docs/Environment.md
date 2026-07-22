# Environment Configuration — Chatbot Service

Create a `.env` file in the `chatbot_service/` root based on `.env.example`. This file should contain all the secret keys and service URLs.

## LLM Provider API Keys (all free tier)

| Variable | Provider | Notes |
|----------|----------|-------|
| `DEFAULT_LLM_PROVIDER` | — | Default provider name: `groq` (default), `gemini`, `cerebras`, etc. |
| `DEFAULT_LLM_MODEL` | — | Model ID (default: `llama-3.1-8b-instant`) |
| `GROQ_API_KEY` | Groq | Primary English provider (300+ tok/s) |
| `CEREBRAS_API_KEY` | Cerebras | Speed overflow (2000+ tok/s) |
| `GEMINI_API_KEY` | Google | Gemini 1.5 Flash (1M context) |
| `SARVAM_API_KEY` | Sarvam AI | Indian language specialist (30B/105B) |
| `GITHUB_TOKEN` | GitHub Models | Free with GitHub account |
| `NVIDIA_NIM_API_KEY` | NVIDIA NIM | GPU-optimized inference |
| `OPENROUTER_API_KEY` | OpenRouter | Gateway to 20+ models |
| `MISTRAL_API_KEY` | Mistral | 1B tokens/month free |
| `TOGETHER_API_KEY` | Together | $25 free credit bank |

> Only keys for providers you want to enable are needed. The `ProviderRouter` auto-skips providers without keys.

## Backend Connection
- `MAIN_BACKEND_BASE_URL`: URL of the main SafeVixAI backend (e.g., `http://localhost:8000` for local, or `https://safevixai-api.onrender.com` for production).

## RAG Configuration
- `CHROMA_PERSIST_DIR`: Path to ChromaDB vectorstore (default: `./data/chroma_db`).
- `EMBEDDING_MODEL`: Config hint — runtime uses `LocalHashEmbeddingFunction` (hash-based, 384-dim, zero ML dependency).
- ChromaDB RAG: `top_k=5`, `min_score=0.55`

## Other Services
- `REDIS_URL`: Redis connection string for session memory (optional — falls back to in-memory). Session TTL: 86400s (24h).
- `OPENWEATHER_API_KEY`: Required for the `WeatherTool`.
- `W3W_API_KEY`: Required for the `What3WordsTool`.
- `OPENCAGE_API_KEY`: Required for OpenCage geocoding fallback.
- `HF_TOKEN`: HuggingFace token — used as Sarvam fallback + Shuka/BharatGen/Whisper via HF Inference API. Not needed for core chatbot flow.
- `ADMIN_SECRET`: Protects admin-only endpoints.
- `ALERT_EMAIL` / `ALERT_EMAIL_PASSWORD`: Email alert config when all 10 LLM providers fail (5-min cooldown).
- `SENTRY_DSN`: Optional Sentry error tracking.

## Local Development vs. Production
- **Local**: Point `MAIN_BACKEND_BASE_URL` to `http://localhost:8000`.
- **Production**: Point to the actual deployed backend URL on Render.com.

> [!WARNING]
> Never commit your `.env` file to the repository. Ensure `.gitignore` is properly configured for the `chatbot_service` folder.
