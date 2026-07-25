# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from cache.llm_cache import CacheEntry, LLMResponseCache
from providers.base import (
    InvalidProviderKeyError,
    ModelUnavailableError,
    ProviderRequest,
    ProviderResult,
    ProviderUnavailableError,
    QuotaExhaustedError,
    RateLimitError,
    TemplateProvider,
)
from providers.router import ProviderRouter, detect_lang
from providers.sarvam_provider import (
    HIGH_STAKES_INTENTS,
    INDIAN_LANGUAGE_CODES,
    Sarvam105BProvider,
    SarvamProvider,
)

_REQUEST = ProviderRequest(
    message="What is the fine for drunk driving?",
    intent="challan",
    history=[],
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _settings(**overrides: str | float | int) -> SimpleNamespace:
    defaults = dict(default_llm_provider="groq", http_timeout_seconds=5.0)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_prov(name: str, text: str | None = None) -> MagicMock:
    p = MagicMock()
    p.name = name
    if text:
        p.generate = AsyncMock(return_value=ProviderResult(
            text=text, provider=name, model=f"{name}-m",
            prompt_tokens=10, completion_tokens=5, total_tokens=15,
        ))
    return p


def _mk_client(status: int = 200, body: dict | None = None) -> MagicMock:
    client = MagicMock(spec=httpx.AsyncClient)
    client.is_closed = False
    if body is None:
        body = {"choices": [{"message": {"content": "Mocked response", "role": "assistant"}}]}
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.json.return_value = body
    resp.text = json.dumps(body)
    resp.headers = {}
    client.post = AsyncMock(return_value=resp)
    return client


def _router(provs: dict | None = None, **kwargs) -> ProviderRouter:
    r = ProviderRouter(_settings(**kwargs))
    if provs:
        r.providers = provs
    return r


class AsyncStreamProvider:
    name = "sp"
    async def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(text="fallback", provider="sp", model="m")
    async def stream(self, request: ProviderRequest):
        agen = AsyncMock()
        agen.__aiter__.return_value = agen
        agen.__anext__.side_effect = ["a", "b", StopAsyncIteration]
        return agen


class NoStreamProvider:
    name = "nostream"
    async def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(text="full response", provider="nostream", model="m")


# ══════════════════════════════════════════════════════════════════════════════
# 1. Constructor
# ══════════════════════════════════════════════════════════════════════════════

class TestConstructor:
    def test_stores_settings(self):
        s = _settings()
        r = ProviderRouter(s)
        assert r.settings is s
        assert r.default_provider == "groq"
        assert r.provider_timeout_seconds == 5.0

    def test_creates_all_providers(self):
        r = ProviderRouter(_settings())
        expected = {"groq", "cerebras", "gemini", "sarvam_30b",
                    "sarvam_105b", "github", "nvidia",
                    "openrouter", "mistral", "together", "template"}
        assert expected.issubset(r.providers.keys())
        assert isinstance(r.providers["template"], TemplateProvider)

    def test_fallback_chain_deduplicated(self):
        r = ProviderRouter(_settings())
        assert r._fallback_chain.count("groq") == 1
        assert r._fallback_chain.count("cerebras") == 1
        assert r._fallback_chain[-1] == "template"
        assert len(r._fallback_chain) == len(set(r._fallback_chain))

    def test_timeout_minimum_floor(self):
        r = ProviderRouter(_settings(http_timeout_seconds=0.0001))
        assert r.provider_timeout_seconds >= 0.001

    def test_confidence_threshold_default(self):
        assert _router()._confidence_threshold == 0.3


# ══════════════════════════════════════════════════════════════════════════════
# 2. _select_provider_name
# ══════════════════════════════════════════════════════════════════════════════

class TestSelectProvider:
    def test_default_english(self):
        assert _router()._select_provider_name(_REQUEST) == "groq"

    def test_indian_language_sarvam_30b(self):
        req = replace(_REQUEST, message="\u0938\u0921\u093c\u0915 \u0938\u0941\u0930\u0915\u094d\u0937\u093e")
        assert _router()._select_provider_name(req, detected_lang="hi") == "sarvam_30b"

    def test_indian_language_high_stakes_105b(self):
        req = replace(_REQUEST, intent="challan_dispute")
        assert _router()._select_provider_name(req, detected_lang="hi") == "sarvam_105b"

    def test_provider_hint(self):
        req = replace(_REQUEST, provider_hint="gemini")
        assert _router()._select_provider_name(req) == "gemini"

    def test_provider_hint_unknown_falls_default(self):
        req = replace(_REQUEST, provider_hint="bogus")
        assert _router()._select_provider_name(req) == "groq"

    def test_tamil_general_sarvam_30b(self):
        req = replace(_REQUEST, message="\u0b9a\u0bbe\u0bb2\u0bc8", intent="general")
        assert _router()._select_provider_name(req, detected_lang="ta") == "sarvam_30b"


# ══════════════════════════════════════════════════════════════════════════════
# 3. generate() — success
# ══════════════════════════════════════════════════════════════════════════════

class TestGenerateSuccess:
    @pytest.mark.asyncio
    async def test_default_provider_returns_result(self):
        g = _mock_prov("groq", "fine is \u20b910,000")
        r = _router({"groq": g, "template": TemplateProvider()})
        res = await r.generate(_REQUEST)
        assert res.text == "fine is \u20b910,000"
        assert res.provider_used == "groq"
        g.generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_with_retrieved_contexts(self):
        g = _mock_prov("groq", "answer")
        r = _router({"groq": g, "template": TemplateProvider()})
        req = replace(_REQUEST, document_snippets=["Section 185: Drunk driving"])
        await r.generate(req)
        args, _ = g.generate.call_args
        assert args[0].document_snippets == ["Section 185: Drunk driving"]

    @pytest.mark.asyncio
    async def test_with_tool_summaries(self):
        g = _mock_prov("groq", "answer")
        r = _router({"groq": g, "template": TemplateProvider()})
        req = replace(_REQUEST, tool_summaries=["Fine: \u20b910,000"])
        await r.generate(req)
        args, _ = g.generate.call_args
        assert "Fine: \u20b910,000" in args[0].tool_summaries

    @pytest.mark.asyncio
    async def test_stores_cache_on_success(self):
        cache = MagicMock(spec=LLMResponseCache)
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        g = _mock_prov("groq", "fresh")
        r = _router({"groq": g, "template": TemplateProvider()})
        r.cache = cache
        await r.generate(_REQUEST)
        cache.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_does_not_cache_template_result(self):
        cache = MagicMock(spec=LLMResponseCache)
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        t = TemplateProvider()
        r = _router({"template": t}, default_llm_provider="template")
        r.cache = cache
        await r.generate(_REQUEST)
        cache.set.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════════
# 4. generate() — cache hit
# ══════════════════════════════════════════════════════════════════════════════

class TestCacheHit:
    @pytest.mark.asyncio
    async def test_cache_hit_skips_provider(self):
        cache = MagicMock(spec=LLMResponseCache)
        cache.get = AsyncMock(return_value=CacheEntry(
            text="cached", provider="groq", model="m",
            prompt_tokens=5, completion_tokens=3, total_tokens=8,
        ))
        g = _mock_prov("groq")
        r = _router({"groq": g, "template": TemplateProvider()})
        r.cache = cache
        res = await r.generate(_REQUEST)
        assert res.text == "cached"
        assert res.provider_used == "cache"
        assert g.generate.call_count == 0

    @pytest.mark.asyncio
    async def test_cache_hit_with_detected_lang(self):
        cache = MagicMock(spec=LLMResponseCache)
        cache.get = AsyncMock(return_value=CacheEntry(text="cached", provider="groq", model="m"))
        r = _router({"groq": _mock_prov("groq"), "template": TemplateProvider()})
        r.cache = cache
        res = await r.generate(_REQUEST, detected_lang="ta")
        assert res.provider_used == "cache"


# ══════════════════════════════════════════════════════════════════════════════
# 5. generate() — fallback paths
# ══════════════════════════════════════════════════════════════════════════════

class TestGenerateFallback:
    @pytest.mark.asyncio
    async def test_primary_unavailable_falls_to_next(self):
        f1 = _mock_prov("fail")
        f1.generate = AsyncMock(side_effect=ProviderUnavailableError("down"))
        f2 = _mock_prov("ok", "fallback text")
        r = _router({"fail": f1, "ok": f2, "template": TemplateProvider()},
                    default_llm_provider="fail")
        r._fallback_chain = ["fail", "ok", "template"]
        res = await r.generate(_REQUEST)
        assert res.text == "fallback text"
        assert res.provider_used == "ok"
        assert res.fallback_from == "fail"

    @pytest.mark.asyncio
    async def test_all_providers_exhausted_raises(self):
        f1 = _mock_prov("fail")
        f1.generate = AsyncMock(side_effect=ProviderUnavailableError("down"))
        r = _router({"fail": f1}, default_llm_provider="fail")
        r._fallback_chain = ["fail", "NO_SUCH_PROVIDER_XYZ"]
        with pytest.raises(RuntimeError, match="All providers exhausted"):
            await r.generate(_REQUEST)

    @pytest.mark.asyncio
    async def test_timeout_falls_to_next(self):
        slow = _mock_prov("slow")
        slow.generate = AsyncMock(side_effect=TimeoutError("timeout"))
        fast = _mock_prov("fast", "fast result")
        r = _router({"slow": slow, "fast": fast, "template": TemplateProvider()},
                    default_llm_provider="slow", http_timeout_seconds=0.1)
        r._fallback_chain = ["slow", "fast", "template"]
        res = await r.generate(_REQUEST)
        assert res.text == "fast result"
        assert res.provider_used == "fast"

    @pytest.mark.asyncio
    async def test_rate_limited_moves_to_next(self):
        lim = _mock_prov("lim")
        lim.generate = AsyncMock(side_effect=RateLimitError("lim", retry_after=30))
        ok = _mock_prov("ok", "ok result")
        r = _router({"lim": lim, "ok": ok, "template": TemplateProvider()},
                    default_llm_provider="lim")
        r._fallback_chain = ["lim", "ok", "template"]
        res = await r.generate(_REQUEST)
        assert res.text == "ok result"
        assert "lim" in r._unavailable_until

    @pytest.mark.asyncio
    async def test_invalid_api_key_moves_to_next(self):
        bad = _mock_prov("bad")
        bad.generate = AsyncMock(side_effect=InvalidProviderKeyError("bad key"))
        ok = _mock_prov("ok", "ok")
        r = _router({"bad": bad, "ok": ok, "template": TemplateProvider()},
                    default_llm_provider="bad")
        r._fallback_chain = ["bad", "ok", "template"]
        res = await r.generate(_REQUEST)
        assert res.text == "ok"

    @pytest.mark.asyncio
    async def test_model_unavailable_moves_to_next(self):
        unav = _mock_prov("unav")
        unav.generate = AsyncMock(side_effect=ModelUnavailableError("gone"))
        ok = _mock_prov("ok", "ok")
        r = _router({"unav": unav, "ok": ok, "template": TemplateProvider()},
                    default_llm_provider="unav")
        r._fallback_chain = ["unav", "ok", "template"]
        res = await r.generate(_REQUEST)
        assert res.text == "ok"

    @pytest.mark.asyncio
    async def test_generic_exception_moves_to_next(self):
        flaky = _mock_prov("flaky")
        flaky.generate = AsyncMock(side_effect=ValueError("unexpected"))
        ok = _mock_prov("ok", "ok")
        r = _router({"flaky": flaky, "ok": ok, "template": TemplateProvider()},
                    default_llm_provider="flaky")
        r._fallback_chain = ["flaky", "ok", "template"]
        res = await r.generate(_REQUEST)
        assert res.text == "ok"
        assert res.provider_used == "ok"

    @pytest.mark.asyncio
    async def test_circuit_broken_skips_provider(self):
        good = _mock_prov("good", "good")
        r = _router({"bad": _mock_prov("bad"), "good": good, "template": TemplateProvider()},
                    default_llm_provider="bad")
        r._fallback_chain = ["bad", "good", "template"]
        r._unavailable_until["bad"] = time.time() + 3600
        res = await r.generate(_REQUEST)
        assert res.text == "good"
        assert res.provider_used == "good"

    @pytest.mark.asyncio
    async def test_no_fallback_raises_immediately(self):
        f = _mock_prov("fail")
        f.generate = AsyncMock(side_effect=ProviderUnavailableError("fail"))
        r = _router({"fail": f}, default_llm_provider="fail")
        with pytest.raises(ProviderUnavailableError):
            await r.generate(_REQUEST, try_fallbacks=False)


# ══════════════════════════════════════════════════════════════════════════════
# 6. generate() — low confidence path
# ══════════════════════════════════════════════════════════════════════════════

class TestLowConfidence:
    @pytest.mark.asyncio
    async def test_low_confidence_triggers_scored_fallback(self):
        low = MagicMock()
        low.name = "low"
        low.generate = AsyncMock(return_value=ProviderResult(
            text="[\u26a0\ufe0f Low confidence] I do not know the answer",
            provider="low", model="m",
        ))
        high = MagicMock()
        high.name = "high"
        high.generate = AsyncMock(return_value=ProviderResult(
            text="A" * 201, provider="high", model="m",
            prompt_tokens=10, completion_tokens=5, total_tokens=100,
        ))
        r = _router({"low": low, "high": high, "template": TemplateProvider()},
                    default_llm_provider="low")
        r._fallback_chain = ["low", "high", "template"]
        r._confidence_threshold = 0.3
        res = await r.generate(_REQUEST)
        assert res.text == "A" * 201
        assert res.provider_used == "high"


# ══════════════════════════════════════════════════════════════════════════════
# 7. _calculate_confidence / _average_confidence / _score_providers
# ══════════════════════════════════════════════════════════════════════════════

class TestConfidence:
    def test_template_always_03(self):
        r = _router()
        assert r._calculate_confidence(
            ProviderResult(text="x", provider="template", model="m"), "g", "template",
        ) == 0.3

    def test_empty_text_zero(self):
        r = _router()
        assert r._calculate_confidence(
            ProviderResult(text="", provider="g", model="m"), "g", "g",
        ) == 0.0

    def test_long_text_increases(self):
        r = _router()
        sc = r._calculate_confidence(
            ProviderResult(text="A" * 300, provider="g", model="m", total_tokens=100),
            "g", "g",
        )
        assert sc == pytest.approx(0.85)

    def test_low_confidence_keywords_penalty(self):
        r = _router()
        sc = r._calculate_confidence(
            ProviderResult(
                text="[\u26a0\ufe0f Low confidence] I do not know the answer",
                provider="g", model="m",
            ),
            "g", "g",
        )
        assert sc == pytest.approx(0.0)

    def test_score_tracks_history(self):
        r = _router()
        r._calculate_confidence(
            ProviderResult(text="Some answer here", provider="g", model="m"),
            "challan", "groq",
        )
        r._calculate_confidence(
            ProviderResult(text="Another longer answer here", provider="g", model="m"),
            "challan", "groq",
        )
        assert len(r._provider_scores["groq"]["challan"]) == 2
        assert r._average_confidence("groq", "challan") > 0

    def test_average_no_history_returns_05(self):
        assert _router()._average_confidence("groq", "challan") == 0.5

    def test_score_sorts_highest_first(self):
        r = _router({"a": _mock_prov("a"), "b": _mock_prov("b")})
        r._provider_scores.setdefault("a", {}).setdefault("i", []).append(0.5)
        r._provider_scores.setdefault("b", {}).setdefault("i", []).append(0.9)
        scored = r._score_providers_for_intent("i", ["a", "b"])
        assert scored[0][1] == "b"

    def test_score_skips_unknown(self):
        assert _router()._score_providers_for_intent("i", ["bogus"]) == []


# ══════════════════════════════════════════════════════════════════════════════
# 8. _provider_unavailable / _mark_provider_failure
# ══════════════════════════════════════════════════════════════════════════════

class TestCircuitBreaker:
    def test_not_marked(self):
        assert _router()._provider_unavailable("groq") is False

    def test_marked_true(self):
        r = _router()
        r._unavailable_until["groq"] = time.time() + 3600
        assert r._provider_unavailable("groq") is True

    def test_template_never_unavailable(self):
        r = _router()
        r._unavailable_until["template"] = time.time() + 3600
        assert r._provider_unavailable("template") is False

    def test_expired_clears(self):
        r = _router()
        r._unavailable_until["groq"] = time.time() - 1
        assert r._provider_unavailable("groq") is False
        assert "groq" not in r._unavailable_until

    def test_mark_rate_limit(self):
        r = _router()
        r._mark_provider_failure("g", RateLimitError("g", 30))
        assert r._unavailable_until["g"] > time.time() + 25

    def test_mark_quota_exhausted(self):
        r = _router()
        r._mark_provider_failure("g", QuotaExhaustedError("done"))
        assert r._unavailable_until["g"] > time.time() + 86000

    def test_mark_invalid_key(self):
        r = _router()
        r._mark_provider_failure("g", InvalidProviderKeyError("bad"))
        assert r._unavailable_until["g"] > time.time() + 3500

    def test_mark_model_unavailable(self):
        r = _router()
        r._mark_provider_failure("g", ModelUnavailableError("gone"))
        assert r._unavailable_until["g"] > time.time() + 3500

    def test_mark_provider_unavailable(self):
        r = _router()
        r._mark_provider_failure("g", ProviderUnavailableError("down"))
        assert r._unavailable_until["g"] > time.time() + 250

    def test_mark_timeout(self):
        r = _router()
        r._mark_provider_failure("g", TimeoutError("timeout"))
        assert r._unavailable_until["g"] > time.time() + 50

    def test_mark_template_ignored(self):
        r = _router()
        r._mark_provider_failure("template", RateLimitError("template", 30))
        assert "template" not in r._unavailable_until

    def test_mark_no_alert_for_short_duration(self):
        r = _router()
        with patch("providers.router.get_alert_service") as mock_alerts:
            r._mark_provider_failure("g", RateLimitError("g", 30))
            mock_alerts.assert_not_called()

    def test_mark_long_duration_triggers_alert(self):
        r = _router()
        with patch("providers.router.get_alert_service") as mock_alerts:
            svc = MagicMock()
            mock_alerts.return_value = svc
            r._mark_provider_failure("g", ProviderUnavailableError("down"))
            svc.alert_circuit_breaker_tripped.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# 9. stream_generate()
# ══════════════════════════════════════════════════════════════════════════════

class TestStream:
    @pytest.mark.asyncio
    async def test_stream_primary_yields_tokens(self):
        sp = AsyncStreamProvider()
        r = _router({"sp": sp, "template": TemplateProvider()}, default_llm_provider="sp")
        agen = AsyncMock()
        agen.__aiter__.return_value = agen
        agen.__anext__.side_effect = ["a", "b", StopAsyncIteration]
        with patch.object(r, "_stream_with_timeout", new=AsyncMock(return_value=agen)):
            out = [x async for x in r.stream_generate(_REQUEST)]
            assert len(out) >= 2
            assert out[-1]["type"] == "done"

    @pytest.mark.asyncio
    async def test_stream_provider_unavailable_uses_fallback(self):
        ok = _mock_prov("ok", "ok text")
        r = _router({"bad": _mock_prov("bad"), "ok": ok, "template": TemplateProvider()},
                    default_llm_provider="bad")
        r._fallback_chain = ["bad", "ok", "template"]
        r._unavailable_until["bad"] = time.time() + 3600
        out = [x async for x in r.stream_generate(_REQUEST)]
        assert out[-1]["type"] == "done"

    @pytest.mark.asyncio
    async def test_stream_fallback_all_fail_yields_error(self):
        fail = _mock_prov("fail")
        fail.stream = AsyncMock(side_effect=RuntimeError("stream err"))
        r = _router({"fail": fail}, default_llm_provider="fail")
        r._fallback_chain = ["fail", "NO_SUCH_PROVIDER_XYZ"]
        out = [x async for x in r.stream_generate(_REQUEST)]
        assert out[-1]["type"] == "error"

    @pytest.mark.asyncio
    async def test_stream_no_stream_method(self):
        r = _router({"nostream": NoStreamProvider(), "template": TemplateProvider()},
                    default_llm_provider="nostream")
        out = [x async for x in r.stream_generate(_REQUEST)]
        assert out[0]["type"] == "token"
        assert out[0]["text"] == "full response"
        assert out[-1]["type"] == "done"


# ══════════════════════════════════════════════════════════════════════════════
# 10. detect_lang
# ══════════════════════════════════════════════════════════════════════════════

class TestDetectLang:
    def test_hindi(self):
        assert detect_lang("\u0928\u092e\u0938\u094d\u0924\u0947") == "hi"
    def test_urdu(self):
        assert detect_lang("\u0627\u0644\u0633\u0644\u0627\u0645") == "ur"
    def test_english_none(self):
        assert detect_lang("English only") is None
    def test_empty_none(self):
        assert detect_lang("") is None
    def test_numbers_none(self):
        assert detect_lang("12345") is None


# ══════════════════════════════════════════════════════════════════════════════
# 11. SarvamProvider — Identity
# ══════════════════════════════════════════════════════════════════════════════

class TestSarvamIdentity:
    def test_name(self):
        assert SarvamProvider().name == "sarvam_30b"
    def test_105b_name(self):
        assert Sarvam105BProvider().name == "sarvam_105b"
    def test_105b_subclass(self):
        assert issubclass(Sarvam105BProvider, SarvamProvider)
    def test_105b_model_size(self):
        assert Sarvam105BProvider().model_size == "105b"
    def test_default_model_30b(self):
        assert SarvamProvider("30b").default_model() == "sarvamai/sarvam-30b"
    def test_default_model_105b(self):
        assert Sarvam105BProvider().default_model() == "sarvamai/sarvam-105b"


# ══════════════════════════════════════════════════════════════════════════════
# 12. SarvamProvider — API key detection
# ══════════════════════════════════════════════════════════════════════════════

class TestSarvamKeys:
    def test_direct_api_true(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "real-key")
        assert SarvamProvider()._use_direct_api() is True
    def test_direct_api_placeholder(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "YOUR_SARVAM_API_KEY")
        assert SarvamProvider()._use_direct_api() is False
    def test_direct_api_empty(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "")
        assert SarvamProvider()._use_direct_api() is False
    def test_direct_api_missing(self, monkeypatch):
        monkeypatch.delenv("SARVAM_API_KEY", raising=False)
        assert SarvamProvider()._use_direct_api() is False
    def test_get_api_key_no_keys(self, monkeypatch):
        monkeypatch.delenv("SARVAM_API_KEY", raising=False)
        monkeypatch.delenv("HF_TOKEN", raising=False)
        with pytest.raises(RuntimeError, match="Neither SARVAM_API_KEY nor HF_TOKEN"):
            SarvamProvider()._get_api_key()
    def test_get_api_key_direct(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "direct-key")
        assert SarvamProvider()._get_api_key() == "direct-key"
    def test_get_api_key_hf_fallback(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "YOUR_SARVAM_API_KEY")
        monkeypatch.setenv("HF_TOKEN", "hf-key")
        assert SarvamProvider()._get_api_key() == "hf-key"


# ══════════════════════════════════════════════════════════════════════════════
# 13. SarvamProvider — URL, headers, api_key_env
# ══════════════════════════════════════════════════════════════════════════════

class TestSarvamConfig:
    def test_base_url_direct(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "key")
        assert "api.sarvam.ai" in SarvamProvider().base_url()
    def test_base_url_hf(self, monkeypatch):
        monkeypatch.delenv("SARVAM_API_KEY", raising=False)
        monkeypatch.setenv("HF_TOKEN", "tok")
        assert "api-inference.huggingface.co" in SarvamProvider().base_url()
    def test_api_key_env_direct(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "key")
        assert SarvamProvider().api_key_env() == "SARVAM_API_KEY"
    def test_api_key_env_hf(self, monkeypatch):
        monkeypatch.delenv("SARVAM_API_KEY", raising=False)
        monkeypatch.setenv("HF_TOKEN", "tok")
        assert SarvamProvider().api_key_env() == "HF_TOKEN"
    def test_extra_headers_direct(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "key")
        assert SarvamProvider().extra_headers() == {}
    def test_extra_headers_hf(self, monkeypatch):
        monkeypatch.delenv("SARVAM_API_KEY", raising=False)
        monkeypatch.setenv("HF_TOKEN", "tok")
        hdrs = SarvamProvider().extra_headers()
        assert hdrs.get("x-use-cache") == "false"


# ══════════════════════════════════════════════════════════════════════════════
# 14. SarvamProvider — generate()
# ══════════════════════════════════════════════════════════════════════════════

class TestSarvamGenerate:
    @pytest.mark.asyncio
    async def test_generate_success(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "key")
        p = SarvamProvider()
        p._client = _mk_client()
        res = await p.generate(_REQUEST)
        assert res.text == "Mocked response"
        assert res.provider == "sarvam_30b"
        assert res.model == "sarvamai/sarvam-30b"
        assert res.india_badge is True

    @pytest.mark.asyncio
    async def test_generate_via_hf(self, monkeypatch):
        monkeypatch.delenv("SARVAM_API_KEY", raising=False)
        monkeypatch.setenv("HF_TOKEN", "hf-valid")
        p = SarvamProvider()
        p._client = _mk_client()
        res = await p.generate(_REQUEST)
        assert res.provider == "sarvam_30b"
        hdrs = p._client.post.call_args.kwargs["headers"]
        assert "Bearer" in hdrs["Authorization"]
        assert hdrs.get("x-use-cache") == "false"

    @pytest.mark.asyncio
    async def test_generate_no_keys_raises(self, monkeypatch):
        monkeypatch.delenv("SARVAM_API_KEY", raising=False)
        monkeypatch.delenv("HF_TOKEN", raising=False)
        with pytest.raises(RuntimeError, match="Neither SARVAM_API_KEY nor HF_TOKEN"):
            await SarvamProvider().generate(_REQUEST)

    @pytest.mark.asyncio
    async def test_generate_500_raises(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "key")
        p = SarvamProvider()
        p._client = _mk_client(status=500)
        with pytest.raises(ProviderUnavailableError):
            await p.generate(_REQUEST)

    @pytest.mark.asyncio
    async def test_generate_403_raises(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "key")
        p = SarvamProvider()
        p._client = _mk_client(status=403)
        with pytest.raises(InvalidProviderKeyError):
            await p.generate(_REQUEST)

    @pytest.mark.asyncio
    async def test_generate_429_raises(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "key")
        p = SarvamProvider()
        p._client = _mk_client(status=429)
        with pytest.raises(RateLimitError):
            await p.generate(_REQUEST)


# ══════════════════════════════════════════════════════════════════════════════
# 15. Sarvam105BProvider — generate()
# ══════════════════════════════════════════════════════════════════════════════

class TestSarvam105BGenerate:
    @pytest.mark.asyncio
    async def test_generate_success(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "key")
        p = Sarvam105BProvider()
        p._client = _mk_client()
        res = await p.generate(_REQUEST)
        assert res.text == "Mocked response"
        assert res.provider == "sarvam_105b"
        assert res.model == "sarvamai/sarvam-105b"

    @pytest.mark.asyncio
    async def test_generate_404_model_unavailable(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "key")
        p = Sarvam105BProvider()
        p._client = _mk_client(status=404, body={"error": "model not found"})
        with pytest.raises(ModelUnavailableError):
            await p.generate(_REQUEST)

    def test_uses_direct_api(self, monkeypatch):
        monkeypatch.setenv("SARVAM_API_KEY", "real-key")
        assert Sarvam105BProvider()._use_direct_api() is True


# ══════════════════════════════════════════════════════════════════════════════
# 16. HIGH_STAKES_INTENTS & INDIAN_LANGUAGE_CODES
# ══════════════════════════════════════════════════════════════════════════════

class TestConstants:
    def test_high_stakes_contains(self):
        for intent in ("LEGAL_ADVICE", "EMERGENCY_REPORT", "FIR_FILING", "CHALLAN_DISPUTE"):
            assert intent in HIGH_STAKES_INTENTS
    def test_not_general(self):
        assert "GENERAL" not in HIGH_STAKES_INTENTS
    def test_indian_languages(self):
        for code in ("hi", "ta", "te", "kn", "ml", "mr", "gu", "bn", "pa", "or", "as", "ur"):
            assert code in INDIAN_LANGUAGE_CODES
    def test_sanskrit_included(self):
        assert "sa" in INDIAN_LANGUAGE_CODES


# ══════════════════════════════════════════════════════════════════════════════
# 17. Provider availability edge cases
# ══════════════════════════════════════════════════════════════════════════════

class TestProviderAvailability:
    @pytest.mark.asyncio
    async def test_non_numeric_cache_does_not_crash(self):
        """Non-numeric cache return (e.g. AsyncMock) must not crash availability check."""
        cache = MagicMock(spec=LLMResponseCache)
        cache.get_provider_unavailable_until = AsyncMock(return_value=MagicMock())
        r = _router({"groq": _mock_prov("groq", "ok")})
        r.cache = cache
        available = await r._is_provider_available_async("groq")
        assert available is True

    @pytest.mark.asyncio
    async def test_template_always_available(self):
        """Template provider must always report as available, regardless of cache."""
        r = _router({"template": TemplateProvider()})
        r.cache = MagicMock(spec=LLMResponseCache)
        r.cache.get_provider_unavailable_until = AsyncMock(return_value=9999999999.0)
        available = await r._is_provider_available_async("template")
        assert available is True

    @pytest.mark.asyncio
    async def test_unavailable_until_cleanup_after_expiry(self):
        """In-memory unavailable_until must be cleaned up after the timestamp expires."""
        r = _router({"groq": _mock_prov("groq", "ok")})
        past = time.time() - 100
        r._unavailable_until["groq"] = past
        available = await r._is_provider_available_async("groq")
        assert available is True
        assert "groq" not in r._unavailable_until
