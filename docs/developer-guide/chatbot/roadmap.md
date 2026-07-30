# SafeVixAI Chatbot — Implementation Roadmap

The development of the chatbot service was divided into nine phases to ensure build consistency and avoid conflicts.

## Phase 1: Foundation ✅
- Created `chatbot_service/` folder and setup base directories.
- Configured all 10 LLM provider API wrappers with auto-fallback.
- Configured Sarvam AI Indian language path (separate from main fallback chain).
- Verified health checks for all providers.

## Phase 2: RAG Pipeline ✅
- Indexed Motor Vehicles Act and WHO PDFs into ChromaDB.
- Built the document retriever with MMR (Maximal Marginal Relevance) search.
- Committed `chatbot_service/data/chroma_db/` to git for Render deployment.
- RAG config: top_k=5, min_score=0.55, LocalHashEmbeddingFunction (384-dim).

## Phase 3: Intent Detection ✅
- Built rule-based `IntentDetector` using keyword matching and regex patterns.
- 9 intent categories with support for multilingual input.
- No separate LLM call — instant classification (<1ms).

## Phase 4: Agent Tools ✅
- Implemented 13 tools: SosTool, ChallanTool, LegalSearchTool, FirstAidTool, WeatherTool, OpenMeteoTool, RoadInfrastructureTool, RoadIssuesTool, SubmitReportTool, GeocodingClient, DrugInfoTool, What3WordsTool, EmergencyTool.
- Connected all tools to the main backend APIs via `httpx` async client.

## Phase 5: Agent Assembly ✅
- Wired everything into a custom `ChatEngine` class (`agent/graph.py`).
- 8 agent modules: context_assembler.py, governance.py, graph.py, intent_detector.py, safety_checker.py, state.py, __init__.py.
- Implemented conversation memory with Redis (`memory/store.py`), 24h TTL.
- Built `ContextAssembler` to orchestrate parallel tool calls.

## Phase 6: Multi-Provider Routing ✅
- Implemented `ProviderRouter` with 10-provider fallback chain: Groq → Cerebras → Gemini → GitHub Models → NVIDIA NIM → OpenRouter → Mistral → Together → Template.
- 13 provider files: base.py, cerebras, gemini, github_models, groq, mistral, nvidia_nim, openrouter, router.py, sarvam, together, __init__.py.
- Added Sarvam AI auto-routing for Indian languages (regex Unicode detection).
- Added `TemplateProvider` as always-works deterministic fallback.

## Phase 7: Indian Language Support ✅
- Integrated Sarvam AI (30B general, 105B legal) for Hindi, Tamil, Telugu, etc. — 14 Indian languages.
- Added IndicSeamless speech model (ai4bharat/indic-seamless) for Indian language ASR/TTS.
- Speech endpoints: `POST /speech/translate`, `GET /speech/status`.

## Phase 8: Voice Integration ✅
- Added voice input/output on the frontend (Web Speech API).
- Implemented auto-read logic for emergency responses.
- 4 service files: pothole_validator.py, speech_translation.py, __init__.py.

## Phase 9: Safety and Hardening ✅
- `SafetyChecker` node with pre/post validation — 12-pattern prompt injection guard.
- Governance audit trail (`governance.py`).
- Rate limits and provider health monitoring.
- All injury responses must start with "Call 112 immediately."
- All 9 phases complete — 892/892 tests passing, 95% coverage.
