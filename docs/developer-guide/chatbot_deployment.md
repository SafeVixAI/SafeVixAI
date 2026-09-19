# Deployment Guide — Chatbot Service

The Chatbot Service runs on its own independent instance on [Render.com](https://render.com). This separation ensures the heavy ML dependencies (torch ~2GB) don't bloat the main backend.

## Prerequisites
- A GitHub account connected to Render.
- Access to LLM API keys (Groq, Sarvam AI, Gemini, etc. — only enabled providers need keys).
- A running Redis instance for conversation memory (optional — falls back to in-memory).

## Steps for Deployment
1. **New Web Service**: Click `New` → `Web Service` on Render.
2. **Setup**:
   - **Root Directory**: `chatbot_service`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`
   - **Instance Type**: `Free tier` (512MB RAM, shared CPU) is sufficient for initial testing.
3. **Environment**: Input all `.env` variables from the dashboard Environment panel.
4. **Health Check**: Set health check path to `/health`.

## Production ChromaDB Strategy
The ChromaDB vectorstore is **committed to git** at `chatbot_service/data/chroma_db/`:
- **No build-time step needed**: Render gets the vectorstore automatically on `git clone`.
- **Startup**: Loads from the committed index in under 5 seconds.
- **Updates**: To update the vectorstore, rebuild locally and commit the new `chroma_db/` directory.

> **Important**: Never `.gitignore` the `chatbot_service/data/chroma_db/` directory — Render's ephemeral disk means the vectorstore must be in the git repo.

## CI/CD Pipeline
- **Production**: Merges to `main` trigger a deployment to the production environment.
- **Testing**: Deployment only occurs if all `pytest` suites in `chatbot_service/tests/` pass (892/892 tests, 95% coverage).

## Port Configuration
The chatbot service runs on **port 8010** locally. On Render, it uses `$PORT` (automatically assigned). The main backend connects to it via the `CHATBOT_SERVICE_URL` environment variable.
