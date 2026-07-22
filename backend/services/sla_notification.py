# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""SLA breach notification service.

Sends email/webhook notifications when complaints breach their SLA deadline.
Integrates with the existing SLAMonitor background loop.
"""

from __future__ import annotations

import logging
import os
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Notification cooldown: don't re-notify the same complaint within this period
_NOTIFIED_CACHE: dict[str, datetime] = {}
COOLDOWN_MINUTES = 30


class SLANotificationService:
    """Sends SLA breach notifications via email and/or webhook."""

    def __init__(self):
        self.email_enabled = bool(os.getenv('SLA_ALERT_EMAIL'))
        self.webhook_enabled = bool(os.getenv('SLA_WEBHOOK_URL'))
        self.alert_email = os.getenv('SLA_ALERT_EMAIL', '')
        self.alert_password = os.getenv('SLA_ALERT_EMAIL_PASSWORD', '')
        self.smtp_host = os.getenv('SLA_SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SLA_SMTP_PORT', '587'))
        self.webhook_url = os.getenv('SLA_WEBHOOK_URL', '')
        self.recipients = [
            r.strip() for r in os.getenv('SLA_ALERT_RECIPIENTS', '').split(',')
            if r.strip()
        ]

    async def notify_sla_breach(
        self,
        complaint_ref: str,
        issue_type: str,
        severity: int,
        city: str | None,
        ward_id: str | None,
        sla_deadline: datetime,
        escalation_path: str | None = None,
    ) -> bool:
        """Send SLA breach notification. Returns True if any notification was sent."""
        # Cooldown check
        now = datetime.now(UTC)
        if complaint_ref in _NOTIFIED_CACHE:
            last = _NOTIFIED_CACHE[complaint_ref]
            if (now - last).total_seconds() < COOLDOWN_MINUTES * 60:
                return False

        overdue_hours = (now - sla_deadline).total_seconds() / 3600 if sla_deadline.tzinfo else 0

        subject = f"⚠️ SLA BREACH: {complaint_ref} ({issue_type}, severity {severity})"
        body = self._format_body(
            complaint_ref=complaint_ref,
            issue_type=issue_type,
            severity=severity,
            city=city,
            ward_id=ward_id,
            sla_deadline=sla_deadline,
            overdue_hours=overdue_hours,
            escalation_path=escalation_path,
        )

        sent = False

        if self.email_enabled and self.recipients:
            try:
                self._send_email(subject, body)
                sent = True
                logger.info("SLA email sent for %s to %s", complaint_ref, self.recipients)
            except Exception as e:
                logger.error("SLA email failed for %s: %s", complaint_ref, e)

        if self.webhook_enabled:
            try:
                await self._send_webhook(
                    complaint_ref=complaint_ref,
                    issue_type=issue_type,
                    severity=severity,
                    city=city,
                    overdue_hours=overdue_hours,
                    subject=subject,
                )
                sent = True
                logger.info("SLA webhook sent for %s", complaint_ref)
            except Exception as e:
                logger.error("SLA webhook failed for %s: %s", complaint_ref, e)

        if sent:
            _NOTIFIED_CACHE[complaint_ref] = now

        return sent

    def _format_body(self, **kwargs: Any) -> str:
        deadline = kwargs.get('sla_deadline', '')
        if isinstance(deadline, datetime):
            deadline = deadline.strftime('%Y-%m-%d %H:%M UTC')

        return f"""🚨 SLA BREACH ALERT — SafeVixAI

Complaint Reference: {kwargs.get('complaint_ref')}
Issue Type: {kwargs.get('issue_type')}
Severity: {kwargs.get('severity')}/5
City: {kwargs.get('city', 'N/A')}
Ward: {kwargs.get('ward_id', 'N/A')}
SLA Deadline: {deadline}
Overdue: {kwargs.get('overdue_hours', 0):.1f} hours
Escalation Path: {kwargs.get('escalation_path', 'Auto-escalation pending')}

ACTION REQUIRED:
1. Assign field officer immediately
2. Contact the responsible authority
3. Update complaint status in SafeVixAI dashboard

---
This is an automated alert from SafeVixAI SLA Monitor.
Do not reply to this email.
"""

    def _send_email(self, subject: str, body: str):
        """Send email via SMTP."""
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.alert_email
        msg['To'] = ', '.join(self.recipients)
        msg.set_content(body)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.alert_email, self.alert_password)
            server.send_message(msg)

    async def _send_webhook(self, **kwargs: Any):
        """Send webhook notification (Slack/Discord/Teams compatible)."""
        payload = {
            'text': f"⚠️ SLA BREACH: {kwargs.get('complaint_ref')} - {kwargs.get('issue_type')} (severity {kwargs.get('severity')}) in {kwargs.get('city', 'Unknown')} — {kwargs.get('overdue_hours', 0):.0f}h overdue",
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f"*{kwargs.get('subject', 'SLA Breach')}*\n\n"
                                f"• *Complaint:* {kwargs.get('complaint_ref')}\n"
                                f"• *Type:* {kwargs.get('issue_type')}\n"
                                f"• *Severity:* {kwargs.get('severity')}/5\n"
                                f"• *City:* {kwargs.get('city', 'N/A')}\n"
                                f"• *Overdue:* {kwargs.get('overdue_hours', 0):.0f} hours"
                    }
                }
            ]
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )
