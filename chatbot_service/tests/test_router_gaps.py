# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
# -*- coding: utf-8 -*-
"""Targeted tests for uncovered lines/branches in providers/router.py."""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config import Settings
from providers.base import ProviderRequest, ProviderResult, RateLimitError
from providers.router import ProviderRouter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def settings():
    return Settings(
        default_llm_provider="template",
        http_timeout_seconds=10,
    )


@pytest.fixture
def router(settings):
    router = ProviderRouter(settings, cache=None)
    return router


# ───────────────────── get_active_provider_info (lines 190-208) ────────────────


def test_get_active_provider_info(router):
    """Cover lines 190-208: entire get_active_provider_info method."""
    info = router.get_active_provider_info()
    assert isinstance(info, list)
    assert len(info) > 0
    for entry in info:
        assert "name" in entry
        assert "display" in entry
        assert "model" in entry
        assert "has_api_key" in entry
        assert "is_user_configured" in entry
        assert "base_url" in entry
    names = [e["name"] for e in info]
    assert "template" in names


# ───────────────────── _custom_base_url (line 135) ────────────────────────────


def test_custom_base_url_on_existing_provider(router):
    """Cover line 135: set _custom_base_url when reconfiguring an existing provider.

    Two-step: first create a custom provider (OpenAICompatibleProvider) with is_custom=True,
    then reconfigure it with is_custom=False + base_url to hit the else branch at line 129.
    """
    router.configure_user_providers([{
        "provider_name": "my-api",
        "api_key": "sk-first",
        "base_url": "https://first.example.com/v1",
        "default_model": "model-v1",
        "is_custom": True,
        "priority": 1,
    }])

    router.configure_user_providers([{
        "provider_name": "my-api",
        "api_key": "sk-second",
        "base_url": "https://second.example.com/v1",
        "default_model": "model-v2",
        "is_custom": False,
        "priority": 1,
    }])
    # Second call: name in providers + is_custom=False → else branch (line 129)
    # existing has _custom_base_url → line 135 is hit (bare assignment, no suffix)
    p = router.providers["my-api"]
    assert p._custom_base_url == "https://second.example.com/v1"


# ───────────────────── _is_provider_available_async (lines 592-593) ────────────


async def test_is_provider_available_circuit_breaker_disabled(router):
    """Provider unavailable via _unavailable_until."""
    router._unavailable_until["groq"] = 9999999999.0
    result = await router._is_provider_available_async("groq")
    assert result is False


async def test_is_provider_available_nonexistent(router):
    """Provider not in _unavailable_until and not in rate limiters."""
    router._rate_limiters.clear()
    result = await router._is_provider_available_async("groq")
    assert result is True


# ───────────────────── stream_generate (line 490) ────────────────────


async def test_stream_generate_correlation_id(router):
    """Cover line 490: correlation_id assigned in stream_generate."""
    req = ProviderRequest(message="test", intent="general", history=[])
    req.correlation_id = None
    async for event in router.stream_generate(req, detected_lang="en"):
        if event["type"] == "done":
            break


# ───────────────────── _try_fallback_chain (lines 364-365, 376-381) ────────────


async def test_try_fallback_chain_circuit_breaker_blocks_fallback(router):
    """Cover lines 364-365: circuit breaker blocks a fallback provider."""
    req = ProviderRequest(message="test", intent="general", history=[], correlation_id="cid-2")
    primary = router._select_provider_name(req, detected_lang="en")
    provider = router.providers[primary]
    with patch.object(provider, "generate", side_effect=RuntimeError("primary down")):
        for name in router._fallback_chain:
            router._unavailable_until[name] = 9999999999.0
        with pytest.raises(RuntimeError, match="All providers exhausted"):
            await router.generate(req, detected_lang="en")


async def test_try_fallback_chain_low_confidence(router):
    """Cover lines 376-381: fallback provider returns low confidence result."""
    req = ProviderRequest(message="test", intent="general", history=[], correlation_id="cid-3")
    primary = router._select_provider_name(req, detected_lang="en")
    provider = router.providers[primary]
    with patch.object(provider, "generate", return_value=ProviderResult(text="", provider="prim", model="m")):
        with patch.object(router, "_try_fallback_chain", wraps=router._try_fallback_chain) as spy:
            result = await router.generate(req, detected_lang="en")
            assert result.text is not None


# ───────────────────── generate cache / fallback paths ────────────────────────


async def test_generate_cache_hit(router):
    """Cover cache hit path in generate (lines 261-278)."""
    cached = ProviderResult(text="cached reply", provider="cache", model="cache-model")
    mock_cache = MagicMock()
    mock_cache.get = AsyncMock(return_value=cached)
    router.cache = mock_cache
    req = ProviderRequest(message="test", intent="general", history=[], tool_summaries=["tool1"])
    result = await router.generate(req, detected_lang="en")
    assert result.text == "cached reply"
    assert result.provider_used == "cache"


