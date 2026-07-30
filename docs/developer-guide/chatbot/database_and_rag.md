# Database Schema and Management

The chatbot service doesn't have its own primary database but interacts with three critical systems: PostgreSQL (PostGIS), Redis, and ChromaDB.

```mermaid
flowchart TB
    subgraph Chatbot["Chatbot Service :8010"]
        CT[ChatEngine Tools]
    end

    subgraph DB["Data Systems"]
        PG["PostgreSQL + PostGIS<br/>Emergency services, road issues"]
        RS["Redis<br/>Conversation memory, provider health"]
        CB["ChromaDB<br/>RAG vectorstore"]
    end

    CT -->|"Query emergency/road data"| PG
    CT -->|"Read/write session + health"| RS
    CT -->|"Vector search MV Act, first aid"| CB

    PG -->|"LISTEN/NOTIFY"| RS

    style Chatbot fill:#9e6a03,color:#fff
    style PG fill:#1f6feb,color:#fff
    style RS fill:#da3633,color:#fff
    style CB fill:#238636,color:#fff
```

## PostgreSQL (with PostGIS)
- **Functions**: Stores and queries spatial data for emergency services and road issues.
- **Tools**:
  - `emergency_tool.py`: Queries nearby hospitals, police stations, etc.
  - `road_issues_tool.py`: Queries recent community-reported potholes and road closures.
- **Triggers**: PostgreSQL `LISTEN/NOTIFY` used to push real-time road events to the chatbot via Redis.

## Redis (for Session Memory)
- **Functions**: Stores the conversation history for every user session.
- **Configuration**:
  - `TTL`: Conversations are stored for 24 hours (86400s).
  - `Memory`: Each session tracks the last 6 turns of the conversation.
- **Provider Health Cache**: Tracks the current health status and rate limits of each LLM provider.

## ChromaDB (Vectorstore)
- **Functions**: Serves as the indexed knowledge base for RAG (Retrieval-Augmented Generation).
- **Setup**:
  - `Documents`: Motor Vehicles Act (1988, 2019), WHO Guidelines, state amendments.
  - `Embeddings`: Using `LocalHashEmbeddingFunction` — zero-dep hash-based 384-dim vectors. No ML libraries needed.
  - `Storage`: Stored on disk in `chatbot_service/data/chroma_db/` — **committed to git** (Render needs it).
- **Management**: Rebuilt locally via `python data/build_vectorstore.py` when new PDFs are added. Commit the updated `chroma_db/` directory.
- **RAG config**: `top_k=5`, `min_score=0.55`
- **Legal PDFs**: `chatbot_service/data/legal/`
- **Medical PDFs**: `chatbot_service/data/medical/`
