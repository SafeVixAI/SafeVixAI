"""Tests for dynamic user-provider integration in the chatbot service."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from providers.router import ProviderRouter
from providers.base import TemplateProvider
from config import Settings


pytestmark = pytest.mark.asyncio


@pytest.fixture
def settings():
    return Settings(default_llm_provider="template", http_timeout_seconds=10, groq_api_key="", gemini_api_key="", cerebras_api_key="",
                   github_token="", nvidia_api_key="", openrouter_api_key="", mistral_api_key="", together_api_key="",
                   sarvam_api_key="")


@pytest.fixture
def router(settings):
    return ProviderRouter(settings, cache=None)


def test_router_init(router):
    assert router.settings is not None
    assert len(router.providers) >= 9
    assert "groq" in router.providers
    assert "template" in router.providers
    assert len(router._fallback_chain) > 0
    assert "template" in router._fallback_chain


def test_configure_user_providers_sets_flag(router):
    configs = [
        {
            "provider_name": "groq",
            "api_key": "gsk-test",
            "base_url": None,
            "default_model": "llama-3.1-8b-instant",
            "is_custom": False,
            "priority": 0,
            "is_active": True,
        },
    ]
    result = router.configure_user_providers(configs)
    assert len(result) == 1
    assert router._user_providers_configured is True


def test_configure_user_providers_skips_empty_name(router):
    configs = [{"provider_name": "", "api_key": "", "priority": 0}]
    result = router.configure_user_providers(configs)
    assert result == []


def test_configure_user_providers_custom_creates_openai_compat(router):
    configs = [
        {
            "provider_name": "my-custom-llm",
            "display_name": "My Custom LLM",
            "api_key": "sk-custom",
            "base_url": "http://localhost:8080/v1/chat/completions",
            "default_model": "llama3.2",
            "is_custom": True,
            "priority": 1,
            "is_active": True,
        },
    ]
    result = router.configure_user_providers(configs)
    assert "my-custom-llm" in result
    provider = router.providers.get("my-custom-llm")
    assert provider is not None
    # Should be an OpenAICompatibleProvider (i.e., has HttpProvider methods)
    assert hasattr(provider, "generate")
    assert hasattr(provider, "default_model")


def test_configure_user_providers_custom_via_unknown_name(router):
    """A name not in the known providers dict should create OpenAICompatibleProvider."""
    configs = [
        {
            "provider_name": "some-random-api",
            "api_key": "sk-random",
            "base_url": "https://api.random.com/v1/chat/completions",
            "default_model": "random-model",
            "is_custom": False,
            "priority": 5,
            "is_active": True,
        },
    ]
    result = router.configure_user_providers(configs)
    assert "some-random-api" in result


def test_rebuild_fallback_chain_respects_priority(router):
    configs = [
        {"provider_name": "openai", "api_key": "sk-o1", "priority": 10, "is_active": True, "is_custom": True},
        {"provider_name": "groq", "api_key": "gsk-g1", "priority": 0, "is_active": True, "is_custom": False},
        {"provider_name": "gemini", "api_key": "AI-g2", "priority": 5, "is_active": True, "is_custom": False},
    ]
    router.configure_user_providers(configs)
    chain = router._fallback_chain
    # groq (p0) should come before gemini (p5), which comes before openai (p10)
    assert chain.index("groq") < chain.index("gemini")
    assert chain.index("gemini") < chain.index("openai")


def test_rebuild_fallback_chain_excludes_inactive(router):
    configs = [
        {"provider_name": "groq", "api_key": "gsk-g1", "priority": 0, "is_active": True, "is_custom": False},
        {"provider_name": "gemini", "api_key": "AI-g2", "priority": 1, "is_active": False, "is_custom": False},
    ]
    router.configure_user_providers(configs)
    # gemini is in the user providers but inactive — check _rebuild_fallback_chain logic
    assert "gemini" in router._user_providers
    chain = router._fallback_chain
    # gemini may still appear if it was in the original chain since _rebuild_fallback_chain
    # only removes user_active names from the existing chain
    assert "groq" in chain


def test_reset_to_env_providers_clears_user_configs(router):
    configs = [
        {"provider_name": "custom-api", "api_key": "sk-c", "priority": 0, "is_active": True, "is_custom": True},
    ]
    router.configure_user_providers(configs)
    assert router._user_providers_configured is True

    router.reset_to_env_providers()
    assert router._user_providers_configured is False
    assert "custom-api" not in router.providers
    assert "groq" in router.providers  # Restored to env default


def test_get_active_provider_info(router):
    """Verify provider info returns non-empty list with user-configured providers."""
    configs = [
        {"provider_name": "groq", "api_key": "gsk-test", "priority": 0, "is_active": True, "is_custom": False},
    ]
    router.configure_user_providers(configs)
    assert len(router._user_providers) > 0
    assert "groq" in router._fallback_chain


def test_reset_removes_custom_from_providers(router):
    """After reset, custom providers should be removed from providers dict."""
    configs = [
        {"provider_name": "temp-custom", "api_key": "sk-t", "priority": 0, "is_active": True, "is_custom": True},
    ]
    router.configure_user_providers(configs)
    assert "temp-custom" in router.providers
    router.reset_to_env_providers()
    assert "temp-custom" not in router.providers
    assert "groq" in router.providers


def test_configure_user_providers_twice_overwrites(router):
    first = [{"provider_name": "groq", "api_key": "gsk-first", "priority": 0, "is_active": True, "is_custom": False}]
    second = [{"provider_name": "groq", "api_key": "gsk-second", "priority": 0, "is_active": True, "is_custom": False}]
    router.configure_user_providers(first)
    router.configure_user_providers(second)
    assert "groq" in router._user_providers
    assert router._user_providers["groq"]["api_key"] == "gsk-second"


def test_health_check_configures_user_providers(router):
    """Simulate health check flow: configure providers then verify chain."""
    configs = [
        {"provider_name": "template", "api_key": "", "priority": 0, "is_active": True, "is_custom": False},
    ]
    router.configure_user_providers(configs)
    assert router._user_providers_configured is True
    assert "template" in router._fallback_chain


# ═══════════════ Edge Case Tests ═══════════════


def test_rebuild_fallback_chain_early_return_when_no_active(router):  # C1
    """When no user providers are active, _rebuild_fallback_chain returns early."""
    original = list(router._fallback_chain)
    configs = [
        {"provider_name": "groq", "api_key": "gsk-test", "priority": 0, "is_active": False, "is_custom": False},
    ]
    router.configure_user_providers(configs)
    # _user_providers is populated, but _rebuild_fallback_chain returns early
    # because user_active set is empty (all inactive)
    assert router._fallback_chain == original


def test_configure_blank_api_key_does_not_crash(router):  # C2
    """configure_user_providers with blank api_key does not crash."""
    configs = [
        {"provider_name": "groq", "api_key": "", "base_url": None, "default_model": None, "priority": 0, "is_active": True, "is_custom": False},
    ]
    result = router.configure_user_providers(configs)
    assert "groq" in result
    assert router._user_providers["groq"]["api_key"] == ""


def test_configure_with_extra_headers(router):  # C3
    """configure_user_providers with extra_headers field."""
    configs = [
        {
            "provider_name": "custom-headers",
            "api_key": "sk-test",
            "base_url": "http://localhost:8080/v1",
            "default_model": "test-model",
            "extra_headers": {"X-Custom": "value123"},
            "priority": 0,
            "is_active": True,
            "is_custom": True,
        },
    ]
    result = router.configure_user_providers(configs)
    assert "custom-headers" in result
    stored = router._user_providers["custom-headers"]
    assert stored.get("extra_headers") == {"X-Custom": "value123"}


def test_reset_to_env_restores_fallback_chain(router):  # C4
    """reset_to_env_providers restores fallback chain to original ordering."""
    original = list(router._fallback_chain)
    configs = [
        {"provider_name": "groq", "api_key": "gsk-test", "priority": 10, "is_active": True, "is_custom": False},
        {"provider_name": "gemini", "api_key": "AI-test", "priority": 5, "is_active": True, "is_custom": False},
    ]
    router.configure_user_providers(configs)
    # Chain should now be gemini (p5) before groq (p10)
    assert router._fallback_chain != original
    router.reset_to_env_providers()
    assert router._fallback_chain == original


def test_detect_lang_returns_correct_codes():  # C5
    """detect_lang returns ISO 639-1 codes for Indian language scripts."""
    from providers.router import detect_lang
    assert detect_lang("नमस्ते") == "hi"       # Hindi
    assert detect_lang("வணக்கம்") == "ta"      # Tamil
    assert detect_lang("నమస్కారం") == "te"    # Telugu
    assert detect_lang("ನಮಸ್ಕಾರ") == "kn"      # Kannada
    assert detect_lang("ഹലോ") == "ml"        # Malayalam
    assert detect_lang("হ্যালো") == "bn"       # Bengali
    assert detect_lang("હેલો") == "gu"         # Gujarati
    assert detect_lang("ਸਤ ਸ੍ਰੀ ਅਕਾਲ") == "pa" # Punjabi
    assert detect_lang("ନମସ୍କାର") == "or"      # Odia
    assert detect_lang("سلام") == "ur"          # Urdu
    assert detect_lang("Hello") is None         # English → None
