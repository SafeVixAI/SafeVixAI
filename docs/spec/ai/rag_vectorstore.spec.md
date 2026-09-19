# RAG System

> Version 1.0 | 2026-07-29

## RAG Query Flow

```mermaid
sequenceDiagram
    participant User as User
    participant SC as SafetyChecker
    participant ID as IntentDetector
    participant CTX as ContextAssembler
    participant Tools as Agent Tools
    participant Chroma as ChromaDB
    participant Embed as LocalHashEmbedding
    participant PR as ProviderRouter
    participant LLM as LLM Provider
    participant CMS as ConversationStore

    User->>SC: User Query
    SC->>SC: Harm/PII Detection
    SC-->>User: [Blocked] "Call 112 immediately"

    SC->>ID: Safe Query
    ID->>ID: Classify Intent (9 classes)

    alt Emergency / First Aid
        ID->>CTX: Intent + Query
        CTX->>Tools: Route to tool
        Tools->>Tools: Execute tool logic
        Tools-->>CTX: Tool results
    else Legal / Challan
        ID->>CTX: Intent + Query
        CTX->>Chroma: Vector Search Query
        Chroma->>Embed: Hash tokens to 384d vector
        Embed-->>Chroma: Embedding
        Chroma->>Chroma: Cosine Similarity Search
        Chroma-->>CTX: Top-k Chunks + Scores
    end

    CTX->>CTX: Assemble System + Tool + RAG Context
    CTX->>PR: Complete context
    PR->>PR: Check language
    PR->>LLM: Generate response (timeout=30s)
    LLM->>LLM: Inference
    LLM-->>PR: Generated text
    PR-->>CMS: Store in Redis (24h TTL)
    CMS-->>User: Final Response
```

## ChromaDB Instance Architecture

```mermaid
flowchart TD
    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b

    subgraph Chatbot_Service["Chatbot Service — :8010"]
        CS_Chroma["ChromaDB<br/>chatbot_service/data/chroma_db/"]:::data
        CS_Chroma --> CS_Commit["COMMITTED to git<br/>Render cold-start ready"]:::control
        CS_Chroma --> CS_Data["Motor Vehicles Act<br/>MoRTH Regulations<br/>First Aid Protocols<br/>Indian Traffic Law"]:::data
        CS_Chroma --> CS_Embed["LocalHashEmbeddingFunction<br/>384-dim, Zero ML Deps<br/>Deterministic Hash"]:::ai
    end

    subgraph Backend["Backend — :8000"]
        BE_Chroma["ChromaDB<br/>backend/data/chroma_db/"]:::data
        BE_Chroma --> BE_Git[".gitignored<br/>Build locally"]:::control
        BE_Chroma --> BE_Data["Civic Data<br/>Municipal Records<br/>Infrastructure Docs"]:::data
        BE_Chroma --> BE_Build["python scripts/app/build_vectorstore.py<br/>~10 min build"]:::control
    end

    UserQ["User Query"]:::edge --> Intent{"Intent"}:::decision
    Intent -->|"Legal / Law"| CS_Chroma
    Intent -->|"First Aid"| CS_Chroma
    Intent -->|"Civic / Infra"| BE_Chroma
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **LocalHashEmbeddingFunction** | Zero ML dependencies; deterministic hash ensures reproducible results |
| **384-dimensional vectors** | Sufficient for legal/medical cosine similarity at 10% storage cost vs 1536d |
| **ChromaDB committed in chatbot** | Render cold-starts would take 10min+ to rebuild; committed copy starts instantly |
| **ChromaDB gitignored in backend** | Backend has fewer cold-starts; rebuild is acceptable |
| **Cosine similarity** | Better suited for sparse legal vectors than L2 distance |

## Architecture

Two ChromaDB instances: chatbot (committed, for LegalSearch + FirstAid) and backend (gitignored, future).

## Embedding Strategy

LocalHashEmbeddingFunction: SHA-256 → 384-dim histogram → unit vector. Zero ML dependencies, ~50x faster than transformers.

## Document Sources

- Motor Vehicles Act 1988: ~200 chunks
- MoRTH guidelines: ~50 chunks
- WHO First Aid: ~150 chunks

## Build

```bash
python scripts/app/build_vectorstore.py
```
