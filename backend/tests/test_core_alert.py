# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import os
import time
from unittest.mock import MagicMock, call, patch

import pytest

from core.alert import (
    ALERT_COOLDOWN_SECONDS,
    AlertService,
    _last_alert_time,
    get_alert_service,
)


@pytest.fixture(autouse=True)
def reset_alert_state():
    _last_alert_time.clear()
    yield


@pytest.fixture
def alert_service():
    return AlertService()


def test_init_enabled():
    with patch.dict(os.environ, {"ALERT_EMAIL": "test@example.com", "ALERT_EMAIL_PASSWORD": "secret"}, clear=True):
        svc = AlertService()
        assert svc.enabled is True
        assert svc.smtp_user == "test@example.com"
        assert svc.alert_to == "test@example.com"


def test_init_disabled():
    with patch.dict(os.environ, {}, clear=True):
        svc = AlertService()
        assert svc.enabled is False


def test_init_custom_recipient():
    with patch.dict(os.environ, {"ALERT_EMAIL": "a@b.com", "ALERT_EMAIL_PASSWORD": "p", "ALERT_EMAIL_TO": "c@d.com"}, clear=True):
        svc = AlertService()
        assert svc.alert_to == "c@d.com"


def test_send_cooldown_suppresses_duplicate(alert_service):
    with patch("core.alert.logger") as mock_logger:
        alert_service._send("test_type", "Subj", "Details", ["Fix 1"])
        assert mock_logger.warning.call_count == 1
        alert_service._send("test_type", "Subj", "Details", ["Fix 1"])
        assert mock_logger.warning.call_count == 1


def test_send_different_types_no_cooldown(alert_service):
    with patch("core.alert.logger") as mock_logger:
        alert_service._send("type_a", "Subj", "Det", ["Fix"])
        alert_service._send("type_b", "Subj", "Det", ["Fix"])
        assert mock_logger.warning.call_count == 2


def test_send_after_cooldown_expired(alert_service):
    with patch("core.alert.logger") as mock_logger:
        alert_service._send("t", "S", "D", ["F"])
        _last_alert_time["t"] = time.time() - ALERT_COOLDOWN_SECONDS - 1
        alert_service._send("t", "S", "D", ["F"])
        assert mock_logger.warning.call_count == 2


def test_send_email_success():
    with patch.dict(os.environ, {"ALERT_EMAIL": "a@b.com", "ALERT_EMAIL_PASSWORD": "p"}, clear=True):
        svc = AlertService()
        with patch("core.alert.smtplib.SMTP") as mock_smtp:
            mock_instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_instance
            svc._send("test", "Subject", "Details here", ["Fix 1", "Fix 2"])
            mock_instance.starttls.assert_called_once()
            mock_instance.login.assert_called_once_with("a@b.com", "p")
            mock_instance.send_message.assert_called_once()


def test_send_email_failure_logged():
    with patch.dict(os.environ, {"ALERT_EMAIL": "a@b.com", "ALERT_EMAIL_PASSWORD": "p"}, clear=True):
        svc = AlertService()
        with patch("core.alert.smtplib.SMTP", side_effect=Exception("Connection refused")):
            with patch("core.alert.logger") as mock_logger:
                svc._send("test", "Subj", "Det", ["Fix"])
                mock_logger.error.assert_called_once()


def test_send_disabled_logs_only(alert_service):
    assert alert_service.enabled is False
    with patch("core.alert.logger") as mock_logger:
        svc = AlertService()
        svc._send("test", "Subj", "Det", ["Fix"])
        mock_logger.info.assert_any_call("Email not configured. Alert printed to logs only.")


def test_alert_all_providers_failed(alert_service):
    with patch.object(alert_service, "_send") as mock_send:
        alert_service.alert_all_providers_failed("groq", ["groq", "gemini"], "Rate limit", "help me")
        mock_send.assert_called_once_with(
            alert_type="llm_providers_exhausted",
            subject="ALL LLM Providers Failed",
            details=mock_send.call_args[1]["details"],
            solutions=mock_send.call_args[1]["solutions"],
        )
        kwargs = mock_send.call_args[1]
        assert kwargs["alert_type"] == "llm_providers_exhausted"
        assert "ALL LLM Providers Failed" in kwargs["subject"]
        assert "groq" in kwargs["details"]


def test_alert_external_api_failed(alert_service):
    with patch.object(alert_service, "_send") as mock_send:
        alert_service.alert_external_api_failed("openweather", "/weather", 429, "Too many requests")
        kwargs = mock_send.call_args[1]
        assert kwargs["alert_type"] == "api_failure_openweather"
        assert "openweather" in kwargs["subject"]


def test_alert_supabase_failed(alert_service):
    with patch.object(alert_service, "_send") as mock_send:
        alert_service.alert_supabase_failed("auth.login", "Invalid credentials")
        kwargs = mock_send.call_args[1]
        assert kwargs["alert_type"] == "supabase_failure"
        assert "auth.login" in kwargs["details"]


def test_alert_health_summary_with_down_providers(alert_service):
    with patch.object(alert_service, "_send") as mock_send:
        alert_service.alert_health_summary({"groq": True, "gemini": False, "cerebras": False})
        mock_send.assert_called_once()
        kwargs = mock_send.call_args[1]
        assert "2/3" in kwargs["subject"]
        assert kwargs["alert_type"] == "health_summary"


def test_alert_health_summary_all_up(alert_service):
    with patch.object(alert_service, "_send") as mock_send:
        alert_service.alert_health_summary({"groq": True, "gemini": True})
        mock_send.assert_not_called()


def test_alert_circuit_breaker_tripped(alert_service):
    with patch.object(alert_service, "_send") as mock_send:
        alert_service.alert_circuit_breaker_tripped("groq", 300, "timeout", "Connection timed out")
        kwargs = mock_send.call_args[1]
        assert "circuit_breaker" in kwargs["alert_type"] and "groq" in kwargs["alert_type"]
        assert "groq" in kwargs["subject"]


def test_get_alert_service_singleton():
    first = get_alert_service()
    second = get_alert_service()
    assert first is second
