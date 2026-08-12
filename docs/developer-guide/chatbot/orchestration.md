# SafeVixAI Chatbot — Agent Documentation

The SafeVixAI Chatbot is an **Agentic AI Assistant**, moving beyond simple chat interfaces to a system that can take real-world actions in emergencies.

## Core Architecture: RAG + Agent Tools

Instead of fine-tuning, which is static and compute-intensive, we use a **Retrieval-Augmented Generation (RAG)** combined with an **Agentic workflow** powered by 13 specialized tools.

### Why Agentic?
- **Action-Oriented**: The chatbot doesn't just answer; it calls emergency APIs, calculates fines, and triggers SOS alerts.
- **Real-Time Data**: It has contextual awareness of the user's GPS coordinates, nearby hospitals, and community reports.
- **Dynamic Decision Logic**: Using a custom `ChatEngine` class, the agent follows a deterministic graph to decide which tools to use and how to synthesize the response.

## Agent Orchestration (ChatEngine)

```mermaid
flowchart TB
    subgraph AgentPipeline[" ChatEngine — Execution Pipeline "]
        direction TB
        S1["1. SafetyChecker<br/>Harmful content filter"] --> S2["2. IntentDetector<br/>Rule-based intent classification"]
        S2 --> S3["3. ContextAssembler<br/>Determine tools + gather context"]
        S3 --> S4["4. Tool Execution<br/>async concurrent tool calls"]
        S4 --> S5["5. ProviderRouter<br/>Language detection + provider selection"]
        S5 --> S6["6. LLM Generation<br/>Response synthesis"]
        S6 --> S7["7. Safety Post-Check<br/>Verify emergency numbers included"]
        S7 --> S8["8. Memory Persistence<br/>Redis 24hr TTL"]
    end

    S4 -->|"Backend API"| BE["Backend :8000<br/>PostGIS / DuckDB"]
    S4 -->|"Vector search"| CV["ChromaDB<br/>RAG Chunks"]
    S5 -->|"English"| GC["Groq / Cerebras /<br/>Gemini / GitHub / NVIDIA"]
    S5 -->|"Indian language"| SA["Sarvam AI<br/>30B / 105B"]
    S8 --> RM["Redis<br/>Conversation Memory"]

    style AgentPipeline fill:#1f6feb,color:#fff
    style BE fill:#238636,color:#fff
    style CV fill:#9e6a03,color:#fff
    style GC fill:#6e5494,color:#fff
    style SA fill:#9e6a03,color:#fff
    style RM fill:#238636,color:#fff


    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b
    classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#7c2d12
    classDef neutral fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b

    class AgentPipeline control
    class S1 neutral
    class S2 ai
    class S3 neutral
    class S4 neutral
    class S5 neutral
    class S6 ai
    class S7 action
    class S8 data
    class BE data
    class CV data
    class GC external
    class SA ai
    class RM data```

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
