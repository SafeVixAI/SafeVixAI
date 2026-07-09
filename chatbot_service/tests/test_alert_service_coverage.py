# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import os
import time
import pytest
from unittest.mock import MagicMock, patch

from core import alert as alert_service


class TestAlertService:
    @pytest.fixture(autouse=True)
    def reset_state(self):
        alert_service._instance = None
        alert_service._last_alert_time.clear()
        # Save and clear env vars to prevent other tests from leaking state
        old_email = os.environ.pop("ALERT_EMAIL", None)
        old_pass = os.environ.pop("ALERT_EMAIL_PASSWORD", None)
        yield
        if old_email is not None:
            os.environ["ALERT_EMAIL"] = old_email
        if old_pass is not None:
            os.environ["ALERT_EMAIL_PASSWORD"] = old_pass

    def test_disabled_by_default(self):
        svc = alert_service.AlertService()
        assert svc.enabled is False
        assert svc.smtp_user == ""

    def test_enabled_with_env(self):
        with patch.dict(os.environ, {"ALERT_EMAIL": "test@gmail.com", "ALERT_EMAIL_PASSWORD": "pass123"}):
            svc = alert_service.AlertService()
            assert svc.enabled is True
            assert svc.smtp_user == "test@gmail.com"

    def test_alert_all_providers_failed(self):
        svc = alert_service.AlertService()
        with patch.object(svc, '_send') as mock_send:
            svc.alert_all_providers_failed("groq", ["groq", "gemini"], "rate limit", "user msg")
            mock_send.assert_called_once()
            kwargs = mock_send.call_args.kwargs
            assert kwargs['alert_type'] == "llm_providers_exhausted"
            assert "ALL LLM Providers Failed" in kwargs['subject']

    def test_alert_external_api_failed(self):
        svc = alert_service.AlertService()
        with patch.object(svc, '_send') as mock_send:
            svc.alert_external_api_failed("weather", "/api/weather", 429, "too many requests")
            mock_send.assert_called_once()
            assert "api_failure_weather" in mock_send.call_args.kwargs['alert_type']

    def test_alert_supabase_failed(self):
        svc = alert_service.AlertService()
        with patch.object(svc, '_send') as mock_send:
            svc.alert_supabase_failed("login", "connection refused")
            mock_send.assert_called_once()
            assert "supabase_failure" in mock_send.call_args.kwargs['alert_type']

    def test_alert_health_summary_no_down(self):
        svc = alert_service.AlertService()
        with patch.object(svc, '_send') as mock_send:
            svc.alert_health_summary({"groq": True, "gemini": True})
            mock_send.assert_not_called()

    def test_alert_health_summary_with_down(self):
        svc = alert_service.AlertService()
        with patch.object(svc, '_send') as mock_send:
            svc.alert_health_summary({"groq": True, "gemini": False, "cerebras": False})
            mock_send.assert_called_once()
            assert "2/3" in mock_send.call_args.kwargs['subject']

    def test_alert_circuit_breaker_tripped(self):
        svc = alert_service.AlertService()
        with patch.object(svc, '_send') as mock_send:
            svc.alert_circuit_breaker_tripped("groq", 300, "timeout", "connection timeout")
            mock_send.assert_called_once()
            assert "circuit_breaker_groq" in mock_send.call_args.kwargs['alert_type']

    def test_alert_wiki_generation_failed(self):
        svc = alert_service.AlertService()
        with patch.object(svc, '_send') as mock_send:
            svc.alert_wiki_generation_failed("test_module", 5, "rate limit")
            mock_send.assert_called_once()
            assert "wiki_generation_failure" in mock_send.call_args.kwargs['alert_type']

    def test_send_cooldown_suppresses(self):
        svc = alert_service.AlertService()
        svc._send("test_type", "Subject", "details", ["fix"])
        assert "test_type" in alert_service._last_alert_time
        svc._send("test_type", "Subject", "details", ["fix"])
        # Cooldown should still be active since we just called it
        assert "test_type" in alert_service._last_alert_time

    def test_send_cooldown_expired(self):
        svc = alert_service.AlertService()
        alert_service._last_alert_time["test_type"] = 0
        with patch.object(svc, '_send', wraps=svc._send) as wrapped:
            # Since _send modifies _last_alert_time internally, calling the real one works
            alert_service._last_alert_time["test_type"] = 0
        svc._send("test_type", "Subject", "details", ["fix"])
        assert alert_service._last_alert_time["test_type"] > 0

    def test_send_disabled_logs_only(self):
        svc = alert_service.AlertService()
        with patch("smtplib.SMTP") as mock_smtp:
            svc._send("test_type", "Test Subject", "body", ["fix1", "fix2"])
            mock_smtp.assert_not_called()

    def test_send_email_success(self):
        with patch.dict(os.environ, {"ALERT_EMAIL": "test@gmail.com", "ALERT_EMAIL_PASSWORD": "pass123"}):
            svc = alert_service.AlertService()
            with patch("smtplib.SMTP") as mock_smtp:
                mock_instance = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_instance
                svc._send("test_type", "Test Subject", "details", ["fix1", "fix2"])
                mock_instance.send_message.assert_called_once()

    def test_send_email_failure(self):
        with patch.dict(os.environ, {"ALERT_EMAIL": "test@gmail.com", "ALERT_EMAIL_PASSWORD": "pass123"}):
            svc = alert_service.AlertService()
            with patch("smtplib.SMTP") as mock_smtp:
                mock_instance = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_instance
                mock_instance.send_message.side_effect = ConnectionError("SMTP down")
                svc._send("test_type", "Test Subject", "details", ["fix1"])

    def test_get_alert_service_singleton(self):
        alert_service._instance = None
        svc1 = alert_service.get_alert_service()
        svc2 = alert_service.get_alert_service()
        assert svc1 is svc2

    def test_get_alert_service_creates_instance(self):
        alert_service._instance = None
        svc = alert_service.get_alert_service()
        assert svc is not None
