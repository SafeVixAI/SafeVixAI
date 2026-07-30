# Runbook: ChromaDB Index Rebuild

> **SNAPSHOT**: This document reflects the state as of its creation date. For current state see [AGENTS.md](../../AGENTS.md).

**Severity:** SEV2 | **Service:** Chatbot | **Time to execute:** 10-30 minutes

## When to rebuild
- RAG returning irrelevant results
- New documents added to knowledge base
- Index corruption detected
- After embedding model change

## Steps

### 1. Stop chatbot service
```bash
docker compose stop chatbot
# Or Render dashboard → Stop service
```

### 2. Backup existing index (optional but recommended)
```bash
cd chatbot_service
cp -r data/chroma_db data/chroma_db_backup_$(date +%Y%m%d)
```

### 3. Rebuild via admin endpoint
```bash
# With admin key
curl -X POST http://localhost:8010/api/v1/admin/rebuild-index \
  -H "X-Admin-Key: $ADMIN_SECRET"
```

### 4. Or rebuild via script
```bash
cd chatbot_service
python data/build_vectorstore.py
```

### 5. Verify rebuild
```bash
curl http://localhost:8010/api/v1/admin/health \
  -H "X-Admin-Key: $ADMIN_SECRET"
# Check chunk count matches expected
```

### 6. Restart and test
```bash
docker compose start chatbot
# Test with a known query
curl -X POST http://localhost:8010/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the fine for drunk driving?"}'
```

## Notes
- Rebuild takes ~10 minutes for full index
- Chatbot is unavailable during rebuild
- Ensure `data/` directory has sufficient disk space
- If using sentence-transformers, model download adds ~22MB
