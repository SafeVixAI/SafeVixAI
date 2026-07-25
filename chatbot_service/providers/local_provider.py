# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from providers.openai_compat import OpenAICompatibleProvider


class LocalOllamaProvider(OpenAICompatibleProvider):
    """Local provider adapter handling native Ollama generation and OpenAI wrappers."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "llama3",
        display_name: str = "Ollama Local"
    ) -> None:
        super().__init__(
            api_key="ollama", # Ollama doesn't require API key usually, but openAI compat needs a non-empty string
            base_url=base_url,
            model=model,
            display_name=display_name
        )


class LocalVLLMProvider(OpenAICompatibleProvider):
    """Local provider adapter handling vLLM OpenAI wrapper."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
        display_name: str = "vLLM Local",
        api_key: str = "empty"
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            display_name=display_name
        )
