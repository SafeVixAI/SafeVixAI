# SafeVixAI — AI Instructions

> **Version 2.1** | AI-powered road safety platform  
> Reflects the current chatbot/agent architecture.

---

## Chatbot Agent Architecture v1.0.0

### Execution Flow

```
User message
  ? SafetyChecker.evaluate()          # Block harmful queries, prepend "Call 112 immediately" for injuries
  ? IntentDetector.detect()           # 9 intent classes, keyword/regex, <1ms
  ? ContextAssembler.assemble()        # Call relevant tools + retrieve RAG chunks
  ? ProviderRouter.generate()          # LLM call with asyncio.wait_for() timeout + auto-fallback chain
  ? ConversationMemoryStore.append()   # Redis session persistence (24h TTL)
  ? ChatResponse
```

### Location of Core Components

All agent logic lives under `chatbot_service/`:

| Component | Path |
|-----------|------|
| Chat engine (graph) | `agent/chat_engine.py` |
| Intent detector | `agent/intent_detector.py` |
| Safety checker | `agent/safety_checker.py` |
| Context assembler | `agent/context_assembler.py` |
| Provider router | `providers/provider_router.py` |
| Conversation memory | `memory/conversation_memory.py` |
| Agent tools (13) | `tools/*.py` |
| LLM providers (9) | `providers/*.py` |
| Governance / audit | `agent/governance.py` |

---

## 9 Intent Classes

Defined in `chatbot_service/agent/intent_detector.py`. Uses keyword matching + regex — **not** a separate LLM call (<1ms).

| Intent | Triggers |
|--------|----------|
| `emergency` | accident, ambulance, hospital, police, sos, crash, injured |
| `first_aid` | bleeding, burn, fracture, cpr, choking, unconscious |
| `challan` | challan, fine, helmet, seatbelt, drunk driving, licence |
| `legal` | motor vehicles act, mv act, section, legal, rights, mva |
| `road_weather` | weather, rain, flood, fog, visibility, storm, monsoon |
| `safe_route` | route, navigate, directions, safest way, safe route |
| `road_infrastructure` | road authority, pwd, nhai, pmgsy, contractor, maintenance |
| `road_issue` | pothole, road hazard, debris, bad road, damaged road |
| `general` | Default fallback for all other queries |

---

## 13 Agent Tools

| Tool | File | Description |
|------|------|-------------|
| SosTool | `sos_tool.py` | Nearby emergency services via backend API |
| EmergencyTool | `tools/__init__.py` (BackendToolClient) | Emergency service lookup |
| ChallanTool | `challan_tool.py` | Fine calculation via backend API |
| LegalSearchTool | `legal_search_tool.py` | ChromaDB vector search (Motor Vehicles Act, MoRTH) |
| FirstAidTool | `first_aid_tool.py` | Static JSON first-aid protocols |
| WeatherTool | `weather_tool.py` | OpenWeather API |
| OpenMeteoTool | `open_meteo.py` | Open-Meteo weather (visibility, precipitation) |
| RoadInfrastructureTool | `road_infra_tool.py` | Road contractor/budget data |
| RoadIssuesTool | `road_issues_tool.py` | Community-reported road issues |
| SubmitReportTool | `submit_report_tool.py` | Submit road damage reports |
| GeocodingClient | `geocoding.py` | Photon/BigDataCloud geocoding |
| DrugInfoTool | `drug_info.py` | Open FDA drug/medical information |
| What3WordsTool | `what3words.py` | What3Words location resolution |

---

## 10 LLM Providers

Located in `chatbot_service/providers/`.

### Fallback Chain (in order)

```
Groq (fastest, 300+ tok/s) ? Cerebras ? Gemini ? GitHub Models
    ? NVIDIA NIM ? OpenRouter ? Mistral ? Together ? Template (deterministic fallback)
```

If all 10 providers fail, `alert_service.py` (project root) sends an email with 3 diagnostic solutions (5-minute cooldown).

### Indian Language Auto-Routing (Separate Path, Not in Chain)

- **Language detection:** Unicode script range regex (Devnagari, Tamil, Telugu, etc.)
- **Sarvam-30B** — General Indic queries
- **Sarvam-105B** — Legal/challan queries in Indic languages (higher accuracy)
- Direct Sarvam API used if `SARVAM_API_KEY` is set
- Falls back to `HF_TOKEN` via HuggingFace Inference API if Sarvam key absent

