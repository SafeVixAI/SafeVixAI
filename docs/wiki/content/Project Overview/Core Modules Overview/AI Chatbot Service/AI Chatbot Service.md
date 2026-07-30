# AI Chatbot Service

<cite>
**Referenced Files in This Document**
- [main.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py)
- [config.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/config.py)
- [intent_detector.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/intent_detector.py)
- [context_assembler.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/context_assembler.py)
- [state.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/state.py)
- [graph.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/graph.py)
- [router.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/router.py)
- [groq_provider.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/groq_provider.py)
- [gemini_provider.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/gemini_provider.py)
- [sarvam_provider.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/sarvam_provider.py)
- [vectorstore.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/vectorstore.py)
- [embeddings.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/embeddings.py)
- [redis_memory.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/memory/redis_memory.py)
- [speech_translation.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/services/speech_translation.py)
- [emergency_tool.py](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/tools/emergency_tool.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document describes the AI Chatbot Service that powers intelligent legal assistance and first aid guidance for road safety in India. It is an agentic Retrieval-Augmented Generation (RAG) system that:
- Detects user intent across nine classes of queries
- Assembles contextual information from vector retrieval, tools, and conversation history
- Routes to multiple LLM providers with automatic failover
- Integrates external services for emergencies, weather, geocoding, and road infrastructure
- Provides voice input/output capabilities with offline-friendly speech models
- Manages conversation memory with Redis and falls back to in-memory storage
- Supports multilingual interactions with Indian language routing and translation

## Project Structure
The chatbot service is organized around a FastAPI application that wires together:
- Agent orchestration (intent detection, context assembly, safety checks)
- Multi-provider LLM routing with fallback
- Vector store for legal and emergency documents
- Tools for external integrations
- Memory store for conversation history
- Speech translation service for voice I/O

```mermaid
graph TB
Client["Client App"] --> API["FastAPI App (/chat, /stream, /health)"]
API --> Engine["ChatEngine"]
Engine --> Memory["ConversationMemoryStore (Redis)"]
Engine --> Intent["IntentDetector"]
Engine --> Assembler["ContextAssembler"]
Engine --> Router["ProviderRouter"]
Assembler --> Vector["LocalVectorStore"]
Assembler --> Tools["External Tools"]
Router --> Providers["LLM Providers<br/>Groq, Gemini, Sarvam, etc."]
API --> Speech["IndicSeamlessService (STT/TTS)"]
```

**Diagram sources**
- [main.py:41-145](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py#L41-L145)
- [graph.py:15-109](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/graph.py#L15-L109)
- [router.py:75-199](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/router.py#L75-L199)
- [vectorstore.py:20-110](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/vectorstore.py#L20-L110)
- [redis_memory.py:10-90](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/memory/redis_memory.py#L10-L90)
- [speech_translation.py:34-141](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/services/speech_translation.py#L34-L141)

**Section sources**
- [main.py:41-145](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py#L41-L145)

## Core Components
- Intent Detection: Classifies incoming messages into nine intent buckets including emergency, first aid, challan, legal, road_issue, and general.
- Context Assembly: Builds a unified prompt by retrieving relevant documents, invoking tools for location-aware services, and enriching with conversation history.
- Provider Routing: Selects the optimal LLM provider based on language, intent, and availability, with a robust fallback chain.
- Vector Store: Loads and indexes legal and emergency documents locally, enabling semantic search.
- Memory Management: Persists chat histories with Redis and falls back to in-memory storage.
- Speech Translation: Provides offline-capable speech-to-text translation for multilingual input.
- Safety Checker: Evaluates prompts for policy compliance before generation.

**Section sources**
- [intent_detector.py:9-25](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/intent_detector.py#L9-L25)
- [context_assembler.py:17-215](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/context_assembler.py#L17-L215)
- [router.py:75-199](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/router.py#L75-L199)
- [vectorstore.py:20-110](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/vectorstore.py#L20-L110)
- [redis_memory.py:10-90](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/memory/redis_memory.py#L10-L90)
- [speech_translation.py:34-141](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/services/speech_translation.py#L34-L141)
- [state.py:9-52](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/state.py#L9-L52)

## Architecture Overview
The system follows an agentic RAG pattern:
- The ChatEngine orchestrates the lifecycle: safety check, intent detection, context assembly, provider selection, and response formatting.
- ContextAssembler selects tools and retriever scopes per intent and augments the prompt with retrieved snippets and tool summaries.
- ProviderRouter applies language-aware routing and automatic failover across multiple providers.
- VectorStore indexes documents and performs semantic search with scoring.
- MemoryStore persists and retrieves conversation history.
- SpeechTranslationService supports voice input with offline-friendly models.

```mermaid
sequenceDiagram
participant U as "User"
participant API as "FastAPI"
participant CE as "ChatEngine"
participant SC as "SafetyChecker"
participant ID as "IntentDetector"
participant CA as "ContextAssembler"
participant VS as "LocalVectorStore"
participant TR as "Retriever"
participant PR as "ProviderRouter"
participant LLM as "LLM Provider"
participant MS as "ConversationMemoryStore"
U->>API : "POST /api/v1/chat"
API->>CE : "ChatRequest"
CE->>MS : "append_message(user)"
CE->>SC : "evaluate(prompt)"
SC-->>CE : "allow/block"
CE->>ID : "detect(message)"
ID-->>CE : "intent"
CE->>CA : "assemble(session_id, message, intent, loc, ip, history)"
CA->>TR : "retrieve(message, scopes?)"
TR->>VS : "search(query, top_k)"
VS-->>TR : "chunks"
TR-->>CA : "results"
CA-->>CE : "ConversationContext"
CE->>PR : "generate(ProviderRequest)"
PR->>LLM : "generate(request)"
LLM-->>PR : "ProviderResult"
PR-->>CE : "result"
CE->>MS : "append_message(assistant, response)"
CE-->>API : "ChatResponse"
API-->>U : "response"
```

**Diagram sources**
- [graph.py:33-87](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/graph.py#L33-L87)
- [context_assembler.py:43-81](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/context_assembler.py#L43-L81)
- [vectorstore.py:51-68](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/vectorstore.py#L51-L68)
- [router.py:154-199](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/router.py#L154-L199)
- [redis_memory.py:23-44](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/memory/redis_memory.py#L23-L44)

## Detailed Component Analysis

### Intent Detection
The intent detector classifies user messages into nine categories:
- emergency: presence of keywords related to accidents, ambulances, hospitals, police, SOS
- first_aid: keywords for bleeding, burns, fractures, CPR, choking, first aid
- challan: mentions of challan/fine/helmet/seatbelt/drunk driving/licence and specific challan codes
- legal: motor vehicles act, sections, legal rights, inspection
- road_issue: potholes, road issues, authorities, maintenance, reporting roads
- general: default classification

```mermaid
flowchart TD
Start(["Message"]) --> Lower["Lowercase"]
Lower --> CheckE["Contains 'accident','ambulance','hospital','police','emergency','sos'?"]
CheckE --> |Yes| E["Intent: emergency"]
CheckE --> |No| CheckFA["Contains 'bleeding','burn','fracture','cpr','choking','first aid'?"]
CheckFA --> |Yes| FA["Intent: first_aid"]
CheckFA --> |No| CheckC["Code match or 'challan','fine','helmet','seatbelt','drunk driving','licence'?"]
CheckC --> |Yes| C["Intent: challan"]
CheckC --> |No| CheckL["Contains 'motor vehicles act','mv act','section','legal','rights','inspection'?"]
CheckL --> |Yes| L["Intent: legal"]
CheckL --> |No| CheckRI["Contains 'pothole','road issue','authority','road maintenance','report road'?"]
CheckRI --> |Yes| RI["Intent: road_issue"]
CheckRI --> |No| G["Intent: general"]
```

**Diagram sources**
- [intent_detector.py:10-24](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/intent_detector.py#L10-L24)

**Section sources**
- [intent_detector.py:9-25](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/intent_detector.py#L9-L25)

### Context Assembly
ContextAssembler builds a unified context per intent:
- emergency: adds nearby emergency services and weather near coordinates; retrieves medical/emergency/healthcare documents
- first_aid: adds first aid steps and optionally FDA drug info extracted from the message; retrieves medical documents
- challan: infers applicable sections and calculates fines; retrieves legal documents
- legal: retrieves legal documents
- road_issue: adds road infrastructure and nearby reported issues; optionally adds submission guidance
- general: retrieves broadly across categories

It also limits retrieved snippets and deduplicates tool and document sources.

```mermaid
classDiagram
class ContextAssembler {
+assemble(session_id, message, intent, lat, lon, client_ip, history) ConversationContext
-_add_emergency_context(context)
-_add_first_aid_context(context)
-_add_challan_context(context)
-_add_road_context(context)
-_add_retrieved(context, results)
}
class Retriever {
+retrieve(query, scopes) list
}
class SosTool
class WeatherTool
class FirstAidTool
class LegalSearchTool
class ChallanTool
class RoadInfrastructureTool
class RoadIssuesTool
class SubmitReportTool
class DrugInfoTool
ContextAssembler --> Retriever : "semantic search"
ContextAssembler --> SosTool : "nearby services"
ContextAssembler --> WeatherTool : "local weather"
ContextAssembler --> FirstAidTool : "first aid steps"
ContextAssembler --> LegalSearchTool : "legal docs"
ContextAssembler --> ChallanTool : "challan inference"
ContextAssembler --> RoadInfrastructureTool : "road authority"
ContextAssembler --> RoadIssuesTool : "reported issues"
ContextAssembler --> SubmitReportTool : "report guidance"
ContextAssembler --> DrugInfoTool : "drug info"
```

**Diagram sources**
- [context_assembler.py:17-215](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/context_assembler.py#L17-L215)

**Section sources**
- [context_assembler.py:43-215](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/context_assembler.py#L43-L215)

### Provider Routing and Multi-Provider LLM Support
ProviderRouter implements a 9-provider fallback chain with language-aware routing:
- Primary routing:
  - Indian language input → Sarvam AI (30B or 105B variant)
  - Legal/challan intent in Indian language → Sarvam-105B
  - Explicit provider hint or default provider
- Fallback chain prioritizes speed and capacity:
  - Groq (fastest English), Cerebras (overflow), Gemini (large context), GitHub/NVIDIA/OpenRouter/Mistral/Together, ending with template provider

```mermaid
classDiagram
class ProviderRouter {
+generate(request, detected_lang, try_fallbacks) ProviderResult
-_select_provider_name(request, detected_lang) str
}
class GroqProvider
class CerebrasProvider
class GeminiProvider
class SarvamProvider
class Sarvam105BProvider
class GitHubModelsProvider
class NvidiaNimProvider
class OpenRouterProvider
class MistralProvider
class TogetherProvider
class TemplateProvider
ProviderRouter --> GroqProvider : "primary"
ProviderRouter --> CerebrasProvider : "fallback"
ProviderRouter --> GeminiProvider : "fallback"
ProviderRouter --> SarvamProvider : "indiacentric"
ProviderRouter --> Sarvam105BProvider : "legal+indian"
ProviderRouter --> GitHubModelsProvider : "fallback"
ProviderRouter --> NvidiaNimProvider : "fallback"
ProviderRouter --> OpenRouterProvider : "fallback"
ProviderRouter --> MistralProvider : "fallback"
ProviderRouter --> TogetherProvider : "fallback"
ProviderRouter --> TemplateProvider : "last-resort"
```

**Diagram sources**
- [router.py:75-199](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/router.py#L75-L199)
- [groq_provider.py:10-23](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/groq_provider.py#L10-L23)
- [gemini_provider.py:18-71](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/gemini_provider.py#L18-L71)
- [sarvam_provider.py:44-125](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/sarvam_provider.py#L44-L125)

**Section sources**
- [router.py:1-199](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/router.py#L1-L199)
- [groq_provider.py:1-23](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/groq_provider.py#L1-L23)
- [gemini_provider.py:1-71](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/gemini_provider.py#L1-L71)
- [sarvam_provider.py:1-125](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/sarvam_provider.py#L1-L125)

### Vector Store Implementation
LocalVectorStore indexes documents from a data directory and persists a JSON index:
- Index loading: loads existing index or builds a new one
- Index building: loads documents, chunks them into fixed-size segments, and writes JSON
- Search: computes token overlap and phrase bonuses, filters by category scopes, sorts by score, returns top-k
- Stats: reports total chunks and unique categories

Embedding utilities:
- normalize_text: collapses whitespace
- tokenize: extracts alpha-numeric tokens
- score_query: overlap + phrase bonus + length normalization

```mermaid
flowchart TD
Load["ensure_index()"] --> HasCache{"In-memory cache?"}
HasCache --> |Yes| ReturnCache["Return cached chunks"]
HasCache --> |No| Exists{"Index file exists?"}
Exists --> |Yes| ReadFile["Load JSON index"] --> BuildList["Build DocumentChunk list"] --> ReturnCache
Exists --> |No| BuildNew["build_index(force=True)"] --> LoadDocs["load_documents(data_dir)"] --> Chunk["Chunk into ~900 chars"] --> Persist["Write JSON index"] --> ReturnCache
Search["search(query, top_k, scopes)"] --> Ensure["ensure_index()"] --> Score["score_query for each chunk"] --> Filter["Filter by scopes"] --> Sort["Sort desc by score"] --> TopK["Take top_k"]
```

**Diagram sources**
- [vectorstore.py:27-68](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/vectorstore.py#L27-L68)
- [embeddings.py:9-31](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/embeddings.py#L9-L31)

**Section sources**
- [vectorstore.py:20-110](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/vectorstore.py#L20-L110)
- [embeddings.py:1-31](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/embeddings.py#L1-L31)

### Conversation Memory Management
ConversationMemoryStore manages chat histories with Redis and an in-memory fallback:
- append_message: stores message with timestamp and metadata; pushes to Redis list and sets TTL
- get_history: reads last N messages from Redis or in-memory
- clear_session: deletes Redis key or clears in-memory list
- ping: pings Redis to probe health; toggles redis vs memory backend
- close: closes Redis connection

```mermaid
sequenceDiagram
participant CE as "ChatEngine"
participant MS as "ConversationMemoryStore"
CE->>MS : "append_message(session_id, role, content, metadata)"
alt Redis available
MS->>MS : "RPUSH + EXPIRE"
else Redis unavailable
MS->>MS : "Set redis_healthy=false"
end
CE->>MS : "get_history(session_id, limit)"
alt Redis healthy
MS-->>CE : "list from Redis"
else
MS-->>CE : "list from memory"
end
```

**Diagram sources**
- [redis_memory.py:23-56](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/memory/redis_memory.py#L23-L56)

**Section sources**
- [redis_memory.py:10-90](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/memory/redis_memory.py#L10-L90)

### Voice Input/Output Capabilities
IndicSeamlessService provides offline-friendly speech-to-text translation:
- Device auto-selection (CUDA if available, else CPU)
- Model loading from local directory or WebLLM CDN identifier
- Audio preprocessing (resampling to 16 kHz, mono)
- SeamlessM4Tv2 generation to target language
- Status reporting for configuration and readiness

```mermaid
classDiagram
class IndicSeamlessService {
+status() dict
+translate_audio_bytes(audio_bytes, target_language) SpeechTranslationResult
-_ensure_model_loaded()
-_resolve_device() str
}
class SpeechTranslationResult {
+text : str
+target_language : str
+device : str
+model_source : str
+sample_rate : int
}
IndicSeamlessService --> SpeechTranslationResult : "returns"
```

**Diagram sources**
- [speech_translation.py:34-141](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/services/speech_translation.py#L34-L141)

**Section sources**
- [speech_translation.py:1-141](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/services/speech_translation.py#L1-L141)

### Tool Execution System
ContextAssembler integrates several tools:
- SOS/Emergency: finds nearby emergency services and formats What3Words and numbers
- Weather: retrieves local conditions for coordinates
- First Aid: provides steps and optionally FDA drug info
- Challan: infers sections and calculates fines
- Road Infrastructure/Issues: authority and reported hazards near coordinates
- Submit Report: guidance for road hazard reporting

These tools enrich the prompt with structured summaries and sources.

**Section sources**
- [context_assembler.py:83-201](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/context_assembler.py#L83-L201)
- [emergency_tool.py:6-15](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/tools/emergency_tool.py#L6-L15)

### Safety Checking and Response Formatting
- SafetyChecker evaluates prompts and blocks unsafe content, returning a policy-compliant response
- ChatEngine formats ChatResponse with response text, intent, de-duplicated sources, and session_id
- Sources are derived from tool summaries and retrieved document sources

**Section sources**
- [graph.py:38-87](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/graph.py#L38-L87)
- [state.py:17-22](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/state.py#L17-L22)

## Dependency Analysis
Key internal dependencies:
- main.py constructs ChatEngine, ContextAssembler, ProviderRouter, LocalVectorStore, ConversationMemoryStore, and tools
- ChatEngine depends on IntentDetector, ContextAssembler, ProviderRouter, LocalVectorStore, and ConversationMemoryStore
- ContextAssembler depends on Retriever, tools, and LegalSearchTool
- ProviderRouter composes multiple providers and applies language detection and fallback logic
- LocalVectorStore depends on document loader and embedding utilities

```mermaid
graph LR
Main["main.py"] --> CE["ChatEngine"]
Main --> CA["ContextAssembler"]
Main --> PR["ProviderRouter"]
Main --> VS["LocalVectorStore"]
Main --> MS["ConversationMemoryStore"]
CE --> ID["IntentDetector"]
CE --> CA
CE --> PR
CE --> MS
CE --> VS
CA --> TR["Retriever"]
CA --> Tools["Tools"]
PR --> Providers["LLM Providers"]
VS --> Embeds["embeddings.py"]
```

**Diagram sources**
- [main.py:41-93](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py#L41-L93)
- [graph.py:15-32](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/graph.py#L15-L32)
- [context_assembler.py:17-42](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/context_assembler.py#L17-L42)
- [router.py:75-109](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/router.py#L75-L109)
- [vectorstore.py:7-8](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/vectorstore.py#L7-L8)
- [embeddings.py:1-31](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/embeddings.py#L1-L31)

**Section sources**
- [main.py:41-93](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py#L41-L93)
- [graph.py:15-32](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/graph.py#L15-L32)
- [context_assembler.py:17-42](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/agent/context_assembler.py#L17-L42)
- [router.py:75-109](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/providers/router.py#L75-L109)
- [vectorstore.py:7-8](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/rag/vectorstore.py#L7-L8)

## Performance Considerations
- Provider selection prioritizes speed (Groq) and capacity (Cerebras/Gemini) with fallbacks to reduce latency and improve reliability
- Vector search limits top_k and filters by category scopes to minimize context size
- Conversation memory uses Redis lists with TTL to cap storage and enable fast retrieval
- Speech translation runs on CUDA if available; otherwise falls back to CPU for offline capability
- Embedding scoring normalizes text and uses token overlap plus phrase bonus to balance relevance and lexical matches

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Health checks:
  - Root endpoint provides service metadata and endpoints
  - Health endpoint checks memory backend availability
- Redis connectivity:
  - ping indicates whether Redis is reachable; if not, the system operates in memory-only mode
- Provider configuration:
  - At least one LLM API key must be set; otherwise startup raises a fatal error
- Speech model dependencies:
  - Missing optional dependencies prevent speech translation; status reports availability and configuration

**Section sources**
- [main.py:106-142](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py#L106-L142)
- [redis_memory.py:67-76](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/memory/redis_memory.py#L67-L76)
- [config.py:115-126](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/config.py#L115-L126)
- [speech_translation.py:109-120](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/services/speech_translation.py#L109-L120)

## Conclusion

> **Enterprise Hardening Notes:**
> - LLM provider calls now use `asyncio.wait_for()` with configurable timeout to prevent hanging
> - Safety checker includes a 12-pattern prompt injection guard
> - Rate limiting enforced via `slowapi` on chat endpoints (5 req/min)
> - Embedding model replaced: `hash-based embeddings` → `LocalHashEmbeddingFunction` (zero ML dependency)

The AI Chatbot Service combines intent-driven orchestration, multilingual provider routing, and a local RAG pipeline to deliver responsive, context-rich assistance for legal queries, first aid, emergencies, road issues, and more. Its modular design enables easy extension of tools, providers, and retrieval strategies while maintaining resilience through automatic failover and memory fallback.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### API Endpoints
- GET /: service metadata and endpoints
- GET /health: memory backend health
- POST /api/v1/chat: chat completion
- POST /api/v1/chat/stream: streaming chat completion
- GET /api/v1/chat/history/{session_id}: retrieve chat history
- GET /api/v1/chat/health: chat engine health
- GET /speech/status: speech model status

**Section sources**
- [main.py:117-142](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/main.py#L117-L142)

### Configuration Keys
- LLM providers: GROQ_API_KEY, GOOGLE_API_KEY, OPENROUTER_API_KEY, HF_TOKEN, MISTRAL_API_KEY, SARVAM_API_KEY, NVIDIA_NIM_API_KEY, CEREBRAS_API_KEY
- Speech: SPEECH_MODEL_ID, SPEECH_MODEL_DIR, SPEECH_DEVICE, SPEECH_DEFAULT_TARGET_LANG
- Data and persistence: CHROMA_PERSIST_DIR, RAG_DATA_DIR, TOP_K_RETRIEVAL, SESSION_TTL_SECONDS
- External APIs: OPENWEATHER_API_KEY, W3W_API_KEY, OPENCAGE_API_KEY

**Section sources**
- [config.py:39-113](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/config.py#L39-L113)
- [config.py:119-125](https://github.com/SafeVixAI/SafeVixAI/blob/main/chatbot_service/config.py#L119-L125)