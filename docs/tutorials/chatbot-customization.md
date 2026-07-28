# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

# Tutorial: Customize the AI Chatbot

**Time required:** 15 minutes
**Prerequisites:** Running chatbot service, at least one LLM provider API key

## Step 1: Configure LLM Providers

Edit `chatbot_service/.env`:

```env
DEFAULT_LLM_PROVIDER=groq
DEFAULT_LLM_MODEL=llama-3.1-70b-versatile
GROQ_API_KEY=gsk_your_key_here
```

Supported providers: groq, gemini, cerebras, github, mistral, together, openrouter, nvidia, sarvam

Each provider requires its own API key in `.env`.

## Step 2: Add a Custom Tool

Tools are located in `chatbot_service/tools/`. To create a new tool:

1. Create a new Python file, e.g., `tools/example_tool.py`
2. Implement the tool following the existing pattern:
   - Accept configuration in `__init__`
   - Provide an async `run()` method that returns a dict
3. Register the tool in `agent/context_assembler.py`

## Step 3: Tune Safety Settings

Edit `chatbot_service/agent/safety_checker.py` to adjust:
- Harm category thresholds (sensitivity levels)
- Allowed and disallowed topics
- Emergency detection configuration

## Step 4: Rebuild the RAG Index

```bash
cd chatbot_service
python -m scripts.build_vectorstore
```

This processes all legal documents and builds the ChromaDB vectorstore for semantic search.

## Verification

- Chatbot responds using your configured provider
- Custom tool output appears in responses for matching intents
- Safety blocks work as expected for prohibited queries
- RAG retrieval returns relevant document chunks

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No LLM provider configured" | Set at least one API key in `.env` |
| RAG search returns empty | Rebuild vectorstore with `python -m scripts.build_vectorstore` |
| Custom tool not called | Check tool registration in `context_assembler.py` and intent detection |
| Provider fallback chain exhausted | Verify API key validity and rate limits for each provider |
