# SafeVixAI Chatbot — Architecture

The SafeVixAI AI chatbot is a **separate Python service** (port 8010) that connects the frontend to advanced LLM behavior and real-time backend data.

## System Components
1. **Frontend (Next.js 15)**: Provides the Chat UI and API interface.
2. **Main Backend (FastAPI :8000)**: Manages PostgreSQL, PostGIS, and user data.
3. **Chatbot Service (FastAPI :8010)**: Independently manages the AI agent pipeline.
4. **Vectorstore (ChromaDB)**: Houses indexed legal and first-aid documents for retrieval.
5. **Memory (Redis)**: Stores conversation history for session-based persistence.

## Data Flow

```mermaid
flowchart TB
    subgraph Frontend[" Frontend — Chat UI "]
        UI["Next.js 15 PWA"]
    end

    subgraph Chatbot[" Chatbot Service — FastAPI :8010 "]
        direction TB
        SC[SafetyChecker] --> ID[IntentDetector]
        ID --> CA[ContextAssembler]
        CA -->|tool calls| TE[Tool Execution]
        TE --> PR[ProviderRouter]
        PR --> LLM[LLM Generation]
        LLM --> PC["Safety Post-Check"]
        PC --> MEM[Memory Persistence]
    end

    subgraph External[" External Dependencies "]
        B1["Backend API :8000<br/>PostGIS / DuckDB"]
        CV["ChromaDB<br/>Vector Store"]
        RM["Redis<br/>Conversation Memory"]
        LP["LLM Providers<br/>10-Provider Chain"]
    end

    UI -->|"Message + GPS"| SC
    MEM --> RM
    TE -->|"live data"| B1
    TE -->|"RAG chunks"| CV
    LLM --> LP

    style Frontend fill:#1f6feb,color:#fff
    style Chatbot fill:#9e6a03,color:#fff
    style External fill:#238636,color:#fff


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

    class Frontend edge
    class UI neutral
    class Chatbot ai
    class SC neutral
    class ID ai
    class CA neutral
    class TE neutral
    class PR neutral
    class LLM ai
    class PC action
    class MEM neutral
    class External external
    class B1 data
    class CV data
    class RM data
    class LP ai```

## Reliability: 10-provider Fallback Chain

To maintain maximum uptime, the service automatically cycles through **nine** LLM providers:

| Order | Provider | Speed | Specialty |
|-------|----------|-------|-----------|
| 1 | **Groq** | 300+ tok/s | Primary English (default: llama-3.1-8b-instant) |
| 2 | **Cerebras** | 2000+ tok/s | Speed overflow |
| 3 | **Gemini** | Varies | Large context (1M tokens) |
| 4 | **GitHub Models** | Varies | Free with GitHub account |
| 5 | **NVIDIA NIM** | Varies | GPU-optimized inference |
| 6 | **OpenRouter** | Varies | Gateway to 20+ models |
| 7 | **Mistral** | Varies | 1B tokens/month free |
| 8 | **Together** | Varies | $25 free credit bank |
| 9 | **Template** | Instant | Deterministic fallback — always works |

## Indian Language Path (Separate — Not in Fallback Chain)

| Condition | Provider | Model |
|-----------|----------|-------|
| Indian language input (Hindi, Tamil, Telugu, etc.) | Sarvam AI (direct API) | sarvam-30b |
| Legal/challan + Indian language | Sarvam AI (direct API) | sarvam-105b |
| Sarvam API key missing | HF Inference API (via HF_TOKEN) | sarvam-30b/105b |

> **14 Indian languages** supported via regex Unicode script range detection. Sarvam is auto-routed — it bypasses the main fallback chain entirely.
