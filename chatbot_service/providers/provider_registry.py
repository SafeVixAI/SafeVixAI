# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Provider registry — factory mappings and default fallback chain."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from providers.base import TemplateProvider

# ── Provider name → provider class mapping ─────────────────────────────────
DEFAULT_PROVIDER_CONFIGS: dict[str, type[TemplateProvider]] = {}

# Lazy imports to avoid circular deps at module level
def _build_config() -> dict[str, type[TemplateProvider]]:
    from providers.cerebras_provider import CerebrasProvider
    from providers.gemini_provider import GeminiProvider
    from providers.github_models_provider import GitHubModelsProvider
    from providers.groq_provider import GroqProvider
    from providers.mistral_provider import MistralProvider
    from providers.nvidia_nim_provider import NvidiaNimProvider
    from providers.openrouter_provider import OpenRouterProvider
    from providers.sarvam_provider import Sarvam105BProvider, SarvamProvider
    from providers.together_provider import TogetherProvider
    from providers.base import TemplateProvider

    return {
        'groq': GroqProvider,
        'cerebras': CerebrasProvider,
        'gemini': GeminiProvider,
        'sarvam_30b': SarvamProvider,
        'sarvam_105b': Sarvam105BProvider,
        'github': GitHubModelsProvider,
        'nvidia': NvidiaNimProvider,
        'openrouter': OpenRouterProvider,
        'mistral': MistralProvider,
        'together': TogetherProvider,
        'template': TemplateProvider,
    }


def get_provider_configs() -> dict[str, type[TemplateProvider]]:
    """Lazy-load and cache the provider mapping."""
    if not DEFAULT_PROVIDER_CONFIGS:
        DEFAULT_PROVIDER_CONFIGS.update(_build_config())
    return DEFAULT_PROVIDER_CONFIGS


# ── Default fallback chain ─────────────────────────────────────────────────
DEFAULT_FALLBACK_CHAIN: list[str] = [
    'groq',        # 1. Fastest English — 300+ tok/s
    'cerebras',    # 2. Speed overflow — 2000+ tok/s
    'sarvam_30b',  # 3. Indic language specialist
    'github',      # 4. Free with GitHub account (Student Pack)
    'gemini',      # 5. Large context, 1M tok/day
    'nvidia',      # 6. GPU-optimized
    'openrouter',  # 7. Gateway to 20+ models
    'mistral',     # 8. 1B tok/month free
    'together',    # 9. $25 credit bank
    'template',    # 10. Always works (deterministic fallback)
]


def create_default_providers() -> dict[str, TemplateProvider]:
    """Instantiate all default providers and return the name→instance mapping."""
    configs = get_provider_configs()
    return {name: cls() for name, cls in configs.items()}
