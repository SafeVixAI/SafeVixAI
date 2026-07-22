# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import patch

from core.metrics import (
    CONTENT_TYPE_LATEST,
    metrics_content_type,
    metrics_response,
)


class TestMetricsResponse:
    def test_metrics_content_type(self):
        result = metrics_content_type()
        assert result == CONTENT_TYPE_LATEST

    def test_metrics_response_calls_update_and_generates(self):
        with patch("core.metrics.update_circuit_breaker_metrics") as mock_update:
            with patch("core.metrics.generate_latest") as mock_generate:
                mock_generate.return_value = b"prometheus_metric 1.0"
                result = metrics_response()
        mock_update.assert_called_once()
        mock_generate.assert_called_once()
        assert result == b"prometheus_metric 1.0"

    def test_update_circuit_breaker_metrics_runs(self):
        with patch("core.circuit_breaker.CircuitBreakerRegistry") as mock_registry:
            mock_registry.all_stats.return_value = {
                "cb_redis": {
                    "state": "closed",
                    "failure_count": 0,
                    "last_failure_time": None,
                },
            }
            from core.metrics import update_circuit_breaker_metrics
            update_circuit_breaker_metrics()
            mock_registry.all_stats.assert_called_once()
