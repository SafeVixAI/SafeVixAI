# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Sarvam AI provider — India's sovereign language model.

Routing priority for Indian languages:
  1. Direct Sarvam API (console.sarvam.ai) — fastest, free credits
  2. HuggingFace Inference API (HF_TOKEN) — fallback if Sarvam API key missing

Supported Indian languages (ISO 639-1 codes):
  hi=Hindi  ta=Tamil  te=Telugu  kn=Kannada  ml=Malayalam  mr=Marathi
  gu=Gujarati  bn=Bengali  pa=Punjabi  or=Odia  as=Assamese  ur=Urdu
  sa=Sanskrit  mai=Maithili  kok=Konkani  doi=Dogri  ks=Kashmiri
"""

from __future__ import annotations

INDIAN_LANGUAGE_CODES = {
    'hi', 'ta', 'te', 'kn', 'ml', 'mr', 'gu', 'bn', 'pa', 'or', 'as', 'ur',
    'sa', 'mai', 'kok', 'doi', 'ks'
}

HIGH_STAKES_INTENTS = {
    'LEGAL_ADVICE', 'EMERGENCY_REPORT', 'FIR_FILING', 'CHALLAN_DISPUTE'
}

# Exported symbols — used by providers/router.py for language-based routing decisions
__all__ = ['INDIAN_LANGUAGE_CODES', 'HIGH_STAKES_INTENTS', 'SarvamProvider', 'Sarvam105BProvider']

import logging
import os

import httpx
from providers.base import HttpProvider, ProviderRequest, ProviderResult, build_messages, raise_for_provider_status

logger = logging.getLogger(__name__)

# Primary: Sarvam Direct API (use when SARVAM_API_KEY is set — 100 free credits)
SARVAM_DIRECT_BASE = "https://api.sarvam.ai/v1"
# Fallback: HuggingFace OpenAI-compatible Inference API (used when Sarvam credits exhausted or key missing)
HF_INFERENCE_BASE = "https://api-inference.huggingface.co/v1"

_MAX_TOKENS = 800
_TEMPERATURE = 0.5


class SarvamProvider(HttpProvider):
    """Sarvam-2B via Direct API (primary) → HuggingFace (fallback).

    Priority:
      1. If SARVAM_API_KEY is set → use api.sarvam.ai directly (fastest, 100 free credits)
      2. Otherwise → use HF_TOKEN via api-inference.huggingface.co (free, OpenAI-compatible)
    """

    name = "sarvam_30b"

    def __init__(self, model_size: str = "30b", api_key: str = "", model: str = "") -> None:
        self.model_size = model_size
        self._sarvam_key = os.environ.get("SARVAM_API_KEY", "").strip()
        self._hf_key = os.environ.get("HF_TOKEN", "").strip()
        if api_key:
            actual_key = api_key
        elif self._sarvam_key and not self._sarvam_key.startswith("YOUR_"):
            actual_key = self._sarvam_key
        else:
            actual_key = self._hf_key
        super().__init__(api_key=actual_key, model=model or self.default_model())

    def _use_direct_api(self) -> bool:
        return bool(self._sarvam_key and not self._sarvam_key.startswith("YOUR_"))

    def _get_api_key(self) -> str:  # type: ignore[override]
        if not self._api_key:
            raise RuntimeError("Neither SARVAM_API_KEY nor HF_TOKEN")
        return self._api_key

    def default_model(self) -> str:
        model_map = {"105b": "sarvamai/sarvam-105b", "30b": "sarvamai/sarvam-30b", "2b": "sarvamai/sarvam-2b"}
        result = model_map.get(self.model_size, "sarvamai/sarvam-30b")
        if result == "sarvamai/sarvam-2b":
            logger.warning("Using Sarvam-2B model. Consider upgrading to 30B for better accuracy.")
        return result

    def base_url(self) -> str:
        if self._use_direct_api():
            return f"{SARVAM_DIRECT_BASE}/chat/completions"
        # HuggingFace fallback — OpenAI-compatible endpoint (activates when Sarvam credits exhausted)
        return f"{HF_INFERENCE_BASE}/chat/completions"

    def api_key_env(self) -> str:
        return "SARVAM_API_KEY" if self._use_direct_api() else "HF_TOKEN"

    def extra_headers(self) -> dict:
        if not self._use_direct_api():
            # HuggingFace requires explicit model routing via x-use-cache header
            return {"x-use-cache": "false"}
        return {}

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        """Call Sarvam direct API or HuggingFace inference endpoint."""
        api_key = self._get_api_key()
        model = request.provider_model or self.default_model()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            **self.extra_headers(),
        }

        # HuggingFace chat completions need the model in the body
        payload = {
            "model": model,
            "messages": build_messages(request),
            "max_tokens": _MAX_TOKENS,
            "temperature": _TEMPERATURE,
        }

        url = self.base_url()
        client = self._get_client()

        logger.debug("SarvamProvider → %s (model=%s, direct=%s)", url, model, self._use_direct_api())
        resp = await client.post(url, headers=headers, json=payload)
        raise_for_provider_status(resp, provider=self.name, model=model)

        data = resp.json()
        try:
            choices = data.get("choices", [])
            if not choices:
                raise KeyError("empty choices")
            text = choices[0].get("message", {}).get("content", "")
            if not text:
                raise KeyError("empty content")
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"SarvamProvider: unexpected response structure: {exc}. "
                f"Response keys: {list(data.keys())}"
            ) from exc
        return ProviderResult(text=text, provider=self.name, model=model, india_badge=True)


class Sarvam105BProvider(SarvamProvider):
    """Sarvam-105B — legal queries in Indian languages.
    More accurate but slower than 2B. Activates for HIGH_STAKES_INTENTS.
    """
    name = "sarvam_105b"

    def __init__(self) -> None:
        super().__init__(model_size="105b")
