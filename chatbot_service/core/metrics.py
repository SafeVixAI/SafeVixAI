# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

REGISTRY = CollectorRegistry(auto_describe=True)

chatbot_request_total = Counter(
    "chatbot_request_total",
    "Total chatbot requests by intent, provider, and status",
    ["intent", "provider", "status"],
    registry=REGISTRY,
)

chatbot_response_time = Histogram(
    "chatbot_response_time_seconds",
    "Time to generate chatbot response by provider",
    ["provider"],
    registry=REGISTRY,
)

chatbot_fallback_total = Counter(
    "chatbot_fallback_total",
    "LLM provider fallback count (from→to)",
    ["from_provider", "to_provider"],
    registry=REGISTRY,
)

chatbot_safety_block_total = Counter(
    "chatbot_safety_block_total",
    "Total safety blocks triggered",
    ["reason"],
    registry=REGISTRY,
)

chatbot_rag_retrieval_time = Histogram(
    "chatbot_rag_retrieval_time_seconds",
    "Time taken for RAG document retrieval",
    registry=REGISTRY,
)

chatbot_memory_operation_time = Histogram(
    "chatbot_memory_operation_time_seconds",
    "Time taken for conversation memory operations",
    ["operation"],
    registry=REGISTRY,
)

api_request_total = Counter(
    "api_request_total",
    "Total API requests by method, endpoint, status",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

api_request_time = Histogram(
    "api_request_time_seconds",
    "Time to process API requests",
    ["method", "endpoint"],
    registry=REGISTRY,
)

speech_translate_total = Counter(
    "speech_translate_total",
    "Total speech translation requests by status",
    ["status"],
    registry=REGISTRY,
)

speech_translate_time = Histogram(
    "speech_translate_time_seconds",
    "Time for speech translation",
    registry=REGISTRY,
)

chatbot_circuit_breaker_state = Gauge(
    "chatbot_circuit_breaker_state",
    "Chatbot provider circuit breaker state (0=available, 1=unavailable)",
    ["provider"],
    registry=REGISTRY,
)

chatbot_circuit_breaker_trips_total = Counter(
    "chatbot_circuit_breaker_trips_total",
    "Total circuit breaker trips by provider",
    ["provider", "error_type"],
    registry=REGISTRY,
)

chatbot_rag_cache_hit = Counter(
    "chatbot_rag_cache_hit_total",
    "Total RAG cache hits",
    registry=REGISTRY,
)

chatbot_rag_cache_miss = Counter(
    "chatbot_rag_cache_miss_total",
    "Total RAG cache misses",
    registry=REGISTRY,
)

chatbot_token_cost_total = Counter(
    "chatbot_token_cost_total",
    "Total LLM token usage and estimated cost by provider",
    ["provider", "model", "token_type"],
    registry=REGISTRY,
)

# Cost per 1K tokens in USD (approximate market rates as of 2026-07)
_PROVIDER_COST_PER_1K: dict[str, dict[str, float]] = {
    "groq": {"input": 0.00015, "output": 0.0006},
    "gemini": {"input": 0.000075, "output": 0.0003},
    "cerebras": {"input": 0.0001, "output": 0.0004},
    "openrouter": {"input": 0.0002, "output": 0.0008},
    "mistral": {"input": 0.00015, "output": 0.0006},
    "together": {"input": 0.0002, "output": 0.0008},
    "github": {"input": 0.00015, "output": 0.0006},
    "nvidia": {"input": 0.0001, "output": 0.0004},
    "sarvam_30b": {"input": 0.0003, "output": 0.0012},
    "sarvam_105b": {"input": 0.0005, "output": 0.0020},
    "template": {"input": 0.0, "output": 0.0},
}


def record_token_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Record token usage and estimated cost as Prometheus counters."""
    chatbot_token_cost_total.labels(
        provider=provider, model=model, token_type="prompt",
    ).inc(prompt_tokens)
    chatbot_token_cost_total.labels(
        provider=provider, model=model, token_type="completion",
    ).inc(completion_tokens)
    chatbot_token_cost_total.labels(
        provider=provider, model=model, token_type="total",
    ).inc(prompt_tokens + completion_tokens)


def update_circuit_breaker_gauges(unavailable_providers: set[str], all_providers: list[str]) -> None:
    for provider in all_providers:
        chatbot_circuit_breaker_state.labels(provider=provider).set(
            1 if provider in unavailable_providers else 0
        )


def metrics_response():
    return generate_latest(REGISTRY)


def metrics_content_type():
    return CONTENT_TYPE_LATEST
