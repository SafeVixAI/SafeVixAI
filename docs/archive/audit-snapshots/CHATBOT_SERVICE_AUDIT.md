# Chatbot Service Audit Report â€" SafeVixAI

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

**Initial Date:** 2026-05-19  
**Last Updated:** 2026-05-22  
**Scope:** `chatbot_service/` â€" FastAPI :8010 (Agentic RAG, 10 providers + Indian language pre-routing, 13 tools, ChromaDB)  
**Auditor:** Principal AI/ML Engineer & Security Auditor  
**Initial Score:** 7.5/10 (B-)  
**Current Score:** 8.5/10 (B+)

---

## Executive Summary

SafeVixAI's chatbot service is an impressive agentic RAG system with a 10-provider LLM fallback chain + Indian language pre-routing, 13 agent tools, ChromaDB vector store, Redis conversation memory, and Indian language support via Sarvam AI. The architecture demonstrates strong AI engineering: intent detection, safety checking, context assembly, parallel tool execution, and circuit breaker alerts.

**Phase 3 Enterprise Hardening delivered:**
- Circuit breakers for repeatedly failing providers
- Streaming chat via `POST /api/v1/chat/stream` (SSE)
- Conversation summarization to manage context window
- Multi-turn intent refinement (`IntentDetector.refine_intent()`)
- Smart fallback routing with confidence scores
- 244/244 tests passing (was 27 failing)
- Safety checker: l33t normalization fix (112 â†' ii2 prevented), space-inserted obfuscation detection via single-char token heuristic, prompt injection patterns
- Circular import resolved (`limiter` extracted from `main.py`)
- `FakeContextAssembler` kwargs, `FakeIntentDetector.refine_intent`, `Sarvam105BProvider.name` override fixed
- SSML/Speech language mapping for 11 Indian languages

**Strengths:** 10-provider fallback + Indian language pre-routing, Sarvam AI for Indian languages, ChromaDB RAG, Redis conversation memory, 13 agent tools, safety checker with 60+ patterns + l33t/space defense, email alerting on total failure, LLM response caching, token counting, parallel tool execution.

---

## 1. Architecture & Structure

### 1.1 Application Factory
| Component | Status | Assessment |
|-----------|--------|------------|
| `create_app()` factory | âœ... Present | âœ... Good pattern |
| Async lifespan | âœ... Present | âœ... Correct for async services |
| ChatEngine initialization | âœ... On startup | âœ... Good |
| ChromaDB loading | âœ... On startup | âš ï¸ Blocks startup if large |
| Speech model preload | âœ... Present | âœ... Via run_in_executor |
| LLM cache initialization | âœ... Present | âœ... Redis-backed |
| Service injection | âœ... Via `app.state` | âš ï¸ Not true DI |

### 1.2 Agent Pipeline
```
User message â†' SafetyChecker â†' IntentDetector â†' ContextAssembler â†' ProviderRouter â†' Response
```

| Stage | Quality | Assessment |
|-------|---------|------------|
| SafetyChecker | âœ... Excellent | 60+ patterns, jailbreak, NFKC, zero-width, l33t, output check |
| IntentDetector | âœ... Good | 9 intent classes, regex-based |
| ContextAssembler | âœ... Good | Parallel tool execution, RAG retrieval |
| ProviderRouter | âœ... Excellent | 11 providers, circuit breaker, caching |

---

## 2. AI/ML Systems

### 2.1 LLM Provider Chain
| Provider | Tier | Purpose | Status |
|----------|------|---------|--------|
| Groq | 1 | Fastest English (300+ tok/s) | âœ... Active |
| Cerebras | 1 | Speed overflow (2000+ tok/s) | âœ... Active |
| Sarvam-30B | 1 | Indian languages | âœ... Active |
| Sarvam-105B | 1 | Legal/challan Indian | âœ... Active |
| Gemini | 2 | Large context (1M tok) | âœ... Active |
| GitHub Models | 2 | Free tier | âœ... Active |
| NVIDIA NIM | 2 | GPU-optimized | âœ... Active |
| OpenRouter | 3 | Gateway to 20+ models | âœ... Active |
| Mistral | 3 | 1B tok/month free | âœ... Active |
| Together | 3 | $25 credit bank | âœ... Active |
| Template | Fallback | Deterministic | âœ... Always works |

### 2.2 CRITICAL: No AI Governance Framework
**Severity:** CRITICAL  
**Scope:** All AI outputs

**Problem:** No systematic approach to:
- Hallucination detection
- Output factuality verification
- Prompt versioning and audit trail
- Model drift monitoring
- Bias detection in responses
- Regulatory compliance (EU AI Act, India AI governance)

**Production Impact:** AI can provide incorrect emergency advice, legal guidance, or first-aid instructions without detection.

**Fix:**
1. Implement hallucination detection (cross-reference with RAG sources)
2. Add prompt versioning to ChromaDB
3. Log all prompts + responses for audit
4. Add factuality scoring to responses
5. Implement response validation against knowledge base

---

## 3. RAG Pipeline

### 3.1 Vector Store
| Component | Status | Assessment |
|-----------|--------|------------|
| ChromaDB | âœ... Present | âœ... Pre-built index committed |
| Embeddings | âš ï¸ Hash-based | âš ï¸ LocalHashEmbeddingFunction (not semantic) |
| Retrieval | âœ... Present | âœ... Scope-based filtering |
| Score threshold | âœ... Present | âœ... `min_score` config |
| Top-k | âœ... Configurable | âœ... `top_k_retrieval` |

### 3.2 HIGH: Hash-Based Embeddings
**Severity:** HIGH  
**File:** `chatbot_service/rag/embeddings.py`

**Problem:** `LocalHashEmbeddingFunction` uses hash-based 384-dim vectors, not semantic embeddings. This means similarity search is based on hash collisions, not semantic meaning.

**Production Impact:** Irrelevant documents retrieved for queries, poor response quality.

**Fix:**
1. Migrate to `SentenceTransformerEmbeddingFunction` (all-MiniLM-L6-v2)
2. Rebuild ChromaDB index with semantic embeddings
3. Add embedding model version tracking

---

## 4. Safety & Security

### 4.1 SafetyChecker
| Feature | Status | Assessment |
|---------|--------|------------|
| Pattern matching | âœ... 60+ patterns | âœ... Comprehensive |
| Jailbreak detection | âœ... 23 patterns | âœ... Good coverage |
| Unicode normalization | âœ... NFKC | âœ... Prevents homoglyph attacks |
| Zero-width stripping | âœ... Present | âœ... Prevents hidden chars |
| L33t detection | âœ... FIXED | âœ... Evaluates BOTH normalized AND non-normalized text (112 â†' ii2 prevented) |
| Space-inserted obfuscation | âœ... FIXED | âœ... Single-char token heuristic detects "h u r t s o m e o n e" |
| Output safety check | âœ... Present | âœ... Validates LLM responses |
| Medical disclaimer | âœ... Present | âœ... "Call 112 immediately" |
| Prompt injection defense | âœ... Strengthened | âœ... HIGH_STAKES_INTENTS realigned, injection patterns blocked before LLM |

### 4.2 HIGH: No Hallucination Detection
**Severity:** HIGH  
**Scope:** All LLM responses

**Problem:** No mechanism to detect when the LLM generates information not present in the RAG context or tool results.

**Production Impact:** AI can invent emergency numbers, legal sections, or first-aid procedures.

**Fix:**
1. Add citation requirement â€" every factual claim must cite a source
2. Implement NLI-based hallucination detection
3. Add confidence scoring to responses
4. Flag responses with low RAG relevance

---

## 5. Tools

### 5.1 Tool Inventory
| Tool | Purpose | Status |
|------|---------|--------|
| SosTool | Nearby emergency services | âœ... Active |
| EmergencyTool | Emergency service lookup | âœ... Active |
| ChallanTool | Fine calculation | âœ... Active |
| LegalSearchTool | ChromaDB vector search | âœ... Active |
| FirstAidTool | Static JSON protocols | âœ... Active |
| WeatherTool | OpenWeather API | âœ... Active |
| OpenMeteoTool | Open-Meteo weather | âœ... Active |
| RoadInfrastructureTool | Road contractor data | âœ... Active |
| RoadIssuesTool | Community reports | âœ... Active |
| SubmitReportTool | Submit road damage | âœ... Active |
| GeocodingTool | Photon/BigDataCloud | âœ... Active |
| DrugInfoTool | Open FDA | âœ... Active |
| What3WordsTool | Location resolution | âœ... Active |

### 5.3 âœ... RESOLVED: Tool Execution Timeout Added
**Severity:** MEDIUM â†' RESOLVED

**Resolution:** `asyncio.wait_for()` now wraps all tool calls with a configurable timeout (default 30s). ProviderRouter also implements global timeout per provider call with graceful degradation â€" failed tool returns error message to LLM which handles it gracefully.

---

## 6. Memory & Caching

### 6.1 Conversation Memory
| Feature | Status | Assessment |
|---------|--------|------------|
| Redis backend | âœ... Present | âœ... With fallback |
| In-memory fallback | âœ... LRU-lite | âœ... 500 session cap |
| Session TTL | âœ... 24 hours | âœ... Configurable |
| History retrieval | âœ... Last 20 messages | âœ... Configurable |

### 6.2 LLM Response Cache
| Feature | Status | Assessment |
|---------|--------|------------|
| Redis backend | âœ... Present | âœ... SHA-256 key |
| TTL | âœ... 1 hour | âœ... Reasonable |
| Cache key | âœ... message + intent + tools | âœ... Deterministic |
| Hit logging | âœ... Present | âœ... Visibility |

---

## 7. Testing

### 7.1 Test Coverage
| Area | Files | Tests | Coverage | Assessment |
|------|-------|-------|----------|------------|
| Safety | 4 | ~48 | ~95% | âœ... Comprehensive â€" l33t, space-inserted, prompt injection |
| Intent detection | 2 | ~36 | ~85% | âœ... Good â€" refine_intent now tested |
| Providers | 3 | ~42 | ~75% | âœ... Good â€" 11 providers covered |
| Tools | 2 | ~28 | ~65% | âš ï¸ More edge cases needed |
| Memory | 2 | ~24 | ~80% | âœ... Good |
| Context assembler | 2 | ~32 | ~85% | âœ... Good â€" FakeContextAssembler kwargs fixed |
| Speech | 1 | ~12 | ~60% | âš ï¸ Basic |
| Admin | 2 | ~22 | ~75% | âœ... Good |
| **Total** | **20+** | **244** | **~80%** | **âœ... 244/244 passing â€" up from 27 failing** |

**Phase 3 Fixes:** FakeContextAssembler kwargs, FakeIntentDetector.refine_intent, Sarvam105BProvider.name override, Settings instantiation, HIGH_STAKES_INTENTS alignment, prompt injection patterns, moved misplaced test_alerts.py. All 27 previously failing tests now pass.

---

## Chatbot Score Summary

| Area | Score | Grade |
|------|-------|-------|
| Architecture | 9/10 | A- |
| AI/ML Systems | 7/10 | B- |
| RAG Pipeline | 7/10 | B- |
| Safety | 9/10 | A- |
| Tools | 8/10 | B+ |
| Memory/Caching | 8/10 | B+ |
| Testing | 8/10 | B+ |
| **Overall** | **8.5/10** | **B+** |
