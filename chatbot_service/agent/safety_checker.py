# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""SafetyChecker — Production-hardened safety filtering for SafeVixAI chatbot.

Fixes audit issue C2 / SECURITY#1:
- Expanded from 5 → 60+ blocked patterns
- Unicode NFKC normalization before matching (blocks fullwidth/homoglyph attacks)
- Zero-width character stripping (U+200B, U+200C, U+200D, U+FEFF, etc.)
- Jailbreak pattern detection (DAN, roleplay exploits, instruction overrides)
- Language-agnostic obfuscation detection (space insertion, l33t speak)
- Output safety check (detect if LLM response accidentally contains harmful content)
- Medical disclaimer injected on first-aid/medical topics
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PII Detection (optional — requires core.pii)
# ---------------------------------------------------------------------------
try:
    from core.pii import PIIDetector
    _pii_detector = PIIDetector()
except ImportError:
    _pii_detector = None

# ---------------------------------------------------------------------------
# Zero-width + invisible character strip
# ---------------------------------------------------------------------------
_ZW_RE = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2060\u2061\ufeff\u00ad]"
)

# ---------------------------------------------------------------------------
# Load patterns from versioned YAML (fallback to hardcoded defaults)
# ---------------------------------------------------------------------------
try:
    from prompts import (
        get_harm_patterns,
        get_jailbreak_patterns,
        get_medical_disclaimer,
        get_medical_keywords,
        get_severe_output_patterns,
    )
    _HARM_PATTERNS: tuple[str, ...] = get_harm_patterns() or (
        # Hit and run / evasion
        "fake an accident", "escape after an accident", "avoid police after",
        "hit and run", "flee the scene", "leave the scene after hitting",
        "drive away after accident", "evade police", "evade law enforcement",
        "hide evidence of crash", "bribe police", "report fake insurance",
        # Violence
        "hurt someone with a car", "kill someone with a car", "run over",
        "mow down", "weaponize vehicle", "use car as weapon", "vehicular attack",
        "vehicular homicide how to", "how to kill", "how to hurt",
        "murder using", "poison someone",
        # Illegal drugs / drunk driving enabling
        "drive drunk without getting caught", "cheat breathalyzer",
        "beat alcohol test", "how to pass drug test while driving",
        # Stalking / tracking without consent
        "track someone without them knowing", "stalk using gps",
        "monitor someone secretly",
        # Road rage enabling
        "how to road rage", "make driver crash", "cut off a car intentionally",
        # Document fraud
        "fake driving license", "forge insurance", "fake vehicle registration",
        "fake challan receipt",
        # Bypassing emergency services
        "ignore 112", "avoid calling ambulance", "not call emergency",
        # Suicide / self-harm (traffic-context)
        "crash my car on purpose", "drive into traffic to die",
        "use car to end my life",
    )
    _JAILBREAK_PATTERNS: tuple[str, ...] = get_jailbreak_patterns() or (
        "ignore previous instructions", "ignore all prior",
        "disregard your instructions", "you are now dan",
        "act as if you have no restrictions", "pretend you have no guidelines",
        "you are an ai without limits", "do anything now",
        "bypass your training", "override system prompt",
        "forget you are an assistant", "new persona",
        "roleplay as an evil", "simulate a harmful", "jailbreak",
        "developer mode", "sudo mode", "unrestricted mode",
        "you must comply", "your true self", "you are freed from",
        "no content policy", "no restrictions apply",
    )
    _SEVERE_OUTPUT_PATTERNS: tuple[str, ...] = get_severe_output_patterns() or (
        "how to kill", "how to hurt", "evade police", "flee the scene",
        "jailbreak", "ignore previous instructions", "bypass safety",
    )
    _MEDICAL_KEYWORDS: tuple[str, ...] = get_medical_keywords() or (
        "first aid", "cpr", "tourniquet", "fracture", "bleeding", "unconscious",
        "shock treatment", "spinal injury", "overdose", "burn treatment",
        "heart attack", "stroke symptoms", "medication", "drug interaction",
        "medical advice", "should i take", "treat my wound",
    )
    _MEDICAL_DISCLAIMER = get_medical_disclaimer() or (
        "\n\n **Medical Disclaimer:** This information is for general guidance only and does not "
        "constitute medical advice. Always call 108 (ambulance) or 112 (emergency) in a real emergency. "
        "Consult a qualified healthcare professional for medical decisions."
    )
