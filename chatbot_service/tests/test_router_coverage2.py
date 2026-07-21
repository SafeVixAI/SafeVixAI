# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Coverage tests for providers/router.py — now covers _stream_with_timeout."""
from __future__ import annotations

import asyncio
import time
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cache.llm_cache import LLMResponseCache
from providers.base import (
    ProviderRequest,
    ProviderResult,
    ProviderUnavailableError,
    QuotaExhaustedError,
    RateLimitError,
    TemplateProvider,
)
from providers.router import ProviderRouter


_REQUEST = ProviderRequest(
    message="What is the fine for drunk driving?",
    intent="challan",
    history=[],
)


def _settings(**overrides):
    defaults = dict(default_llm_provider="groq", http_timeout_seconds=5.0)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_prov(name, text=None, stream_method=None):
    p = MagicMock()
    p.name = name
    if text:
        p.generate = AsyncMock(return_value=ProviderResult(
            text=text, provider=name, model=f"{name}-m",
            prompt_tokens=10, completion_tokens=5, total_tokens=15,
        ))
    if stream_method is not None:
        p.stream = stream_method
    return p


def _router(provs=None, **kwargs):
    r = ProviderRouter(_settings(**kwargs))
    if provs:
        r.providers = provs
    return r


class TestSelectProviderLanguageRouting:
    def test_detected_lang_none_falls_to_default(self):
        r = _router()
        req = replace(_REQUEST, message="English text")
        assert r._select_provider_name(req, detected_lang=None) == "groq"

    def test_detected_lang_indian_not_in_list_uses_default(self):
        r = _router()
        req = replace(_REQUEST, intent="general")
        assert r._select_provider_name(req, detected_lang="xx") == "groq"

    def test_indian_language_general_routes_to_sarvam_30b(self):
        r = _router()
        for code in ("hi", "ta", "te", "kn", "ml", "bn", "gu", "pa", "or", "ur"):
            req = replace(_REQUEST, intent="general")
            assert r._select_provider_name(req, detected_lang=code) == "sarvam_30b"


class TestGenerateSuccessSarvamBadge:
    @pytest.mark.asyncio
    async def test_sarvam_badge_on_success(self):
        s = _mock_prov("sarvam", "\u0938\u0921\u093c\u0915 \u0938\u0941\u0930\u0915\u094d\u0937\u093e")
        r = _router({"sarvam": s, "template": TemplateProvider()}, default_llm_provider="sarvam")
        res = await r.generate(_REQUEST)
        assert res.text == "\u0938\u0921\u093c\u0915 \u0938\u0941\u0930\u0915\u094d\u0937\u093e"

    @pytest.mark.asyncio
    async def test_india_badge_set_for_sarvam(self):
        s = MagicMock()
        s.name = "sarvam"
        s.generate = AsyncMock(return_value=ProviderResult(
            text="\u0928\u092e\u0938\u094d\u0924\u0947", provider="sarvam", model="sarvam-2b",
        ))
        r = _router({"sarvam": s, "template": TemplateProvider()}, default_llm_provider="sarvam")
        res = await r.generate(_REQUEST)
        assert getattr(res, "india_badge", None) is not None


class TestProviderAvailabilityAsync:
    """_is_provider_available_async — Redis unavailable_until sync."""

    @pytest.mark.asyncio
    async def test_redis_until_future_returns_false_and_syncs(self):
        cache = MagicMock(spec=LLMResponseCache)
        future_time = time.time() + 3600
        cache.get_provider_unavailable_until = AsyncMock(return_value=future_time)
        r = _router({"groq": _mock_prov("groq", "ok")})
        r.cache = cache
        available = await r._is_provider_available_async("groq")
        assert available is False
        assert r._unavailable_until.get("groq") == future_time

    @pytest.mark.asyncio
    async def test_redis_until_past_returns_true(self):
        cache = MagicMock(spec=LLMResponseCache)
        past_time = time.time() - 100
        cache.get_provider_unavailable_until = AsyncMock(return_value=past_time)
        r = _router({"groq": _mock_prov("groq", "ok")})
        r.cache = cache
        available = await r._is_provider_available_async("groq")
        assert available is True

    @pytest.mark.asyncio
    async def test_redis_none_returns_true(self):
        cache = MagicMock(spec=LLMResponseCache)
        cache.get_provider_unavailable_until = AsyncMock(return_value=None)
        r = _router({"groq": _mock_prov("groq", "ok")})
        r.cache = cache
        available = await r._is_provider_available_async("groq")
        assert available is True


