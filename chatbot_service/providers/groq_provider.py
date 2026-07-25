# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Groq Cloud provider — llama-3.1-8b-instant at 300+ tok/s.
Free tier: 14,400 req/day, 500K tok/day, 6,000 TPM. Sign up: console.groq.com
Env vars: GROQ_API_KEY, GROQ_MODEL (optional, default: llama-3.1-8b-instant)

P0-05 FIX (audit C5): Groq free tier = 6,000 TPM.
At MAX_RESPONSE_TOKENS=800 and 20 RPM that's 16,000 TPM — 2.67x the free limit.
Fix: Cap MAX_RESPONSE_TOKENS at 400 for Groq, skip if estimated context > 4,000 tokens.
"""
from __future__ import annotations

import logging

from providers.base import HttpProvider, ProviderRequest, ProviderResult, build_messages

logger = logging.getLogger(__name__)

# Groq-specific token limits (free tier)
_GROQ_MAX_RESPONSE_TOKENS = 400   # halved from 800 to stay within 6000 TPM at 20 RPM
_GROQ_TPM_GUARD = 4_000           # skip Groq if estimated total tokens exceed this


def _estimate_tokens(text: str) -> int:
    """Heuristic token estimator: ~4 chars per token (close enough for guards)."""
    return max(1, len(text) // 4)


def _estimate_request_tokens(request: ProviderRequest) -> int:
    """Estimate total token count for a provider request."""
    messages = build_messages(request)
    total_chars = sum(len(m.get("content", "")) for m in messages)
    return max(1, total_chars // 4) + _GROQ_MAX_RESPONSE_TOKENS


class GroqProvider(HttpProvider):
    """Primary provider — fastest for English queries.

    Overrides generate()/stream() to:
    1. Skip if estimated context > _GROQ_TPM_GUARD tokens (C5 fix)
    2. Use reduced max_tokens to stay within 6000 TPM free tier
    """

    name = "groq"

    def __init__(self, api_key: str = "", model: str = "") -> None:
        super().__init__(max_tokens=_GROQ_MAX_RESPONSE_TOKENS, api_key=api_key, model=model)

    def api_key_env(self) -> str:
        return "GROQ_API_KEY"

    def base_url(self) -> str:
        return "https://api.groq.com/openai/v1/chat/completions"

    def default_model(self) -> str:
        return "llama-3.1-8b-instant"

    async def stream(self, request: ProviderRequest):
        estimated = _estimate_request_tokens(request)
        if estimated > _GROQ_TPM_GUARD:
            logger.info(
                "Groq stream skipped: estimated ~%d tokens exceeds %d TPM guard.",
                estimated, _GROQ_TPM_GUARD,
            )
            return
        async for token in super().stream(request):
            yield token

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        estimated = _estimate_request_tokens(request)
        if estimated > _GROQ_TPM_GUARD:
            logger.info(
                "Groq skipped: estimated ~%d tokens exceeds %d TPM guard. "
                "Passing to next provider.",
                estimated,
                _GROQ_TPM_GUARD,
            )
            from providers.base import ProviderUnavailableError
            msg = (
                f"groq: context too large (~{estimated} tokens). "
                "Skipping to preserve free-tier TPM budget."
            )
            raise ProviderUnavailableError(
                msg
            )
        return await super().generate(request)
