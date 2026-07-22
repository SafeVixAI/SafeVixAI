# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

# DEPRECATED: Use core.tracing.setup_tracing() instead. Will be removed in v4.0.

import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

def setup_telemetry(app: FastAPI, service_name: str = "safevixai-backend") -> None:
    """
    Sets up OpenTelemetry tracing for the FastAPI application.
    """
    try:
        # Check if OTLP exporter is available, fallback to Console
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter()
        except ImportError:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter()
            except ImportError:
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                exporter = ConsoleSpanExporter()

        resource = Resource.create(attributes={"service.name": service_name})
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        # Instrument the app
        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry tracing initialized for %s", service_name)
    except Exception as e:
        logger.warning("Failed to initialize OpenTelemetry tracing: %s", e)
