# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI


@pytest.fixture(autouse=True)
def _mock_all_telemetry_deps():
    orig = dict(sys.modules)
    grpc_mod = MagicMock()
    http_mod = MagicMock()
    instr_mod = MagicMock()
    sys.modules["opentelemetry.exporter.otlp.proto.grpc.trace_exporter"] = grpc_mod
    sys.modules["opentelemetry.exporter.otlp.proto.http.trace_exporter"] = http_mod
    sys.modules["opentelemetry.instrumentation.fastapi"] = instr_mod

    yield
    sys.modules.update(orig)


class TestSetupTelemetry:
    def test_grpc_exporter_path(self):
        app = MagicMock(spec=FastAPI)
        with patch("core.telemetry.TracerProvider") as mock_tp:
            with patch("core.telemetry.BatchSpanProcessor") as mock_bsp:
                with patch("core.telemetry.FastAPIInstrumentor") as mock_inst:
                    from core.telemetry import setup_telemetry

                    setup_telemetry(app)

        grpc_mod = sys.modules["opentelemetry.exporter.otlp.proto.grpc.trace_exporter"]
        grpc_mod.OTLPSpanExporter.assert_called_once()
        mock_tp.assert_called_once()
        mock_bsp.assert_called_once()
        mock_inst.instrument_app.assert_called_once_with(app)

    def test_http_fallback_when_grpc_missing(self):
        app = MagicMock(spec=FastAPI)
        sys.modules["opentelemetry.exporter.otlp.proto.grpc.trace_exporter"] = None
        with patch("core.telemetry.TracerProvider") as mock_tp:
            with patch("core.telemetry.BatchSpanProcessor") as mock_bsp:
                with patch("core.telemetry.FastAPIInstrumentor") as mock_inst:
                    from core.telemetry import setup_telemetry

                    setup_telemetry(app)

        http_mod = sys.modules["opentelemetry.exporter.otlp.proto.http.trace_exporter"]
        http_mod.OTLPSpanExporter.assert_called_once()
        mock_tp.assert_called_once()
        mock_bsp.assert_called_once()
        mock_inst.instrument_app.assert_called_once_with(app)

    def test_console_fallback_when_all_otlp_missing(self):
        app = MagicMock(spec=FastAPI)
        sys.modules["opentelemetry.exporter.otlp.proto.grpc.trace_exporter"] = None
        sys.modules["opentelemetry.exporter.otlp.proto.http.trace_exporter"] = None
        with patch("core.telemetry.TracerProvider") as mock_tp:
            with patch("core.telemetry.BatchSpanProcessor") as mock_bsp:
                with patch("core.telemetry.FastAPIInstrumentor") as mock_inst:
                    with patch("opentelemetry.sdk.trace.export.ConsoleSpanExporter") as mock_console:
                        from core.telemetry import setup_telemetry

                        setup_telemetry(app)

                        mock_console.assert_called_once()
                        mock_tp.assert_called_once()
                        mock_bsp.assert_called_once()
                        mock_inst.instrument_app.assert_called_once_with(app)

    def test_service_name_passed_to_resource(self):
        app = MagicMock(spec=FastAPI)
        with patch("core.telemetry.TracerProvider") as mock_tp:
            with patch("core.telemetry.BatchSpanProcessor"):
                with patch("core.telemetry.FastAPIInstrumentor"):
                    from core.telemetry import setup_telemetry

                    setup_telemetry(app, service_name="my-custom-service")

                    resource = mock_tp.call_args[1]["resource"]
                    assert resource.attributes["service.name"] == "my-custom-service"

    def test_logs_success_message(self):
        app = MagicMock(spec=FastAPI)
        with patch("core.telemetry.TracerProvider"):
            with patch("core.telemetry.BatchSpanProcessor"):
                with patch("core.telemetry.FastAPIInstrumentor"):
                    with patch("core.telemetry.logger") as mock_log:
                        from core.telemetry import setup_telemetry

                        setup_telemetry(app)
                        mock_log.info.assert_called_once()

    def test_exception_handled_gracefully(self):
        app = MagicMock(spec=FastAPI)
        with patch(
            "core.telemetry.TracerProvider",
            side_effect=RuntimeError("OTEL failed"),
        ), patch("core.telemetry.logger") as mock_log:
            from core.telemetry import setup_telemetry

            setup_telemetry(app)
            mock_log.warning.assert_called_once()

    def test_default_service_name(self):
        app = MagicMock(spec=FastAPI)
        with patch("core.telemetry.TracerProvider") as mock_tp:
            with patch("core.telemetry.BatchSpanProcessor"):
                with patch("core.telemetry.FastAPIInstrumentor"):
                    from core.telemetry import setup_telemetry

                    setup_telemetry(app)

                    resource = mock_tp.call_args[1]["resource"]
                    assert resource.attributes["service.name"] == "safevixai-backend"

    def test_provider_add_span_processor_called(self):
        app = MagicMock(spec=FastAPI)
        with patch("core.telemetry.TracerProvider") as mock_tp:
            with patch("core.telemetry.BatchSpanProcessor") as mock_bsp:
                with patch("core.telemetry.FastAPIInstrumentor"):
                    from core.telemetry import setup_telemetry

                    setup_telemetry(app)

                    mock_tp_instance = mock_tp.return_value
                    mock_tp_instance.add_span_processor.assert_called_once_with(
                        mock_bsp.return_value
                    )
