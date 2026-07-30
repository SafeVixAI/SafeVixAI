# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Prometheus business metrics for SafeVixAI backend."""
from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Shared registry (use default registry for simplicity)
REGISTRY = CollectorRegistry(auto_describe=True)

# ── SOS Metrics ──────────────────────────────────────────────────────────────
sos_dispatch_total = Counter(
    "sos_dispatch_total",
    "Total number of SOS dispatches",
    ["status", "mode"],  # status: success/failed/queued, mode: online/offline
    registry=REGISTRY,
)

sos_response_time = Histogram(
    "sos_response_time_seconds",
    "Time taken to process SOS dispatch",
    registry=REGISTRY,
)

# ── Emergency Service Metrics ────────────────────────────────────────────────
emergency_lookup_total = Counter(
    "emergency_lookup_total",
    "Total number of emergency service lookups",
    ["service_type", "source"],  # service_type: hospital/police/ambulance, source: overpass/cache
    registry=REGISTRY,
)

emergency_lookup_time = Histogram(
    "emergency_lookup_time_seconds",
    "Time taken to lookup emergency services",
    ["service_type"],
    registry=REGISTRY,
)

emergency_services_found = Gauge(
    "emergency_services_found",
    "Number of emergency services found in radius",
    ["service_type", "radius_meters"],
    registry=REGISTRY,
)

# ── Live Tracking Metrics ────────────────────────────────────────────────────
tracking_sessions_active = Gauge(
    "tracking_sessions_active",
    "Number of active live tracking sessions",
    registry=REGISTRY,
)

tracking_session_total = Counter(
    "tracking_session_total",
    "Total number of tracking sessions created",
    ["status"],  # status: created/expired/stopped
    registry=REGISTRY,
)

tracking_update_total = Counter(
    "tracking_update_total",
    "Total number of location updates received",
    ["status"],  # status: success/failure
    registry=REGISTRY,
)

# ── Chatbot Metrics ──────────────────────────────────────────────────────────
chatbot_request_total = Counter(
    "chatbot_request_total",
    "Total number of chatbot requests",
    ["intent", "provider", "status"],  # status: success/fallback/failed
    registry=REGISTRY,
)

chatbot_response_time = Histogram(
    "chatbot_response_time_seconds",
    "Time taken for chatbot to generate response",
    ["provider"],
    registry=REGISTRY,
)

chatbot_fallback_total = Counter(
    "chatbot_fallback_total",
    "Total number of LLM provider fallbacks",
    ["from_provider", "to_provider"],
    registry=REGISTRY,
)

# ── Challan Metrics ──────────────────────────────────────────────────────────
challan_calculation_total = Counter(
    "challan_calculation_total",
    "Total number of challan calculations",
    ["violation_code", "source"],  # source: duckdb/llm
    registry=REGISTRY,
)

challan_calculation_time = Histogram(
    "challan_calculation_time_seconds",
    "Time taken to calculate challan",
    registry=REGISTRY,
)

# ── API Health Metrics ───────────────────────────────────────────────────────
api_request_total = Counter(
    "api_request_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

api_request_time = Histogram(
    "api_request_time_seconds",
    "Time taken to process API request",
    ["method", "endpoint"],
    registry=REGISTRY,
)

# ── Database Metrics ─────────────────────────────────────────────────────────
db_query_time = Histogram(
    "db_query_time_seconds",
    "Time taken for database queries",
    ["operation"],  # operation: select/insert/update/delete
    registry=REGISTRY,
)

db_connection_pool_size = Gauge(
    "db_connection_pool_size",
    "Current database connection pool size",
    registry=REGISTRY,
)

# ── Cache Metrics ────────────────────────────────────────────────────────────
cache_hit_total = Counter(
    "cache_hit_total",
    "Total number of cache hits",
    ["cache_type"],  # cache_type: redis/memory
    registry=REGISTRY,
)

cache_miss_total = Counter(
    "cache_miss_total",
    "Total number of cache misses",
    ["cache_type"],
    registry=REGISTRY,
)

# ── WebSocket Connection Metrics ──────────────────────────────────────────────
ws_connections_total = Gauge(
    "ws_connections_total",
    "Current number of active WebSocket connections",
    ["group"],
    registry=REGISTRY,
)

# ── Issue Report Metrics ─────────────────────────────────────────────────────
issue_reports_total = Counter(
    "issue_reports_total",
    "Total number of issue reports created",
    ["issue_type", "category"],
    registry=REGISTRY,
)

issue_sla_breaches_total = Counter(
    "issue_sla_breaches_total",
    "Total number of SLA breaches",
    registry=REGISTRY,
)

issue_duplicates_detected = Counter(
    "issue_duplicates_detected",
    "Total number of duplicate issues detected",
    registry=REGISTRY,
)

issue_spam_detected = Counter(
    "issue_spam_detected",
    "Total number of spam issues detected",
    registry=REGISTRY,
)

# ── Circuit Breaker Metrics ──────────────────────────────────────────────────
circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
    ["name"],
    registry=REGISTRY,
)

circuit_breaker_calls_total = Counter(
    "circuit_breaker_calls_total",
    "Total calls through circuit breaker",
    ["name", "result"],
    registry=REGISTRY,
)

circuit_breaker_failure_total = Counter(
    "circuit_breaker_failure_total",
    "Total failures tracked by circuit breaker",
    ["name", "failure_type"],
    registry=REGISTRY,
)


def update_circuit_breaker_metrics():
    from core.circuit_breaker import CircuitBreakerRegistry
    state_map = {"closed": 0, "open": 1, "half_open": 2}
    stats = CircuitBreakerRegistry.all_stats()
    set(stats)

    for name, data in stats.items():
        circuit_breaker_state.labels(name=name).set(state_map.get(data["state"], 0))
        circuit_breaker_calls_total.labels(name=name, result="success").inc(0)
        circuit_breaker_calls_total.labels(name=name, result="failure").inc(0)
        circuit_breaker_failure_total.labels(name=name, failure_type="exception").inc(0)


# ── Helper Functions ─────────────────────────────────────────────────────────
def metrics_response():
    """Generate Prometheus metrics response."""
    update_circuit_breaker_metrics()
    return generate_latest(REGISTRY)


def metrics_content_type():
    """Get Prometheus metrics content type."""
    return CONTENT_TYPE_LATEST
