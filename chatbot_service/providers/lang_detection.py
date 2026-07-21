# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Lightweight Indian-language detection (no NLTK dependency)."""

from __future__ import annotations

import re

# Unicode script ranges for Indian languages
_DEVANAGARI = re.compile(r'[\u0900-\u097f]')   # Hindi, Marathi, Sanskrit, etc.
_TAMIL = re.compile(r'[\u0b80-\u0bff]')
_TELUGU = re.compile(r'[\u0c00-\u0c7f]')
_KANNADA = re.compile(r'[\u0c80-\u0cff]')
_MALAYALAM = re.compile(r'[\u0d00-\u0d7f]')
_BENGALI = re.compile(r'[\u0980-\u09ff]')
_GUJARATI = re.compile(r'[\u0a80-\u0aff]')
_PUNJABI = re.compile(r'[\u0a00-\u0a7f]')
_ODIA = re.compile(r'[\u0b00-\u0b7f]')
_URDU = re.compile(r'[\u0600-\u06ff]')  # Arabic script — includes Urdu


def detect_lang(text: str) -> str | None:
    """Detect if the text contains Indian language script.

    Returns ISO 639-1 code or None (English/unknown).
    """
    if _DEVANAGARI.search(text):
        return 'hi'
    if _TAMIL.search(text):
        return 'ta'
    if _TELUGU.search(text):
        return 'te'
    if _KANNADA.search(text):
        return 'kn'
    if _MALAYALAM.search(text):
        return 'ml'
    if _BENGALI.search(text):
        return 'bn'
    if _GUJARATI.search(text):
        return 'gu'
    if _PUNJABI.search(text):
        return 'pa'
    if _ODIA.search(text):
        return 'or'
    if _URDU.search(text):
        return 'ur'
    return None
