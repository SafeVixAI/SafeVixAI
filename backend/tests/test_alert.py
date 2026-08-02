# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from core.alert import AlertService, _last_alert_time, get_alert_service

pytest.skip("Alert service disabled per user request", allow_module_level=True)


def test_init_disabled_when_no_credentials() -> None:
    with patch.dict("os.environ", {}, clear=True):
        svc = AlertService()
        assert svc.enabled is False
        assert svc.smtp_user == ""


def test_init_enabled_with_credentials() -> None:
    with patch.dict("os.environ", {"ALERT_EMAIL": "a@b.com", "ALERT_EMAIL_PASSWORD": "pass"}):
        svc = AlertService()
        assert svc.enabled is True
        assert svc.smtp_user == "a@b.com"


def test_cooldown_suppresses_duplicate() -> None:
    svc = AlertService()
    svc.enabled = True
    svc.smtp_user = "a@b.com"
    svc.smtp_pass = "pass"
    svc.alert_to = "a@b.com"
    key = "test_cooldown"
    _last_alert_time[key] = 0
    with patch("core.alert.smtplib.SMTP") as mock_smtp:
        mock_ctx = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_ctx
        svc._send(key, "test", "details", ["fix"])
        svc._send(key, "test", "details", ["fix"])
    assert mock_smtp.call_count == 1


def test_send_email_success() -> None:
    svc = AlertService()
    svc.enabled = True
    svc.smtp_user = "a@b.com"
    svc.smtp_pass = "pass"
    svc.alert_to = "a@b.com"
    with patch("smtplib.SMTP") as mock_smtp:
        instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = instance
        svc._send("test_type", "Test Subject", "details here", ["Fix 1", "Fix 2"])
        instance.send_message.assert_called_once()


def test_send_email_failure_logged() -> None:
    svc = AlertService()
    svc.enabled = True
    svc.smtp_user = "a@b.com"
    svc.smtp_pass = "pass"
    with patch("smtplib.SMTP", side_effect=Exception("SMTP down")):
        svc._send("test", "Subject", "details", ["fix"])


def test_send_not_enabled_logs_only() -> None:
    svc = AlertService()
    svc.enabled = False
    _last_alert_time.pop("test", None)
    with patch("core.alert.logger") as mock_log:
        svc._send("test", "Subject", "details", ["fix"])
        assert mock_log.warning.call_count >= 1


def test_alert_all_providers_failed() -> None:
    svc = AlertService()
    with patch.object(svc, "_send") as mock_send:
        svc.alert_all_providers_failed("groq", ["groq", "gemini"], "timeout", "hello")
        mock_send.assert_called_once()
        args = mock_send.call_args[1]
        assert "LLM Providers Failed" in args["subject"]
        assert len(args["solutions"]) == 3


def test_alert_external_api_failed() -> None:
    svc = AlertService()
    with patch.object(svc, "_send") as mock_send:
        svc.alert_external_api_failed("weather", "/api/weather", 503, "down")
        mock_send.assert_called_once()
        assert "External API Failed" in mock_send.call_args[1]["subject"]


def test_alert_supabase_failed() -> None:
    svc = AlertService()
    with patch.object(svc, "_send") as mock_send:
        svc.alert_supabase_failed("auth", "connection refused")
        mock_send.assert_called_once()
        assert "Supabase Connection Failed" in mock_send.call_args[1]["subject"]


def test_alert_health_summary_all_up() -> None:
    svc = AlertService()
    with patch.object(svc, "_send") as mock_send:
        svc.alert_health_summary({"groq": True, "gemini": True})
        mock_send.assert_not_called()


def test_alert_health_summary_some_down() -> None:
    svc = AlertService()
    with patch.object(svc, "_send") as mock_send:
        svc.alert_health_summary({"groq": True, "gemini": False})
        mock_send.assert_called_once()
        assert "DOWN" in mock_send.call_args[1]["subject"]


def test_alert_circuit_breaker_tripped() -> None:
    svc = AlertService()
    with patch.object(svc, "_send") as mock_send:
        svc.alert_circuit_breaker_tripped("groq", 120, "timeout", "rate limited")
        mock_send.assert_called_once()
        assert "Circuit Breaker Tripped" in mock_send.call_args[1]["subject"]


def test_get_alert_service_singleton() -> None:
    import core.alert as _ca
    _ca._instance = None
    a = get_alert_service()
    b = get_alert_service()
    assert a is b
