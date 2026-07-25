# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Fraud Detector for SafeVixAI.

Detects spam patterns, citizen abuse rate limiting, potential bots, and handles PII redaction for DPDP compliance.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.road_issue import RoadIssue

logger = logging.getLogger("safevixai.fraud_detector")

# Common PII Regexes for Redaction (Indian context: Aadhaar, PAN, phone, email)
AADHAAR_REGEX = re.compile(r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b|\b[2-9]\d{11}\b")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
PHONE_REGEX = re.compile(r"\b(?:\+91|91)?[6-9]\d{9}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


class FraudDetector:
    """Enterprise-grade Fraud and Abuse Detection with DPDP compliance."""

    SPAM_KEYWORDS = {
        "buy", "sell", "discount", "free", "click", "subscribe", "winner", "prize", "cash", "crypto",
        "lottery", "test", "testing", "asdf", "qwerty", "aaaa"
    }

    @classmethod
    def is_spam_text(cls, text: str | None) -> tuple[bool, str | None]:
        """Check if description matches typical spam patterns."""
        if not text:
            return False, None

        # Check for excessive exclamation marks or repeated letters
        if re.search(r"!{4,}", text):
            return True, "Excessive punctuation (abuse)"
        if re.search(r"(.)\1{6,}", text):
            return True, "Excessive repeated characters"

        # Check for all caps
        clean_text = text.strip()
        if len(clean_text) > 10 and clean_text == clean_text.upper():
            return True, "ALL CAPS submission (spam/rant)"

        # Check for spam keywords
        words = set(re.findall(r"\b\w+\b", text.lower()))
        matched_keywords = words.intersection(cls.SPAM_KEYWORDS)
        if matched_keywords:
            return True, f"Contains spam keywords: {', '.join(matched_keywords)}"

        return False, None

    @classmethod
    async def verify_rate_limit(
        cls,
        db: AsyncSession,
        *,
        citizen_phone: str,
        max_per_hour: int = 5,
    ) -> tuple[bool, int]:
        """
        Enforce rate limits per phone number to prevent citizen spamming.

        Returns:
            (is_allowed, recent_count)
        """
        if not citizen_phone:
            return True, 0

        one_hour_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        stmt = select(func.count(RoadIssue.id)).where(
            RoadIssue.citizen_phone == citizen_phone,
            RoadIssue.created_at > one_hour_ago,
        )
        count = (await db.execute(stmt)).scalar() or 0

        if count >= max_per_hour:
            logger.warning(
                "Phone %s hit rate limit: %d complaints in past hour (limit: %d)",
                citizen_phone, count, max_per_hour
            )
            return False, count

        return True, count

    @classmethod
    def detect_bot_signature(
        cls,
        *,
        user_agent: str | None,
        submission_time_ms: float | None,
    ) -> tuple[bool, str | None]:
        """Check for programmatic/headless bot submission signs."""
        if not user_agent:
            return True, "Missing User-Agent header"

        # Look for typical automated tools
        bot_indicators = ["python-requests", "curl", "postman", "headless", "selenium", "puppeteer"]
        for indicator in bot_indicators:
            if indicator in user_agent.lower():
                return True, f"Automated/Bot User-Agent detected: {indicator}"

        # Sub-second form submission
        if submission_time_ms is not None and submission_time_ms < 500:
            return True, "Sub-second submission (probable automation)"

        return False, None

    @classmethod
    def redact_pii(cls, text: str | None) -> str | None:
        """
        Redact Indian-specific PII (Aadhaar, PAN, Phone, Email) for DPDP compliance.
        """
        if not text:
            return text

        redacted = text
        redacted = AADHAAR_REGEX.sub("[REDACTED AADHAAR]", redacted)
        redacted = PAN_REGEX.sub("[REDACTED PAN]", redacted)
        redacted = PHONE_REGEX.sub("[REDACTED PHONE]", redacted)
        redacted = EMAIL_REGEX.sub("[REDACTED EMAIL]", redacted)
        return redacted
