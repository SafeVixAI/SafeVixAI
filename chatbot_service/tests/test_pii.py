# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

from core.pii import PIIDetector


def test_email_detection():
    detector = PIIDetector()
    result = detector.detect("contact me at user@example.com")
    assert result.has_pii
    assert "email" in result.detected_types
    assert "[REDACTED]" in result.redacted_text
    assert "user@example.com" not in result.redacted_text


def test_phone_detection():
    detector = PIIDetector()
    result = detector.detect("Call me at +919876543210")
    assert result.has_pii
    assert "phone" in result.detected_types
    assert "[REDACTED]" in result.redacted_text


def test_aadhaar_detection():
    detector = PIIDetector()
    result = detector.detect("My aadhaar is 2345 6789 0123")
    assert result.has_pii
    assert "aadhaar" in result.detected_types


def test_pan_detection():
    detector = PIIDetector()
    result = detector.detect("PAN: ABCDE1234F")
    assert result.has_pii
    assert "pan" in result.detected_types


def test_vehicle_detection():
    detector = PIIDetector()
    result = detector.detect("TN01AB1234")
    assert result.has_pii
    assert "vehicle" in result.detected_types


def test_no_pii():
    detector = PIIDetector()
    result = detector.detect("What is the speed limit?")
    assert not result.has_pii
    assert result.detected_types == []


def test_multiple_pii_types():
    detector = PIIDetector()
    result = detector.detect("email me@test.com or call +919999999999")
    assert result.has_pii
    assert "email" in result.detected_types
    assert "phone" in result.detected_types


def test_redacted_text():
    detector = PIIDetector()
    result = detector.detect("My email is a@b.com and my PAN is ABCDE1234F")
    assert "[REDACTED]" in result.redacted_text
    assert result.redacted_text.count("[REDACTED]") == 2


def test_has_pii_quick_check():
    detector = PIIDetector()
    assert detector.has_pii("call +919999999999")
    assert not detector.has_pii("what is a challan")
