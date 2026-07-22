# ADR-002: 10-provider LLM Fallback Chain

**Date:** 2026-05-20  
**Status:** ✅ Accepted  
**Author:** SafeVixAI AI Team  

## Context

LLM APIs are unreliable — rate limits, outages, and latency spikes are common. The chatbot must remain operational during upstream failures.

If a single provider is chosen and it goes down, the entire chatbot becomes unavailable. For a safety application, this is unacceptable.

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Single provider** | One LLM (e.g., Groq) | Simple | Complete outage if provider down |
| **Fallback chain (chosen)** | Try providers sequentially until one succeeds | Near-zero downtime | Increased complexity |
| **Parallel fan-out** | Call all providers, return fastest | Lowest latency | Wasted API calls, cost |

## Decision

Implement a 10-provider fallback chain:

```
Groq → Cerebras → Gemini → GitHub Models → NVIDIA NIM → OpenRouter → Mistral → Together → Template
```

With a separate Indian language routing path:
- Hindi/Tamil/etc. → Sarvam-30B
- Legal queries in Indian languages → Sarvam-105B

Each provider is tried in order. If one fails (rate limit, timeout, error), the next is tried immediately.

The final fallback (`TemplateProvider`) is a deterministic, zero-dependency provider that always works — guaranteeing the chatbot never returns a blank response.

## Consequences

- ~100ms overhead per failed provider (non-blocking timeout)
- Email alert on complete chain failure (all 9 down)
- `< 0.01% chance of all 10 providers being simultaneously unavailable`
- Each provider needs its own API key in Secrets Manager
- Provider health is monitored via circuit breaker pattern
