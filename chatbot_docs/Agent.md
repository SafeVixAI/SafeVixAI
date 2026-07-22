# SafeVixAI Chatbot — Agent Documentation

The SafeVixAI Chatbot is an **Agentic AI Assistant**, moving beyond simple chat interfaces to a system that can take real-world actions in emergencies.

## Core Architecture: RAG + Agent Tools

Instead of fine-tuning, which is static and compute-intensive, we use a **Retrieval-Augmented Generation (RAG)** combined with an **Agentic workflow** powered by 13 specialized tools.

### Why Agentic?
- **Action-Oriented**: The chatbot doesn't just answer; it calls emergency APIs, calculates fines, and triggers SOS alerts.
- **Real-Time Data**: It has contextual awareness of the user's GPS coordinates, nearby hospitals, and community reports.
- **Dynamic Decision Logic**: Using a custom `ChatEngine` class, the agent follows a deterministic graph to decide which tools to use and how to synthesize the response.

## Agent Orchestration (ChatEngine)

The agent follows a deterministic yet flexible execution sequence defined in `agent/graph.py`:

1. **SafetyChecker**: Evaluates the message for harmful content. Blocks if necessary.
2. **IntentDetector**: Classifies the message using rule-based keyword matching into one of 9 intents (e.g., `FIND_HOSPITAL`, `CHALLAN_QUERY`). Instant — no LLM call needed.
3. **ContextAssembler**: Based on the detected intent, determines which tools to invoke and gathers context.
4. **Tool Execution**: Runs selected tools concurrently (using `asyncio`) to gather real-time data from the backend API, ChromaDB, or external services.
5. **ProviderRouter**: Selects the optimal LLM provider based on language detection and available API keys. Builds the final prompt with system instructions + tool context + conversation history.
6. **LLM Generation**: Calls the selected provider (one of 9 in the fallback chain, or Sarvam for Indian languages) for final response synthesis.
7. **Safety Post-Check**: Ensures emergency responses include contact numbers (112) and nearest hospital info.
8. **Memory Persistence**: Stores the turn in Redis conversation memory (24hr TTL).

## 13 Agent Tools

| Tool | What It Does | Data Source |
|------|-------------|-------------|
| SosTool | Finds nearest emergency services | Backend API → PostGIS + Overpass |
| ChallanTool | Calculates traffic fines deterministically | Backend API → DuckDB SQL |
| LegalSearchTool | Searches MV Act and traffic regulations | ChromaDB vector search |
| FirstAidTool | Provides WHO-based first-aid protocols | Static JSON data |
| WeatherTool | Gets current weather conditions | OpenWeather API |
| OpenMeteoTool | Gets weather risk factors (precipitation, visibility) | Open-Meteo API |
| RoadInfrastructureTool | Returns contractor/budget/engineer info | Backend API → data.gov.in |
| RoadIssuesTool | Lists community-reported road issues | Backend API → PostGIS |
| SubmitReportTool | Submits road damage reports | Backend API → PostgreSQL |
| GeocodingClient | Reverse geocoding and address resolution | Photon/BigDataCloud |
| DrugInfoTool | Pharmaceutical lookup via Open FDA | Open FDA API |
| What3WordsTool | 3-word location resolution | What3Words API |
| EmergencyTool | Emergency service lookups | Backend API → PostGIS |

## Key Capabilities
- **Parallel Tool Calling**: Reduces response time for complex queries (e.g., finding both hospitals and police simultaneously).
- **10-provider LLM Fallback**: Groq → Cerebras → Gemini → GitHub Models → NVIDIA NIM → OpenRouter → Mistral → Together → Template.
- **Indian Language Auto-Routing**: Hindi, Tamil, Telugu, etc. detected via Unicode script range regex and routed to **Sarvam AI** (30B general / 105B legal) — separate path, not in main fallback chain.
- **14 Indian Languages**: Full support with IndicSeamless speech model for ASR/TTS.
