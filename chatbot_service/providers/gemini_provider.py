# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Google Gemini provider — gemini-1.5-flash with 1M token context window.
Free tier: 1,500 req/day, 1M tok/min. Sign up: aistudio.google.com
Env vars: GEMINI_API_KEY, GEMINI_MODEL (optional, default: gemini-1.5-flash)

NOTE: Gemini uses its own REST endpoint format, not the OpenAI-compatible one.
We translate the OpenAI messages format to Gemini's contents format here.

P0-09 FIX (audit H4): API key moved from URL query param to x-goog-api-key header
to prevent key exposure in server access logs, proxy logs, and browser history.
"""
from __future__ import annotations

import json
import logging
import os

import httpx
from providers.base import HttpProvider, ProviderRequest, ProviderResult, build_messages, raise_for_provider_status

logger = logging.getLogger(__name__)

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(HttpProvider):
    """Gemini 1.5 Flash — used for large-context queries (legal PDFs, long conversations)."""

    name = "gemini"
    _client: httpx.AsyncClient | None = None

    def __init__(self, api_key: str = "", model: str = "") -> None:
        super().__init__(
            api_key=api_key or (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip(),
            model=model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip(),
        )

    def api_key_env(self) -> str:
        return "GEMINI_API_KEY"

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=40.0)
        return self._client

    async def stream(self, request: ProviderRequest):
        api_key = self._api_key
        if not api_key:
            return

        model = request.provider_model or self._model

        oai_messages = build_messages(request)
        contents = []
        system_text_parts: list[str] = []

        for msg in oai_messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_text_parts.append(content)
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})

        body: dict = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": 800,
                "temperature": 0.5,
            },
        }
        if system_text_parts:
            body["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system_text_parts)}]
            }

        url = f"{GEMINI_BASE}/{model}:streamGenerateContent"
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }

        async with self._get_client().stream("POST", url, json=body, headers=headers) as resp:
            raise_for_provider_status(resp, provider=self.name, model=model)
            buffer = ""
            async for chunk in resp.aiter_text():
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                text = part.get("text", "")
                                if text:
                                    yield text
                    except json.JSONDecodeError:
                        logger.debug("Skipping malformed SSE chunk in Gemini stream: %.100s", data_str, exc_info=True)

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        api_key = self._api_key
        if not api_key:
            raise RuntimeError("GeminiProvider: Missing env var 'GEMINI_API_KEY' or 'GOOGLE_API_KEY'")

        model = request.provider_model or self._model

        # Convert OpenAI-style messages → Gemini contents format
        oai_messages = build_messages(request)
        contents = []
        system_text_parts: list[str] = []

        for msg in oai_messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_text_parts.append(content)
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})

        # Gemini takes system instruction separately
        body: dict = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": 800,
                "temperature": 0.5,
            },
        }
        if system_text_parts:
            body["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system_text_parts)}]
            }

        url = f"{GEMINI_BASE}/{model}:generateContent"
        # P0-09: Use x-goog-api-key header instead of URL query param
        # Prevents API key from appearing in server access logs, proxy logs, and browser history
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }
        resp = await self._get_client().post(url, json=body, headers=headers)
        raise_for_provider_status(resp, provider=self.name, model=model)

        data = resp.json()
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise KeyError("empty candidates")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise KeyError("empty parts")
            text = parts[0].get("text", "")
            if not text:
                raise KeyError("empty text")
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"GeminiProvider: unexpected response structure: {exc}. "
                f"Response keys: {list(data.keys())}"
            ) from exc
        return ProviderResult(text=text, provider=self.name, model=model)
