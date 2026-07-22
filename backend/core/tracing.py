# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""OpenTelemetry distributed tracing setup for SafeVixAI backend."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

if TYPE_CHECKING:
    from fastapi import FastAPI

SERVICE_NAME = "safevixai-backend"
SERVICE_VERSION = os.getenv("APP_VERSION", "dev")


def setup_tracing(app: FastAPI) -> trace.TracerProvider:
    """Initialize OpenTelemetry tracing and instrument FastAPI app."""
    resource = Resource.create(
        {
            "service.name": SERVICE_NAME,
            "service.version": SERVICE_VERSION,
            "deployment.environment": os.getenv("APP_ENV", "development"),
        }
    )

    provider = TracerProvider(resource=resource)

    # Always export to console for development
    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # OTLP exporter for production (Jaeger, Tempo, etc.)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    trace.set_tracer_provider(provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    return provider


def get_tracer(name: str = SERVICE_NAME) -> trace.Tracer:
    """Get a tracer for manual instrumentation."""
    return trace.get_tracer(name)
