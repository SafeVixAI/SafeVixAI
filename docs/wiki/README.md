# SafeVixAI Repository Wiki

> **Auto-synced** from `.qoder/repowiki/en/` via GitHub Actions

This folder contains the complete repository wiki — 104 documentation files organized by module, covering every aspect of the SafeVixAI platform.

## Structure

```
docs/wiki/
├── content/                          # 104 markdown documentation files
│   ├── AI Chatbot Service/           # Agentic RAG chatbot (9 files)
│   ├── API Reference/                # REST API endpoints (8 files)
│   ├── Data Management/              # Vector store, data pipelines (6 files)
│   ├── Database Schema/              # PostgreSQL + PostGIS models (8 files)
│   ├── Emergency Locator Module/     # GPS, SOS, emergency services (7 files)
│   ├── Frontend Application/         # Next.js PWA + components (13 files)
│   ├── Performance Optimization/     # Caching, AI inference (6 files)
│   ├── Project Overview/             # Architecture, tech stack (29 files)
│   ├── Road Reporter (RoadWatch)/    # Community road reporting (6 files)
│   ├── System Architecture/          # Microservices, data flow (5 files)
│   ├── Contributing Guidelines.md
│   ├── Deployment and CI_CD.md
│   ├── Getting Started.md
│   ├── Offline Architecture.md
│   ├── Performance Optimization.md
│   ├── Security and Authentication.md
│   └── Testing Strategy.md
├── meta/
│   └── repowiki-metadata.json        # Catalog with prompts + dependencies
└── README.md                         # This file
```

## How It Works

1. **Source of truth**: `.qoder/repowiki/en/` (generated + manually refined)
2. **Sync**: GitHub Actions workflow runs on push → copies to `docs/wiki/`
3. **Staleness detection**: Workflow compares codebase against wiki, flags undocumented files

## Key Facts (Ground Truth)

| Metric | Value |
|---|---|
| LLM Providers | 9 real + Template (deterministic fallback) — Groq, Gemini, Cerebras, Mistral, NVIDIA NIM, Sarvam AI, Together AI, GitHub Models, OpenRouter |
| Chatbot Tools | 13 |
| Intent Classes | 9 |
| Embedding Model | LocalHashEmbeddingFunction (zero-dependency) |
| Features | 25/25 COMPLETE |
| Unit Tests | 2829 total (1365 backend + 892 chatbot + 572 frontend) |
| Frontend Components | 91 components across 13 subdirs |
| Frontend Routes | 28 routes (app router) |
| API Route Modules | 27 (backend + chatbot) |
| Rate Limiting | slowapi — General 100/min, Auth 5/min, SOS 3/min, Challan 60/min, Chat 30/min, Geocode 30/min |
| Auth | Supabase Auth (HS256 JWT) |
| GH Actions Workflows | 19 CI/CD workflows |
| HuggingFace Dataset Hub | [SafeVixAI/SafeVixAI-Dataset-Hub](https://huggingface.co/datasets/SafeVixAI/SafeVixAI-Dataset-Hub) |