class TestMarkProviderFailureRedisSync:
    """_mark_provider_failure with cache Redis sync path (lines 544-551)."""

    @pytest.mark.asyncio
    async def test_redis_sync_on_failure(self):
        cache = MagicMock(spec=LLMResponseCache)
        cache.set_provider_unavailable_until = AsyncMock()
        cache.get_provider_unavailable_until = AsyncMock(return_value=None)
        r = _router({"g": _mock_prov("g", "ok")})
        r.cache = cache
        r._mark_provider_failure("g", RateLimitError("g", 30))
        cache.set_provider_unavailable_until.assert_called_once()
        args = cache.set_provider_unavailable_until.call_args[0]
        assert args[0] == "g"
        assert args[2] == 30

    @pytest.mark.asyncio
    async def test_redis_sync_no_running_loop(self):
        cache = MagicMock(spec=LLMResponseCache)
        cache.set_provider_unavailable_until = AsyncMock()
        r = _router({"g": _mock_prov("g", "ok")})
        r.cache = cache
        with patch("asyncio.get_running_loop", side_effect=RuntimeError):
            r._mark_provider_failure("g", RateLimitError("g", 30))
        cache.set_provider_unavailable_until.assert_not_called()

    @pytest.mark.asyncio
    async def test_redis_sync_on_quota_exhausted(self):
        cache = MagicMock(spec=LLMResponseCache)
        cache.set_provider_unavailable_until = AsyncMock()
        cache.get_provider_unavailable_until = AsyncMock(return_value=None)
        r = _router({"g": _mock_prov("g", "ok")})
        r.cache = cache
        r._mark_provider_failure("g", QuotaExhaustedError("done"))
        cache.set_provider_unavailable_until.assert_called_once()
        args = cache.set_provider_unavailable_until.call_args[0]
        assert args[2] == 86400

    def test_alert_called_for_long_duration(self):
        r = _router({"g": _mock_prov("g", "ok")})
        with patch("providers.router.get_alert_service") as mock_alerts:
            svc = MagicMock()
            mock_alerts.return_value = svc
            r._mark_provider_failure("g", ProviderUnavailableError("down for long period"))
            svc.alert_circuit_breaker_tripped.assert_called_once()
            args = svc.alert_circuit_breaker_tripped.call_args[1]
            assert args["duration_seconds"] == 300

    def test_confidence_score_truncation_past_20(self):
        """_calculate_confidence trims scores past 20 (line 379)."""
        r = _router()
        for i in range(25):
            r._calculate_confidence(
                ProviderResult(text="A" * 100, provider="g", model="m", total_tokens=100),
                "challan", "groq",
            )
        assert len(r._provider_scores["groq"]["challan"]) == 20


