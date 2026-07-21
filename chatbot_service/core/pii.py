# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(slots=True)
class PIIDetectionResult:
    has_pii: bool
    redacted_text: str
    detected_types: list[str] = field(default_factory=list)


class PIIDetector:
    def __init__(self, *, redact_with: str = "[REDACTED]") -> None:
        self.redact_with = redact_with
        self._patterns: dict[str, re.Pattern] = {
            "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            "phone": re.compile(r"(?:\+91|0)?[6-9]\d{9}"),
            "aadhaar": re.compile(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b"),
            "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
            "vehicle": re.compile(r"\b[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{1,4}\b"),
            "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
        }

    def detect(self, text: str) -> PIIDetectionResult:
        detected_types: list[str] = []
        redacted = text
        for pii_type, pattern in self._patterns.items():
            matches = pattern.findall(redacted)
            if matches:
                detected_types.append(pii_type)
                redacted = pattern.sub(self.redact_with, redacted)
        return PIIDetectionResult(
            has_pii=len(detected_types) > 0,
            redacted_text=redacted,
            detected_types=detected_types,
        )

    def has_pii(self, text: str) -> bool:
        for pattern in self._patterns.values():
            if pattern.search(text):
                return True
        return False