### Provider Files

| Provider | File | Key Env Var |
|----------|------|-------------|
| Groq | `groq_provider.py` | `GROQ_API_KEY` |
| Cerebras | `cerebras_provider.py` | `CEREBRAS_API_KEY` |
| Gemini | `gemini_provider.py` | `GEMINI_API_KEY` |
| GitHub Models | `github_provider.py` | `GITHUB_TOKEN` |
| NVIDIA NIM | `nvidia_provider.py` | `NVIDIA_API_KEY` |
| OpenRouter | `openrouter_provider.py` | `OPENROUTER_API_KEY` |
| Mistral | `mistral_provider.py` | `MISTRAL_API_KEY` |
| Together | `together_provider.py` | `TOGETHER_API_KEY` |
| Template | `template_provider.py` | None (deterministic fallback) |

### Auto-Routing Rules

1. Indian language input (Hindi, Tamil, Telugu, etc.) ? **Sarvam-30B** (Indic specialist)
2. Legal/challan + Indian language ? **Sarvam-105B** (higher accuracy for law)
3. English ? Default provider (usually Groq, 300+ tok/s)
4. Rate-limited ? Cascade through fallback chain
5. All providers fail ? `TemplateProvider` (deterministic, always works)

---

## System Prompt

```python
SYSTEM_PROMPT = (
    "You are SafeVixAI, an AI assistant built for Indian road safety and emergency response. "
    "Help users with: emergency contacts, first aid, pothole/accident reporting, traffic challans, "
    "navigation, and road authority escalation. "
    "Always answer concisely in the SAME language the user writes in (Hindi, Tamil, Telugu, etc.). "
    "For life-threatening situations, always lead with 112 (universal emergency) or 102 (ambulance). "
    "Be factual — cite MV Act sections when answering challan questions."
)
```

---

## RAG System

### Vector Store

- **Engine:** ChromaDB
- **Embedding:** `LocalHashEmbeddingFunction` (384-dim, zero ML dependency, SHA-256 hash-based)
- **Similarity:** Cosine similarity
- **Parameters:** `top_k=5`, `min_score=0.55`
- **Documents:** Motor Vehicles Act sections, MoRTH guidelines, traffic rules, WHO first-aid protocols

### Two ChromaDB Instances

| Path | Commit Status | Notes |
|------|--------------|-------|
| `chatbot_service/data/chroma_db/` | **COMMITTED** | Render needs pre-built store at cold start |
| `backend/data/chroma_db/` | **GITIGNORED** | Built locally, ~10 min rebuild via `build_vectorstore.py` |

### Rebuilding the Index

```bash
# Add new PDFs to chatbot_service/data/ or backend/data/
# Then run:
cd chatbot_service
python data/build_vectorstore.py

# Restart the service to reload ChromaDB from disk
```

---

## Safety System

### SafetyChecker (`chatbot_service/agent/safety_checker.py`)

- `SafetyChecker.evaluate()` — Blocks prompt injection, hate speech, dangerous instructions
- 12-pattern prompt injection guard
- All injury responses **must** start with "Call 112 immediately"

### AI Governance (`chatbot_service/agent/governance.py`)

- Audit trail for all AI decisions
- Tracks: intent classification, provider used, tool calls, response safety check

---

## Speech System

### IndicSeamlessService

- **File:** `chatbot_service/services/speech_translation.py`
- **Model:** `ai4bharat/indic-seamless` (loaded at service startup)
- **Endpoints:** `POST /speech/translate`, `GET /speech/status`
- **Languages:** 14 Indian languages

### Endpoint Truth

```
POST /speech/translate   ? Correct, NOT /api/v1/speech/translate
GET  /speech/status
```

---

## 14-Language Mapping

Defined in `frontend/lib/languages.ts`. Each language has a 4-code mapping:

`UI code ? recognitionCode ? speechTargetCode ? synthesisCode`