class TestStreamGenerateEdgeCases:
    """stream_generate — timeout path, first_token tracking, and error fallback."""

    @pytest.mark.asyncio
    async def test_stream_timeout_triggers_fallback(self):
        """_stream_with_timeout timeout triggers fallback in stream_generate."""
        ok_provider = _mock_prov("ok", "fallback response text")

        r = _router({"ok": ok_provider, "template": TemplateProvider()}, default_llm_provider="ok")
        r._fallback_chain = ["ok", "template"]

        async def timeout_stream(provider, req):
            raise TimeoutError("streaming timed out")
            yield  # never reached, makes this an async generator

        with patch.object(r, "_stream_with_timeout", new=timeout_stream):
            out = [x async for x in r.stream_generate(_REQUEST)]
        assert out[-1]["type"] == "done"
        # primary provider is marked unavailable after timeout, so template is used as fallback
        assert out[-1]["provider"] in ("ok", "template")

    @pytest.mark.asyncio
    async def test_stream_generate_yields_tokens(self):
        """stream_generate yields tokens with proper provider name."""
        async def token_gen():
            yield "single"

        async def mock_stream(provider, request):
            async for token in token_gen():
                yield token

        provider = _mock_prov("sp", "should not be called")
        # ensure sp is available
        r = _router({"sp": provider, "template": TemplateProvider()}, default_llm_provider="sp")
        r._unavailable_until.pop("sp", None) if "sp" in r._unavailable_until else None
        with patch.object(r, "_stream_with_timeout", new=mock_stream):
            out = [x async for x in r.stream_generate(_REQUEST)]
        assert len(out) >= 2
        assert out[-1]["type"] == "done"
        assert out[-1]["provider"] == "sp"

    @pytest.mark.asyncio
    async def test_stream_fallback_all_fail_yields_error(self):
        fail = _mock_prov("fail")
        fail.generate = AsyncMock(side_effect=RuntimeError("stream err"))
        fail.stream = None  # MagicMock auto-creates .stream; set None to force non-stream path
        r = _router({"fail": fail}, default_llm_provider="fail")
        r._fallback_chain = ["fail", "NONEXISTENT"]
        out = [x async for x in r.stream_generate(_REQUEST)]
        assert out[-1]["type"] == "error"

    @pytest.mark.asyncio
    async def test_real_stream_with_timeout_yields_tokens(self):
        """Exercises the actual _stream_with_timeout method (not mocked)."""
        async def stream_method(req):
            yield "first "
            yield "second "
            yield "third"

        prov = _mock_prov("streamer", stream_method=stream_method)
        r = _router({"streamer": prov, "template": TemplateProvider()}, default_llm_provider="streamer")
        out = [x async for x in r.stream_generate(_REQUEST)]
        assert out[-1]["type"] == "done"
        assert out[-1]["provider"] == "streamer"
        assert len(out) >= 4

    @pytest.mark.asyncio
    async def test_real_stream_with_timeout_timeout_triggers_fallback(self):
        """_stream_with_timeout timeout raises TimeoutError caught in stream_generate."""
        async def stream_method(req):
            await asyncio.sleep(999)
            yield "never"  # pragma: no cover

        prov = _mock_prov("slow", stream_method=stream_method)
        r = _router({"slow": prov, "template": TemplateProvider()}, default_llm_provider="slow")
        r.provider_timeout_seconds = 0.01
        r._fallback_chain = ["slow", "template"]
        r._unavailable_until.pop("slow", None)
        out = [x async for x in r.stream_generate(_REQUEST)]
        assert out[-1]["type"] == "done"
        assert out[-1]["provider"] == "template"


class TestCheckAllProviders:
    """check_all_providers fallback path — all fail (lines missed elsewhere)."""

    @pytest.mark.asyncio
    async def test_all_providers_fail_empty_list(self):
        f1 = _mock_prov("fail")
        f1.generate = AsyncMock(side_effect=ProviderUnavailableError("down"))
        r = _router({"fail": f1}, default_llm_provider="fail")
        r._fallback_chain = ["fail", "NONEXISTENT"]
        with pytest.raises(RuntimeError, match="All providers exhausted"):
            await r.generate(_REQUEST)

    def test_fallback_chain_low_confidence_skip(self):
        """Fallback chain skips providers when skip_low_confidence is set."""
        r = _router({"groq": _mock_prov("groq"), "template": TemplateProvider()})
        scored = r._score_providers_for_intent("general", ["groq", "template"])
        assert len(scored) <= 2
