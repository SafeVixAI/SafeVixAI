# RAG System
> Version 1.0 | 2026-07-25

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
cd chatbot_service && python rag/build_vectorstore.py
```
