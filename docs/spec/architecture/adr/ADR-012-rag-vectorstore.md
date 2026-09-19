# ADR-012: ChromaDB for Legal RAG Vector Store

**Date:** 2026-05-26
**Status:** ✅ Accepted
**Author:** SafeVixAI AI Team

## Context

The AI chatbot needs to answer questions about Indian traffic law (Motor Vehicles Act 2019, state regulations, MoRTH guidelines). Raw PDF documents must be searchable via semantic similarity. The vector store must:
- Run locally (no external API costs)
- Support incremental updates
- Work in the chatbot service's Python environment
- Be small enough for Render.com's 512MB memory limit

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **ChromaDB (chosen)** | Open-source embedding database | Local, persistent, simple API, small footprint | SQLite-backed (single writer), limited scaling |
| **Pinecone** | Managed vector database | Scalable, fast | $70+/month, out of budget |
| **FAISS** | Facebook's vector index | Very fast, local | No built-in persistence, harder to update incrementally |
| **pgvector** | PostgreSQL vector extension | Integrated with existing DB | Requires pgvector on Supabase, migration complexity |

## Decision

Use ChromaDB with a custom `LocalHashEmbeddingFunction`:
- 384-dimension hash-based embeddings (zero ML dependencies)
- Cosine similarity for retrieval
- Persisted to `chatbot_service/data/chroma_db/`
- TOP_K_RETRIEVAL = 5, RAG_MIN_SCORE = 0.55
- Built from PDFs: Motor Vehicles Act 2019, Central Motor Vehicles Rules, state amendments

## Consequences

- ChromaDB directory (`chatbot_service/data/chroma_db/`) is **committed to git** — Render cold-starts need pre-built index
- `backend/data/chroma_db/` is gitignored — rebuilt locally (~10 minutes)
- Custom embedding function needs no ML dependencies (torch, transformers are only for speech, not RAG)
- Retrieval speed: ~50ms per query with 500+ documents
