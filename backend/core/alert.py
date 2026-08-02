# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""SafeVixAI Alert Service — Email notifications for application-level failures.

Moved from project-root alert_service.py into backend/core/alert.py
to eliminate sys.path hacks from backend/main.py and chatbot_service.

Sends alert emails when critical external services fail:
  - All LLM providers exhausted
  - Supabase auth/DB failures
  - External API failures (geocoding, weather, FDA, etc.)
  - Rate limit exhaustion across providers

Each alert includes:
  - What failed and why
  - 3 specific ways to fix the issue
  - Current provider health status

Env vars:
  ALERT_EMAIL          — Gmail address to send from
  ALERT_EMAIL_PASSWORD — Gmail App Password (not regular password)
  ALERT_EMAIL_TO       — Recipient (defaults to ALERT_EMAIL)
"""

from __future__ import annotations

import logging
import os
import smtplib
import time
from collections import defaultdict
from datetime import datetime
from email.mime.text import MIMEText

logger = logging.getLogger("safevixai.alerts")

_last_alert_time: dict[str, float] = defaultdict(float)
ALERT_COOLDOWN_SECONDS = 300


class AlertService:
    """Lightweight email alert service for SafeVixAI production monitoring."""

    def __init__(self):
        self.smtp_user = os.environ.get("ALERT_EMAIL", "")
        self.smtp_pass = os.environ.get("ALERT_EMAIL_PASSWORD", "")
        self.alert_to = os.environ.get("ALERT_EMAIL_TO", self.smtp_user)
        self.enabled = bool(self.smtp_user and self.smtp_pass)

        if self.enabled:
            logger.info("Alert service enabled \u2192 %s", self.alert_to)
        else:
            logger.info("Alert service disabled (set ALERT_EMAIL + ALERT_EMAIL_PASSWORD)")

    def alert_all_providers_failed(
        self,
        primary_provider: str,
        failed_providers: list[str],
        error_msg: str,
        user_message: str = "",
    ):
        """Alert when ALL LLM providers in the fallback chain have failed."""
        self._send(
            alert_type="llm_providers_exhausted",
            subject="ALL LLM Providers Failed",
            details=(
                f"Primary provider: {primary_provider}\n"
                f"Failed chain: {' → '.join(failed_providers)}\n"
                f"Error: {error_msg}\n"
                f"User query: {user_message[:100]}..."
            ),
            solutions=[
                "CHECK API KEYS — Log into each provider dashboard and verify keys are active:\n"
                "  \u2022 Groq: https://console.groq.com/keys\n"
                "  \u2022 Cerebras: https://cloud.cerebras.ai\n"
                "  \u2022 Gemini: https://aistudio.google.com/app/apikey\n"
                "  \u2022 OpenRouter: https://openrouter.ai/keys",
                "CHECK RATE LIMITS — Provider quota/rate-limits may be reached:\n"
                "  • Groq: 30 RPM / 14400 RPD\n"
                "  • Gemini: 15 RPM / 1M tok/day\n"
                "  • Check your BYOK API key in Settings / .env or switch to local Ollama",
                "CHECK SERVICE STATUS — Provider may be down:\n"
                "  \u2022 Groq: https://status.groq.com\n"
                "  \u2022 Gemini: https://status.cloud.google.com\n"
                "  \u2022 Template fallback should ALWAYS work \u2014 if it also failed, "
                "check the application code in providers/base.py",
            ],
        )

    def alert_external_api_failed(
        self,
        service_name: str,
        endpoint: str,
        status_code: int,
        error_msg: str,
    ):
        """Alert when an external API (weather, geocoding, FDA, etc.) fails."""
        self._send(
            alert_type=f"api_failure_{service_name}",
            subject=f"External API Failed: {service_name}",
            details=(
                f"Service: {service_name}\n"
                f"Endpoint: {endpoint}\n"
                f"HTTP Status: {status_code}\n"
                f"Error: {error_msg}"
            ),
            solutions=[
                f"CHECK API KEY \u2014 Verify {service_name} credentials in .env:",
                f"CHECK RATE LIMITS \u2014 {service_name} may have daily/monthly limits:"
                "\n  \u2022 Free-tier APIs typically reset daily at midnight UTC"
                "\n  \u2022 Consider caching responses to reduce API calls",
                f"CHECK SERVICE STATUS \u2014 {service_name} may be experiencing downtime:"
                "\n  \u2022 The tool will return gracefully degraded data"
                "\n  \u2022 Users will see a 'service temporarily unavailable' message",
            ],
        )

    def alert_supabase_failed(self, operation: str, error_msg: str):
        """Alert when Supabase auth or database operations fail."""
        self._send(
            alert_type="supabase_failure",
            subject="Supabase Connection Failed",
            details=(
                f"Operation: {operation}\n"
                f"Error: {error_msg}"
            ),
            solutions=[
                "CHECK SUPABASE STATUS \u2014 https://status.supabase.com\n"
                "  \u2022 Free-tier projects auto-pause after 7 days of inactivity\n"
                "  \u2022 Go to https://supabase.com/dashboard \u2192 your project \u2192 Resume",
                "CHECK CREDENTIALS \u2014 Verify in backend/.env:\n"
                "  \u2022 SUPABASE_URL should be https://<project-ref>.supabase.co\n"
                "  \u2022 SUPABASE_KEY should be the anon/public key\n"
                "  \u2022 SUPABASE_SERVICE_KEY should be the service_role key",
                "CHECK NETWORK \u2014 The backend server may not have internet access:\n"
                "  \u2022 Test: curl -s https://api.supabase.co/health\n"
                "  \u2022 If on Cloud Run, check VPC/firewall settings",
            ],
        )

    def alert_health_summary(self, provider_health: dict[str, bool]):
        """Send periodic health summary of all providers."""
        down = [p for p, ok in provider_health.items() if not ok]
        up = [p for p, ok in provider_health.items() if ok]

        if not down:
            return

        self._send(
            alert_type="health_summary",
            subject=f"Provider Health: {len(down)}/{len(provider_health)} DOWN",
            details=(
                f"UP ({len(up)}): {', '.join(up) or 'none'}\n"
                f"DOWN ({len(down)}): {', '.join(down)}\n"
            ),
            solutions=[
                "IMMEDIATE \u2014 The fallback chain handles this automatically.\n"
                "  Users are being served by working providers.",
                "SHORT-TERM \u2014 Check and refresh API keys for downed providers.\n"
                f"  Failed: {', '.join(down)}",
                "LONG-TERM \u2014 Consider upgrading critical providers to paid tiers\n"
                "  to avoid free-tier rate limits during high-traffic periods.",
            ],
        )

    def alert_circuit_breaker_tripped(
        self,
        provider: str,
        duration_seconds: int,
        error_type: str,
        error_message: str,
    ):
        """Alert when a provider circuit breaker trips."""
        duration_min = duration_seconds // 60
        self._send(
            alert_type=f"circuit_breaker_{provider}",
            subject=f"Circuit Breaker Tripped: {provider}",
            details=(
                f"Provider: {provider}\n"
                f"Disabled for: {duration_min} minutes\n"
                f"Error type: {error_type}\n"
                f"Error: {error_message[:200]}"
            ),
            solutions=[
                f"CHECK {provider.upper()} STATUS \u2014 The provider may be down or rate-limited:\n"
                f"  \u2022 Verify API key is valid and has remaining quota\n"
                f"  \u2022 Check provider status page for outages",
                "WAIT FOR AUTOMATIC RECOVERY \u2014 Circuit breakers auto-reset:\n"
                f"  \u2022 This provider will be re-enabled after {duration_min} minutes\n"
                "  \u2022 The fallback chain continues serving requests",
                "CONSIDER PROVIDER REPLACEMENT — If this happens frequently:\n"
                "  • Update .env or frontend Settings with a fresh BYOK provider key\n"
                "  • Or enable local Ollama provider for unlimited local inference",
            ],
        )

    def _send(
        self,
        alert_type: str,
        subject: str,
        details: str,
        solutions: list[str],
    ):
        """Service disabled per user request."""
        pass


_instance: AlertService | None = None


def get_alert_service() -> AlertService:
    """Get or create the global AlertService singleton."""
    global _instance
    if _instance is None:
        _instance = AlertService()
    return _instance


# Backward-compatibility alias
send_alert = get_alert_service