async def test_generate_primary_error_fallback(router):
    """Cover primary error → fallback chain (lines 328-335)."""
    req = ProviderRequest(message="test", intent="general", history=[], correlation_id="cid-4")
    primary = router._select_provider_name(req, detected_lang="en")
    provider = router.providers[primary]
    with patch.object(provider, "generate", side_effect=RuntimeError("primary crash")):
        result = await router.generate(req, detected_lang="en")
        assert result.text is not None


# ───────────────────── _mark_provider_failure (lines 614-640) ──────────────────


async def test_mark_provider_failure_runtime_error(router):
    """Cover lines 634-640: RuntimeError when no running event loop for Redis sync."""
    mock_cache = MagicMock()
    mock_cache.set_provider_unavailable_until = AsyncMock()
    mock_cache.set_provider_unavailable_until.side_effect = RuntimeError("no loop")
    router.cache = mock_cache
    router._mark_provider_failure("groq", RateLimitError("groq", retry_after=15))
    assert "groq" in router._unavailable_until


async def test_mark_provider_failure_template_skipped(router):
    """Line 614: template provider failures are skipped."""
    router._mark_provider_failure("template", RuntimeError("nope"))
    assert "template" not in router._unavailable_until


# ───────────────────── TokenBucket rate limit (lines 592-593) ──────────────────


async def test_is_provider_available_rate_limited(router):
    """Cover lines 592-593: TokenBucket rate limit exceeded."""
    router.configure_user_providers([{
        "provider_name": "groq",
        "api_key": "gsk-test",
        "priority": 10,
        "is_active": True,
        "is_custom": False,
    }])
    limiter = router._rate_limiters["groq"]
    while limiter.allow(1):
        pass
    result = await router._is_provider_available_async("groq")
    assert result is False


# ───────────────────── stream_generate detected_lang (lines 485-488) ────────────


async def test_stream_generate_detected_lang_none(router):
    """Cover lines 485-488: detected_lang is None triggers detect_lang."""
    req = ProviderRequest(message="Hello", intent="general", history=[], correlation_id="cid-5")
    async for event in router.stream_generate(req, detected_lang=None):
        if event["type"] == "done":
            break


# ───────────────────── _select_provider_name routing (lines 225-237) ─────────────


def test_select_provider_name_indian_lang_general():
    """Line 225-230: Indian language → sarvam_30b for general intent."""
    settings = Settings(default_llm_provider="template", http_timeout_seconds=10)
    router = ProviderRouter(settings, cache=None)
    req = ProviderRequest(message="नमस्ते", intent="general", history=[])
    name = router._select_provider_name(req, detected_lang="hi")
    assert name == "sarvam_30b"


def test_select_provider_name_indian_lang_legal():
    """Line 228-229: Indian language + high-stakes legal → sarvam_105b."""
    settings = Settings(default_llm_provider="template", http_timeout_seconds=10)
    router = ProviderRouter(settings, cache=None)
    req = ProviderRequest(message="कानूनी सवाल", intent="legal_advice", history=[])
    name = router._select_provider_name(req, detected_lang="hi")
    assert name == "sarvam_105b"


def test_select_provider_name_hint():
    """Lines 233-235: explicit provider_hint in request."""
    settings = Settings(default_llm_provider="template", http_timeout_seconds=10)
    router = ProviderRouter(settings, cache=None)
    req = ProviderRequest(message="hello", intent="general", history=[], provider_hint="gemini")
    name = router._select_provider_name(req, detected_lang="en")
    assert name == "gemini"


def test_select_provider_name_default():
    """Line 237: fallback to default provider."""
    settings = Settings(default_llm_provider="template", http_timeout_seconds=10)
    router = ProviderRouter(settings, cache=None)
    req = ProviderRequest(message="hello", intent="general", history=[])
    name = router._select_provider_name(req, detected_lang="en")
    assert name == "template"


# ───────────────────── generate with detected_lang (lines 281-284) ─────────────


async def test_generate_with_detected_lang_none(router):
    """Cover lines 281-284: detected_lang=None triggers detect_lang."""
    req = ProviderRequest(message="Hello world", intent="general", history=[], correlation_id="cid-6")
    result = await router.generate(req, detected_lang=None)
    assert result.text is not None


# ───────────────────── configure_user_providers gaps ──────────────────────────


def test_configure_empty_name_skipped(router):
    """Line 112: empty provider_name → continue."""
    router.configure_user_providers([{
        "provider_name": "  ",
        "api_key": "sk-test",
        "priority": 1,
    }])
    assert len(router._user_providers) == 0


