# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

from providers.local_provider import LocalOllamaProvider, LocalVLLMProvider


class TestLocalProviders:
    def test_ollama_provider_defaults(self):
        p = LocalOllamaProvider()
        assert p.base_url() == "http://localhost:11434/v1/chat/completions"
        assert p._model == "llama3"
        assert p._display_name == "Ollama Local"

    def test_ollama_provider_custom(self):
        p = LocalOllamaProvider(base_url="http://custom:11434/v1", model="llama2")
        assert p.base_url() == "http://custom:11434/v1/chat/completions"
        assert p._model == "llama2"

    def test_vllm_provider_defaults(self):
        p = LocalVLLMProvider()
        assert p.base_url() == "http://localhost:8000/v1/chat/completions"
        assert p._model == "meta-llama/Meta-Llama-3-8B-Instruct"
        assert p._display_name == "vLLM Local"

    def test_vllm_provider_custom(self):
        p = LocalVLLMProvider(base_url="http://custom:8000/v1", model="custom-model", display_name="Custom", api_key="key123")
        assert p.base_url() == "http://custom:8000/v1/chat/completions"
        assert p._model == "custom-model"
        assert p._display_name == "Custom"