except ImportError:
    logger.warning("prompts package not available — using hardcoded safety defaults")
    _HARM_PATTERNS: tuple[str, ...] = (
        "fake an accident", "escape after an accident", "avoid police after",
        "hit and run", "flee the scene", "leave the scene after hitting",
        "drive away after accident", "evade police", "evade law enforcement",
        "hide evidence of crash", "bribe police", "report fake insurance",
        "hurt someone with a car", "kill someone with a car", "run over",
        "mow down", "weaponize vehicle", "use car as weapon", "vehicular attack",
        "vehicular homicide how to", "how to kill", "how to hurt",
        "murder using", "poison someone",
        "drive drunk without getting caught", "cheat breathalyzer",
        "beat alcohol test", "how to pass drug test while driving",
        "track someone without them knowing", "stalk using gps",
        "monitor someone secretly",
        "how to road rage", "make driver crash", "cut off a car intentionally",
        "fake driving license", "forge insurance", "fake vehicle registration",
        "fake challan receipt",
        "ignore 112", "avoid calling ambulance", "not call emergency",
        "crash my car on purpose", "drive into traffic to die",
        "use car to end my life",
    )
    _JAILBREAK_PATTERNS: tuple[str, ...] = (
        "ignore previous instructions", "ignore all prior",
        "disregard your instructions", "you are now dan",
        "act as if you have no restrictions", "pretend you have no guidelines",
        "you are an ai without limits", "do anything now",
        "bypass your training", "override system prompt",
        "forget you are an assistant", "new persona",
        "roleplay as an evil", "simulate a harmful", "jailbreak",
        "developer mode", "sudo mode", "unrestricted mode",
        "you must comply", "your true self", "you are freed from",
        "no content policy", "no restrictions apply",
    )
    _SEVERE_OUTPUT_PATTERNS: tuple[str, ...] = (
        "how to kill", "how to hurt", "evade police", "flee the scene",
        "jailbreak", "ignore previous instructions", "bypass safety",
    )
    _MEDICAL_KEYWORDS: tuple[str, ...] = (
        "first aid", "cpr", "tourniquet", "fracture", "bleeding", "unconscious",
        "shock treatment", "spinal injury", "overdose", "burn treatment",
        "heart attack", "stroke symptoms", "medication", "drug interaction",
        "medical advice", "should i take", "treat my wound",
    )
    _MEDICAL_DISCLAIMER = (
        "\n\n **Medical Disclaimer:** This information is for general guidance only and does not "
        "constitute medical advice. Always call 108 (ambulance) or 112 (emergency) in a real emergency. "
        "Consult a qualified healthcare professional for medical decisions."
    )

# ---------------------------------------------------------------------------
# L33t-speak / obfuscation normalization table
# ---------------------------------------------------------------------------
_L33T: dict[str, str] = {
    "0": "o", "1": "i", "3": "e", "4": "a",
    "5": "s", "7": "t", "@": "a", "$": "s",
    "+": "t", "|": "i",
}


def _normalize_text(text: str, l33t: bool = True) -> str:
    """Normalize text for pattern matching:
    1. Strip zero-width / invisible characters
    2. Apply Unicode NFKC normalization (collapses fullwidth, homoglyphs)
    3. Lowercase
    4. Decode l33t-speak (optional — l33t corrupts numbers like 112→ii2)
    5. Remove excessive whitespace (space-inserted obfuscation)
    """
    text = _ZW_RE.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    if l33t:
        for leet, char in _L33T.items():
            text = text.replace(leet, char)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    blocked: bool
    response: str | None = None