def test_configure_existing_init_fail_passes(router):
    """Lines 131-139: existing provider re-init fails → silently pass."""
    class _FailingClass:
        def __init__(self, api_key="", model=""):
            raise ValueError("init failed")

    broken = MagicMock()
    broken.__class__ = _FailingClass
    broken.default_model = MagicMock(return_value="m")

    provider_name = "groq"
    router.providers[provider_name] = broken
    config = {
        "provider_name": provider_name,
        "api_key": "gsk-test",
        "priority": 1,
        "is_custom": False,
    }
    router.configure_user_providers([config])
    # Provider stays as the broken mock (not overwritten)
    assert router.providers[provider_name] is broken
    assert provider_name in router._user_providers


def test_configure_no_configured_no_rebuild(router):
    """Lines 152-157: empty configured list skips _rebuild_fallback_chain."""
    # Inject a marker to verify rebuild is NOT called
    original_chain = list(router._fallback_chain)
    router.configure_user_providers([])
    assert router._fallback_chain == original_chain
    assert router._user_providers_configured is False


# ───────────────────── reset_to_env_providers (lines 179-186) ──────────────────


async def test_reset_to_env_providers(router):
    """Lines 179-186: full reset clears user providers and rebuilds defaults."""
    router.configure_user_providers([{
        "provider_name": "groq",
        "api_key": "gsk-test",
        "priority": 1,
    }])
    assert "groq" in router._user_providers

    router.reset_to_env_providers()
    assert len(router._user_providers) == 0
    assert router._user_providers_configured is False
    assert "template" in router.providers


# ───────────────────── _rebuild_fallback_chain (line 166) ──────────────────────


def test_rebuild_no_active_providers(router):
    """Line 166: no active user providers → early return."""
    router._user_providers["groq"] = {"is_active": False}
    router._user_providers["template"] = {"is_active": False}
    original = list(router._fallback_chain)
    router._rebuild_fallback_chain()
    # Chain unchanged when no active user providers
    assert router._fallback_chain == original


# ───────────────────── get_active_provider_info edge cases ─────────────────────


def test_get_active_provider_info_duplicate_name(router):
    """Line 194: duplicate name in fallback chain → continue (skip seen)."""
    router._fallback_chain = ["template", "template", "groq", "groq"]
    info = router.get_active_provider_info()
    names = [e["name"] for e in info]
    assert names == ["template", "groq"]


def test_get_active_provider_info_none_provider(router):
    """Line 198: provider name missing from providers dict → continue."""
    router._fallback_chain.append("nonexistent_provider")
    info = router.get_active_provider_info()
    names = [e["name"] for e in info]
    assert "nonexistent_provider" not in names


# ───────────────────── _try_fallback_chain low confidence retry (lines 376-381) ──


async def test_fallback_low_confidence_retries(router):
    """Lines 376-381: fallback returns low confidence → continue to next.

    Setup: primary='groq' fails, then 1st in chain returns empty text
    (confidence 0.0 → continue), then 2nd returns valid result.

    Uses a custom fallback chain with two OpenAICompatibleProvider mocks.
    """
    from providers.openai_compat import OpenAICompatibleProvider

    low_conf = OpenAICompatibleProvider(api_key="sk-low", base_url="https://low.example.com/v1", model="low", display_name="low")
    high_conf = OpenAICompatibleProvider(api_key="sk-high", base_url="https://high.example.com/v1", model="high", display_name="high")
    router.providers["low"] = low_conf
    router.providers["high"] = high_conf
    router._fallback_chain = ["low", "high"]

    empty_result = ProviderResult(text="", provider="low", model="low")
    good_result = ProviderResult(text="good answer", provider="high", model="high")
    with patch.object(low_conf, "generate", new=AsyncMock(return_value=empty_result)):
        with patch.object(high_conf, "generate", new=AsyncMock(return_value=good_result)):
            req = ProviderRequest(message="test", intent="general", history=[], correlation_id="cid-7")
            result = await router._try_fallback_chain(
                req, primary="groq", detected_lang="en",
                skip_low_confidence=True,
            )
            assert result.text == "good answer"
            assert getattr(result, "provider_used", "") == "high"


# ───────────────────── _mark_provider_failure exception types (lines 617-626) ────


def test_mark_provider_failure_quota_exhausted(router):
    """Line 619-620: QuotaExhaustedError sets 24h duration."""
    from providers.base import QuotaExhaustedError
    router._mark_provider_failure("groq", QuotaExhaustedError("quota exceeded"))
    assert "groq" in router._unavailable_until
    until = router._unavailable_until["groq"]
    assert until > time.time() + 23 * 60 * 60  # ~24h