| Language | Example Codes |
|----------|--------------|
| Hindi | `hi ? hi ? hin_Deva ? hi-IN` |
| Tamil | `ta ? ta ? tam_Taml ? ta-IN` |
| Telugu | `te ? te ? tel_Telu ? te-IN` |
| Bengali | `bn ? bn ? ben_Beng ? bn-IN` |
| Marathi | `mr ? mr ? mar_Deva ? mr-IN` |
| Gujarati | `gu ? gu ? guj_Gujr ? gu-IN` |
| Kannada | `kn ? kn ? kan_Knda ? kn-IN` |
| Malayalam | `ml ? ml ? mal_Mlym ? ml-IN` |
| Punjabi | `pa ? pa ? pan_Guru ? pa-IN` |
| Urdu | `ur ? ur ? urd_Arab ? ur-IN` |
| Odia | `or ? or ? ory_Orya ? or-IN` |
| Assamese | `as ? as ? asm_Beng ? as-IN` |
| English | `en ? en ? eng_Latn ? en-IN` |
| Hinglish | `hi-en ? hi ? hin_Deva ? hi-IN` |

This mapping is correctly used in `VoiceInput.tsx` and the assistant page `speechSynthesis`.

---

## Conversation Memory

- **Storage:** Redis with 24h TTL (`config.py: session_ttl_seconds = 86400`)
- **Library:** `chatbot_service/memory/conversation_memory.py` — `ConversationMemoryStore`
- **Fallback:** In-memory store if Redis is unavailable
- **Session ID:** Generated per conversation and passed as `session_id` in chat requests

---

## Offline AI

All offline AI runs client-side in the browser — no server required.

| Component | Technology | Model/Size | File |
|-----------|-----------|------------|------|
| Offline LLM | `@mlc-ai/web-llm` | Phi-3 Mini (2.2GB, WebGPU) | `frontend/lib/offline-ai.ts` |
| Pothole Detection | `@huggingface/transformers` | YOLOv8n (15MB ONNX) | `frontend/components/PotholeDetector.tsx` |
| Offline Challans | `@duckdb/duckdb-wasm` | DuckDB-Wasm WASM | `frontend/lib/duckdb-challan.ts` |

### Offline LLM Details

- Phi-3 Mini (3.8B params, 4-bit quantized, ~2.2GB)
- Downloads on-demand when user clicks "Use Offline AI"
- Falls back to Gemma-2B if WebGPU unavailable
- Bundles 20 WHO-based first-aid articles for offline RAG
- Builds HNSW index in IndexedDB (~30s first setup)

### Service Worker

Only activates in production (`npm run build && npm start`), not in dev mode.

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| Two separate FastAPI services | Chatbot has heavy ML deps (torch ~2GB); backend stays lightweight |
| 10-provider LLM fallback | Zero downtime — if one API rate-limits, next takes over |
| Sarvam AI for Indian languages | Trained on 4 trillion Indic tokens; best Hindi/Tamil legal accuracy |
| DuckDB for challans (not LLM) | Deterministic SQL; LLMs hallucinate fine amounts |
| ChromaDB committed to git | Render cold-starts need pre-built vectorstore; rebuild takes 10 min |
| LocalHashEmbeddingFunction | Zero ML dependency for embeddings; hash-based 384-dim vectors |
| Intent-first classification | <1ms routing avoids full RAG search on every message |
| Redis conversation memory | Fast session persistence with 24h TTL, graceful in-memory fallback |

---

## Chatbot Testing Checklist

| Test | Expected Response Contains |
|------|--------------------------|
| "nearest hospital" | Hospital name + phone + "Call 112" |
| "drunk driving fine" | "Section 185" + "Rs 10,000" |
| "helmet fine in Bangalore" | "Section 194C" + "Rs 1,000" + "Karnataka" |
| "someone is bleeding badly" | "Call 112 immediately" (first line) |
| "speed limit on highways" | Specific km/h value + MVA section |
| Send in Hindi | Response in Hindi (routed to Sarvam AI) |
| Send in Tamil | Response in Tamil (routed to Sarvam AI) |
| "hello" | Friendly greeting without legal content |

---

## Critical Rules (Never Break)

1. Any AI response about injuries **must** start with "Call 112 immediately"
2. Never delete `chatbot_service/data/chroma_db/` — it's committed for Render deployment
3. Backend and chatbot have **separate** `.venv`, `.env`, `requirements.txt` — never mix dependencies
4. WebLLM Phi-3 model (2.2GB) downloads on-demand only — never preload without user consent
5. All injury responses must pass through `SafetyChecker.evaluate()`
6. Do **not** change the system prompt without testing all 9 intent classes

---

*Document version: 2.1 | AI-powered road safety platform*
