# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""SafeVixAI Alert Service — Email notifications for application-level failures.

Moved from project-root alert_service.py into chatbot_service/core/alert.py
to eliminate sys.path hacks.

Sends alert emails when critical external services fail:
  - All LLM providers exhausted
  - Supabase auth/DB failures
  - External API failures (geocoding, weather, FDA, etc.)
  - Rate limit exhaustion across providers

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
        arrow = ' \u2192 '
        self._send(
            alert_type="llm_providers_exhausted",
            subject="ALL LLM Providers Failed",
            details=(
                f"Primary provider: {primary_provider}\n"
                f"Failed chain: {arrow.join(failed_providers)}\n"
                f"Error: {error_msg}\n"
                f"User query: {user_message[:100]}..."
            ),
            solutions=[
                "CHECK API KEYS \u2014 Log into each provider dashboard and verify keys are active:\n"
                "  \u2022 Groq: https://console.groq.com/keys\n"
                "  \u2022 Cerebras: https://cloud.cerebras.ai\n"
                "  \u2022 Gemini: https://aistudio.google.com/app/apikey\n"
                "  \u2022 OpenRouter: https://openrouter.ai/keys",
                "CHECK RATE LIMITS — Provider quota/rate-limits may be reached:\n"
                "  • Groq: 30 RPM / 14400 RPD\n"
                "  • Gemini: 15 RPM / 1M tok/day\n"
                "  • Check your BYOK API key in Settings / .env or switch to local Ollama",
                "CHECK SERVICE STATUS — Provider may be down:\n"
                "  • Groq: https://status.groq.com\n"
                "  • Gemini: https://status.cloud.google.com\n"
                "  • Template fallback should ALWAYS work — if it also failed, "
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
                f"CHECK API KEY — Verify {service_name} credentials in .env:",
                f"CHECK RATE LIMITS — {service_name} may have daily/monthly limits:"
                "\n  • Free-tier APIs typically reset daily at midnight UTC"
                "\n  • Consider caching responses to reduce API calls",
                f"CHECK SERVICE STATUS — {service_name} may be experiencing downtime:"
                "\n  • The tool will return gracefully degraded data"
                "\n  • Users will see a 'service temporarily unavailable' message",
            ],
        )

    def alert_supabase_failed(self, operation: str, error_msg: str):
        self._send(
            alert_type="supabase_failure",
            subject="Supabase Connection Failed",
            details=(
                f"Operation: {operation}\n"
                f"Error: {error_msg}"
            ),
            solutions=[
                "CHECK SUPABASE STATUS — https://status.supabase.com\n"
                "  • Free-tier projects auto-pause after 7 days of inactivity\n"
                "  • Go to https://supabase.com/dashboard → your project → Resume",
                "CHECK CREDENTIALS — Verify in backend/.env:\n"
                "  • SUPABASE_URL should be https://<project-ref>.supabase.co\n"
                "  • SUPABASE_KEY should be the anon/public key\n"
                "  • SUPABASE_SERVICE_KEY should be the service_role key",
                "CHECK NETWORK — The backend server may not have internet access:\n"
                "  • Test: curl -s https://api.supabase.co/health\n"
                "  • If on Cloud Run, check VPC/firewall settings",
            ],
        )

    def alert_health_summary(self, provider_health: dict[str, bool]):
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
                "IMMEDIATE — The fallback chain handles this automatically.",
                "SHORT-TERM — Check and refresh BYOK API keys for downed providers.\n"
                f"  Failed: {', '.join(down)}",
                "LONG-TERM — Use multiple BYOK keys or local Ollama for zero-limit inference.",
            ],
        )

    def alert_circuit_breaker_tripped(
        self,
        provider: str,
        duration_seconds: int,
        error_type: str,
        error_message: str,
    ):
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
                f"CHECK {provider.upper()} STATUS — The provider may be down or rate-limited:\n"
                f"  • Verify API key is valid and has remaining quota"
                f"  • Check provider status page for outages",
                "WAIT FOR AUTOMATIC RECOVERY — Circuit breakers auto-reset:\n"
                f"  • This provider will be re-enabled after {duration_min} minutes"
                "  • The fallback chain continues serving requests",
                "CONSIDER PROVIDER REPLACEMENT — If this happens frequently:\n"
                "  • Update .env or frontend Settings with a fresh BYOK provider key"
                "  • Or enable local Ollama provider for unlimited local inference",
            ],
        )

    def alert_wiki_generation_failed(self, module_name: str, consecutive_fails: int, error_msg: str):
        """Alert when automated Wiki generation fails persistently via LLM chain."""
        self._send(
            alert_type="wiki_generation_failure",
            subject=f"Wiki Documentation Update Stopped: {module_name}",
            details=(
                f"Module: {module_name}\n"
                f"Consecutive Failures: {consecutive_fails}\n"
                f"Error/Status: {error_msg}"
            ),
            solutions=[
                "CHECK RATE LIMITS — Multi-LLM fallback chain may have exhausted free-tier tokens:",
                "CHECK PROVIDER STATUS — Primary or secondary LLMs may be experiencing downtime:",
                "FALLBACK STUBS ACTIVATED — The platform automatically defaults to AST stubs:",
            ],
        )

    def _send(
        self,
        alert_type: str,
        subject: str,
        details: str,
        solutions: list[str],
    ):
        now = time.time()
        if now - _last_alert_time[alert_type] < ALERT_COOLDOWN_SECONDS:
            logger.debug("Alert '%s' suppressed (cooldown)", alert_type)
            return
        _last_alert_time[alert_type] = now

        solutions_text = "\n\n".join(
            f"  {i+1}. {s}" for i, s in enumerate(solutions)
        )

        body = f"""SafeVixAI Production Alert
{'=' * 50}

{subject}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DETAILS:
{details}

{'=' * 50}
3 WAYS TO FIX THIS:

{solutions_text}

{'=' * 50}
This alert was sent by SafeVixAI Alert Service.
Cooldown: {ALERT_COOLDOWN_SECONDS}s between same-type alerts.
Configure: ALERT_EMAIL + ALERT_EMAIL_PASSWORD in .env
"""

        logger.warning("ALERT [%s]: %s \u2014 %s", alert_type, subject, details.split('\n')[0])

        if not self.enabled:
            logger.info("Email not configured. Alert printed to logs only.")
            return

        try:
            msg = MIMEText(body)
            msg["Subject"] = f"[SafeVixAI] {subject}"
            msg["From"] = self.smtp_user
            msg["To"] = self.alert_to

            with smtplib.SMTP("smtp.gmail.com", 587) as s:
                s.starttls()
                s.login(self.smtp_user, self.smtp_pass)
                s.send_message(msg)

            logger.info("Alert email sent to %s", self.alert_to)
        except Exception as e:
            logger.error("Failed to send alert email: %s", e)


_instance: AlertService | None = None


def get_alert_service() -> AlertService:
    global _instance
    if _instance is None:
        _instance = AlertService()
    return _instance


# Backward-compatibility alias
send_alert = get_alert_service