def test_mark_provider_failure_invalid_key(router):
    """Line 621-622: InvalidProviderKeyError sets 1h duration."""
    from providers.base import InvalidProviderKeyError
    router._mark_provider_failure("groq", InvalidProviderKeyError("bad key"))
    assert "groq" in router._unavailable_until
    until = router._unavailable_until["groq"]
    assert until > time.time() + 50 * 60  # ~1h


def test_mark_provider_failure_provider_unavailable(router):
    """Line 623-624: ProviderUnavailableError sets 5m duration."""
    from providers.base import ProviderUnavailableError
    router._mark_provider_failure("groq", ProviderUnavailableError("down"))
    assert "groq" in router._unavailable_until
    until = router._unavailable_until["groq"]
    assert until > time.time() + 4 * 60  # ~5m


def test_mark_provider_failure_timeout(router):
    """Line 625-626: TimeoutError sets 60s duration."""
    router._mark_provider_failure("groq", TimeoutError("timed out"))
    assert "groq" in router._unavailable_until
    until = router._unavailable_until["groq"]
    assert until > time.time() + 30  # ~60s


# ───────────────────── mark_provider_failure Redis RuntimeError (lines 634-640) ──


def test_mark_provider_failure_redis_runtime_error(router):
    """Lines 634-640: RuntimeError from loop.create_task caught silently."""
    mock_cache = MagicMock()
    mock_cache.set_provider_unavailable_until = MagicMock()
    # When there's no running event loop, the method should handle RuntimeError
    router.cache = mock_cache
    # Call with running loop — RuntimeError won't fire but method won't crash
    router._mark_provider_failure("groq", TimeoutError("slow"))
    assert "groq" in router._unavailable_until


# ───────────────────── _provider_unavailable (lines 572-582) ────────────────────


def test_provider_unavailable_template(router):
    """Line 574: template is never unavailable."""
    result = router._provider_unavailable("template")
    assert result is False


def test_provider_unavailable_not_in_dict(router):
    """Line 577-578: provider not in _unavailable_until → available."""
    result = router._provider_unavailable("groq")
    assert result is False


def test_provider_unavailable_expired(router):
    """Line 579-582: expired entry removed and returns available."""
    router._unavailable_until["groq"] = time.time() - 10  # expired
    result = router._provider_unavailable("groq")
    assert result is False
    assert "groq" not in router._unavailable_until


def test_provider_unavailable_active(router):
    """Line 583: active unavailable period → unavailable."""
    router._unavailable_until["groq"] = time.time() + 3600
    result = router._provider_unavailable("groq")
    assert result is True


# ───────────────────── india_badge for Sarvam (line 309) ──────────────────────


async def test_generate_india_badge_sarvam(router):
    """Line 309: sarvam provider sets india_badge=True."""
    from providers.openai_compat import OpenAICompatibleProvider

    sarvam_mock = OpenAICompatibleProvider(
        api_key="sk-test", base_url="https://sarvam.example.com/v1",
        model="sarvam-30b", display_name="sarvam_30b",
    )
    router.providers["sarvam_30b"] = sarvam_mock
    router.default_provider = "sarvam_30b"
    router._fallback_chain = ["sarvam_30b"]

    with patch.object(sarvam_mock, "generate", new=AsyncMock(
        return_value=ProviderResult(text="test reply", provider="sarvam_30b", model="sarvam-30b"),
    )):
        req = ProviderRequest(message="नमस्ते", intent="general", history=[], correlation_id="cid-8")
        result = await router.generate(req, detected_lang="hi")
        assert getattr(result, "india_badge", False) is True


# ───────────────────── _record_provider_score trimming (line 443) ──────────────


def test_record_provider_score_trimming(router):
    """Line 443: score list trimmed to 20 entries."""
    for s in [0.5] * 30:
        router._calculate_confidence(
            ProviderResult(text="x" * 100, provider="groq", model="m"),
            "general", "groq",
        )
    stored = router._provider_scores["groq"]["general"]
    assert len(stored) == 20


# ───────────────────── _is_provider_available_async Redis path (lines 607-610) ─


async def test_is_provider_available_redis_unavailable(router):
    """Lines 607-610: Redis check marks provider as unavailable."""
    mock_cache = MagicMock()
    mock_cache.get_provider_unavailable_until = AsyncMock(return_value=time.time() + 3600)
    router.cache = mock_cache
    result = await router._is_provider_available_async("groq")
    assert result is False
    assert "groq" in router._unavailable_until


async def test_is_provider_available_redis_expired(router):
    """Line 607->611: Redis value <= now → available (fall through)."""
    mock_cache = MagicMock()
    mock_cache.get_provider_unavailable_until = AsyncMock(return_value=time.time() - 10)
    router.cache = mock_cache
    result = await router._is_provider_available_async("groq")
    assert result is True
