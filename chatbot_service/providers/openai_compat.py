# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""OpenAI-compatible provider — for custom/local endpoints (Ollama, vLLM, LocalAI, etc.)

This provider accepts runtime configuration: base_url, api_key, model.
Useful for user-defined custom providers in the enterprise provider management system.
"""

from __future__ import annotations

import logging

from providers.base import HttpProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(HttpProvider):
    """Generic OpenAI-compatible provider for custom/local endpoints.

    Configured at runtime with base_url, api_key, and model.
    Supports any OpenAI-compatible chat completions API (Ollama, vLLM, LocalAI, etc.)
    """

    def __init__(
        self,
        *,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        display_name: str = "Custom Provider",
    ) -> None:
        self._display_name = display_name
        super().__init__(api_key=api_key, model=model)
        self._custom_base_url = base_url.rstrip("/") + "/chat/completions" if base_url else ""

    def api_key_env(self) -> str:
        return ""

    def base_url(self) -> str:
        if self._custom_base_url:
            return self._custom_base_url
        return "http://localhost:11434/v1/chat/completions"

    def default_model(self) -> str:
        return "llama3.2"

    @property
    def name(self) -> str:
        return self._display_name.lower().replace(" ", "-") if self._display_name else "custom"

    @name.setter
    def name(self, value: str) -> None:
        pass