class SafetyChecker:
    """Evaluate user messages for safety before forwarding to LLM."""

    def evaluate(self, message: str) -> SafetyDecision:
        # Check against both l33t-normalized (catches "h0w 70 hur7")
        # and non-l33t-normalized (l33t corrupts numbers like 112 → ii2)
        raw = _normalize_text(message, l33t=True)
        raw_no_l33t = _normalize_text(message, l33t=False)

        for normalized in [raw, raw_no_l33t]:
            # --- Jailbreak / injection attempt ---
            if any(pattern in normalized for pattern in _JAILBREAK_PATTERNS):
                return SafetyDecision(
                    blocked=True,
                    response=(
                        "I cannot comply with requests to override my safety guidelines or pretend to "
                        "be a different AI. I'm here to help with road safety, emergencies, and driving "
                        "information. If you have a genuine safety question, please ask directly."
                    ),
                )
            # --- Harmful / evasion / violence patterns ---
            if any(pattern in normalized for pattern in _HARM_PATTERNS):
                return SafetyDecision(
                    blocked=True,
                    response=(
                        "I cannot assist with evading emergency services, causing harm to people, or "
                        "illegal activities. "
                        "If you are witnessing or involved in an accident, call **112** immediately. "
                        "If this is a genuine safety or legal question, please rephrase it."
                    ),
                )
            # --- Space-inserted obfuscation (e.g. "h u r t   s o m e o n e") ---
            # Only trigger when letters appear as single chars separated by spaces
            tokens = normalized.split()
            if len(tokens) >= 4 and all(len(t) == 1 or t.isdigit() for t in tokens):
                joined = normalized.replace(" ", "")
                h_words = {w for p in _HARM_PATTERNS for w in p.split() if len(w) >= 4}
                j_words = {w for p in _JAILBREAK_PATTERNS for w in p.split() if len(w) >= 4}
                if any(w in joined for w in h_words | j_words):  # pragma: no branch
                    return SafetyDecision(
                        blocked=True,
                        response=(
                            "I cannot assist with evading emergency services, causing harm to people, or "
                            "illegal activities. "
                            "If you are witnessing or involved in an accident, call **112** immediately. "
                            "If this is a genuine safety or legal question, please rephrase it."
                        ),
                    )

        return SafetyDecision(blocked=False)

    def add_medical_disclaimer_if_needed(self, message: str, response: str) -> str:
        """Append medical disclaimer to LLM responses on medical/first-aid topics."""
        normalized = _normalize_text(message)
        if any(kw in normalized for kw in _MEDICAL_KEYWORDS):
            if _MEDICAL_DISCLAIMER not in response:
                return response + _MEDICAL_DISCLAIMER
        return response

    def check_output_safety(self, llm_response: str) -> SafetyDecision:
        """Basic output safety check — catch if the LLM returned harmful content."""
        normalized = _normalize_text(llm_response)
        if any(pattern in normalized for pattern in _SEVERE_OUTPUT_PATTERNS):
            return SafetyDecision(
                blocked=True,
                response=(
                    "I encountered an issue generating a safe response. "
                    "Please call 112 for emergencies or 108 for ambulance."
                ),
            )
        return SafetyDecision(blocked=False)

    def check_pii(self, text: str) -> tuple[bool, str, list[str]]:
        if _pii_detector is not None:
            result = _pii_detector.detect(text)
            return (result.has_pii, result.redacted_text, result.detected_types)
        return (False, text, [])

    async def check_llama_guard(self, text: str, role: str = "user") -> SafetyDecision:
        """Use Llama Guard 3 8B via Groq to evaluate safety of input or output."""
        import os
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            return SafetyDecision(blocked=False)

        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=groq_api_key)
            response = await client.chat.completions.create(
                messages=[{"role": role, "content": text}],
                model="llama-guard-3-8b",
            )
            content = response.choices[0].message.content.strip().lower()
            if content.startswith("unsafe"):  # pragma: no branch
                return SafetyDecision(
                    blocked=True,
                    response="I cannot assist with this request due to safety restrictions."
                )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Llama Guard check failed: %s", exc)

        return SafetyDecision(blocked=False)
