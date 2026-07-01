# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Provider Router — 11-provider fallback chain with Indian language routing.

Auto-routing rules (in priority order):
  1. User speaks Indian language → Sarvam-30B (Indic specialist)
  2. Legal/challan query in Indian language → Sarvam-105B
  3. Default online → Groq (fastest English, 300+ tok/s)
  4. Groq rate-limited → Cerebras (2000+ tok/s overflow)
  5. High-context (legal PDFs > 50K tokens) → Gemini 1.5 Flash (1M ctx)
  6. Further fallbacks → GitHub → NVIDIA → OpenRouter → Mistral → Together
"""

from __future__ import annotations

import asyncio
import logging
import re
import time

from cache.llm_cache import LLMResponseCache, CacheEntry
from config import Settings
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
from providers.cerebras_provider import CerebrasProvider
from providers.gemini_provider import GeminiProvider
from providers.github_models_provider import GitHubModelsProvider
from providers.groq_provider import GroqProvider
from providers.mistral_provider import MistralProvider
from providers.nvidia_nim_provider import NvidiaNimProvider
from providers.openrouter_provider import OpenRouterProvider
from providers.sarvam_provider import (
    INDIAN_LANGUAGE_CODES,
    HIGH_STAKES_INTENTS,
    Sarvam105BProvider,
    SarvamProvider,
)
from providers.together_provider import TogetherProvider
from providers.openai_compat import OpenAICompatibleProvider

import sys as _sys
from pathlib import Path as _Path
for parent in _Path(__file__).resolve().parents:
    if (parent / 'alert_service.py').exists():
        if str(parent) not in _sys.path:
            _sys.path.insert(0, str(parent))
        break
from alert_service import get_alert_service

from core.metrics import chatbot_circuit_breaker_trips_total, update_circuit_breaker_gauges


logger = logging.getLogger("safevixai.chatbot.providers")

# ── Language detection (lightweight — no NLTK dependency) ─────────────────
# Script ranges for Indian languages
_DEVANAGARI = re.compile(r'[\u0900-\u097f]')   # Hindi, Marathi, Sanskrit, etc.
_TAMIL = re.compile(r'[\u0b80-\u0bff]')
_TELUGU = re.compile(r'[\u0c00-\u0c7f]')
_KANNADA = re.compile(r'[\u0c80-\u0cff]')
_MALAYALAM = re.compile(r'[\u0d00-\u0d7f]')
_BENGALI = re.compile(r'[\u0980-\u09ff]')
_GUJARATI = re.compile(r'[\u0a80-\u0aff]')
_PUNJABI = re.compile(r'[\u0a00-\u0a7f]')
_ODIA = re.compile(r'[\u0b00-\u0b7f]')
_URDU = re.compile(r'[\u0600-\u06ff]')  # Arabic script — includes Urdu


def detect_lang(text: str) -> str | None:
    """Detect if the text contains Indian language script.
    Returns ISO 639-1 code or None (English/unknown).
    """
    if _DEVANAGARI.search(text):
        return 'hi'  # Default Devanagari → Hindi
    if _TAMIL.search(text):
        return 'ta'
    if _TELUGU.search(text):
        return 'te'
    if _KANNADA.search(text):
        return 'kn'
    if _MALAYALAM.search(text):
        return 'ml'
    if _BENGALI.search(text):
        return 'bn'
    if _GUJARATI.search(text):
        return 'gu'
    if _PUNJABI.search(text):
        return 'pa'
    if _ODIA.search(text):
        return 'or'
    if _URDU.search(text):
        return 'ur'
    return None


class ProviderRouter:
    """Routes requests through the 11-provider fallback chain.

    Key routing decisions:
    - Indian language input → Sarvam AI (trained on 4 trillion Indic tokens)
    - Legal/challan in Indian lang → Sarvam-105B (more accurate for legal)
    - English → Groq → Cerebras → Gemini → GitHub → NVIDIA → OpenRouter
                     → Mistral → Together
    """

    def __init__(self, settings: Settings, *, cache: LLMResponseCache | None = None) -> None:
        self.settings = settings
        self.cache = cache

        # All 11 providers + Sarvam variants
        self.providers: dict[str, TemplateProvider] = {
            # Tier 1 — Critical
            'groq': GroqProvider(),
            'cerebras': CerebrasProvider(),
            'gemini': GeminiProvider(),
            # Indian language routing
            'sarvam': SarvamProvider(),
            'sarvam_30b': SarvamProvider(),
            'sarvam_105b': Sarvam105BProvider(),
            # Tier 2 — High
            'github': GitHubModelsProvider(),
            'github_models': GitHubModelsProvider(),
            'nvidia': NvidiaNimProvider(),
            'nvidia_nim': NvidiaNimProvider(),
            # Tier 3 — Medium
            'openrouter': OpenRouterProvider(),
            'mistral': MistralProvider(),
            'together': TogetherProvider(),
            # Template / testing
            'template': TemplateProvider(),
        }
        self.default_provider = settings.default_llm_provider
        self.provider_timeout_seconds = max(0.001, float(settings.http_timeout_seconds))
        self._unavailable_until: dict[str, float] = {}

        # Phase 18: Token Bucket rate limiters per provider
        from providers.circuit_breaker import TokenBucket
        self._rate_limiters: dict[str, TokenBucket] = {}

        # Confidence score tracking per provider per intent
        self._provider_scores: dict[str, dict[str, list[float]]] = {}
        self._confidence_threshold = 0.3

        # Fallback chain — tried in order when provider fails
        self._fallback_chain = [
            'groq',
            'cerebras',
            'sarvam_30b',
            'github',      # 1. Free with GitHub account (Student Pack)
            'groq',        # 2. Fastest English — 300+ tok/s
            'cerebras',    # 3. Speed overflow — 2000+ tok/s
            'gemini',      # 4. Large context, 1M tok/day
            'nvidia',      # 5. GPU-optimized
            'openrouter',  # 6. Gateway to 20+ models
            'mistral',     # 7. 1B tok/month free
            'together',    # 8. $25 credit bank
            'template',    # 9. Always works (deterministic fallback)
        ]
        self._fallback_chain = list(dict.fromkeys(self._fallback_chain))

        # ── User-configured providers (overrides env-var defaults) ─────────
        self._user_providers: dict[str, dict] = {}
        self._user_providers_configured = False

    def configure_user_providers(self, provider_configs: list[dict]) -> list[str]:
        """Override providers with user-supplied API keys and custom endpoints.

        Args:
            provider_configs: List of dicts with keys:
                - provider_name: str (e.g. 'groq', 'openai', 'ollama')
                - api_key: str
                - base_url: str | None
                - default_model: str | None
                - is_custom: bool
                - priority: int
                - extra_headers: dict | None

        Returns:
            List of configured provider names.
        """
        configured = []
        for cfg in provider_configs:
            name = cfg.get("provider_name", "").strip().lower()
            if not name:
                continue

            api_key = cfg.get("api_key", "") or ""
            base_url = cfg.get("base_url") or ""
            model = cfg.get("default_model") or ""
            is_custom = cfg.get("is_custom", False)
            extra_headers = cfg.get("extra_headers") or {}

            if is_custom or name not in self.providers:
                provider = OpenAICompatibleProvider(
                    api_key=api_key,
                    base_url=base_url,
                    model=model or "gpt-3.5-turbo",
                    display_name=cfg.get("display_name", name),
                )
                provider_name = name
                self.providers[provider_name] = provider
            else:
                existing = self.providers.get(name)
                if existing and hasattr(existing, '__init__'):
                    try:
                        provider = existing.__class__(api_key=api_key, model=model or existing.default_model())
                        if base_url and hasattr(provider, '_custom_base_url'):
                            provider._custom_base_url = base_url
                        self.providers[name] = provider
                    except Exception:
                        pass
                provider_name = name

            from providers.circuit_breaker import TokenBucket
            # Base capacity on priority or default
            priority = cfg.get("priority", 10)
            capacity = 100 if priority < 5 else 30
            refill = 10.0 if priority < 5 else 2.0
            if provider_name not in self._rate_limiters:
                self._rate_limiters[provider_name] = TokenBucket(capacity=capacity, refill_rate=refill)

            self._user_providers[provider_name] = cfg
            configured.append(provider_name)

        if configured:
            self._user_providers_configured = True
            self._rebuild_fallback_chain()
            logger.info("User-configured %d providers: %s", len(configured), configured)

        return configured

    def _rebuild_fallback_chain(self) -> None:
        """Rebuild fallback chain based on user priority ordering."""
        user_active = {
            name for name, cfg in self._user_providers.items()
            if cfg.get("is_active", True)
        }
        if not user_active:
            return

        existing = [p for p in self._fallback_chain if p not in user_active]
        user_sorted = sorted(
            self._user_providers.items(),
            key=lambda x: x[1].get("priority", 0),
        )
        user_names = [name for name, cfg in user_sorted if cfg.get("is_active", True)]
        self._fallback_chain = list(dict.fromkeys(user_names + existing))
        logger.info("Fallback chain rebuilt: %s", self._fallback_chain[:6])

    def reset_to_env_providers(self) -> None:
        """Reset all user-configured providers, reverting to env-var defaults."""
        for name in list(self._user_providers.keys()):
            self.providers.pop(name, None)
        self._user_providers.clear()
        self._user_providers_configured = False

        self.providers.update({
            'groq': GroqProvider(),
            'cerebras': CerebrasProvider(),
            'gemini': GeminiProvider(),
            'sarvam': SarvamProvider(),
            'sarvam_30b': SarvamProvider(),
            'sarvam_105b': Sarvam105BProvider(),
            'github': GitHubModelsProvider(),
            'nvidia': NvidiaNimProvider(),
            'openrouter': OpenRouterProvider(),
            'mistral': MistralProvider(),
            'together': TogetherProvider(),
        })
        self._fallback_chain = list(dict.fromkeys([
            'groq', 'cerebras', 'sarvam_30b', 'github',
            'groq', 'cerebras', 'gemini', 'nvidia',
            'openrouter', 'mistral', 'together', 'template',
        ]))
        logger.info("ProviderRouter reset to default env-var providers")

    def get_active_provider_info(self) -> list[dict]:
        """Return currently active provider configurations (info only, no keys)."""
        info = []
        seen = set()
        for name in self._fallback_chain:
            if name in seen:
                continue
            seen.add(name)
            provider = self.providers.get(name)
            if provider is None:
                continue
            is_user = name in self._user_providers
            info.append({
                "name": name,
                "display": getattr(provider, '_display_name', name),
                "model": getattr(provider, '_model', ''),
                "has_api_key": bool(getattr(provider, '_api_key', '')),
                "is_user_configured": is_user,
                "base_url": getattr(provider, '_custom_base_url', '') or getattr(provider, 'base_url', lambda: '')(),
            })
        return info

    def _select_provider_name(
        self,
        request: ProviderRequest,
        *,
        detected_lang: str | None = None,
    ) -> str:
        """Apply routing logic to pick the best provider.

        Routing priority:
          1. Indian language → Sarvam
          2. Legal intent + Indian lang → Sarvam-105B
          3. Explicit provider hint in request → use it
          4. Default configured provider
        """
        # ── Indian language routing ──────────────────────────────────────────
        if detected_lang and detected_lang in INDIAN_LANGUAGE_CODES:
            # Check for high-stakes legal intent
            intent = getattr(request, 'intent', '') or ''
            if intent.upper() in HIGH_STAKES_INTENTS:
                return 'sarvam_105b'
            return 'sarvam_30b'

        # ── Explicit provider override ────────────────────────────────────────
        hint = getattr(request, 'provider_hint', None)
        if hint and hint in self.providers:
            return hint

        return self.default_provider



    async def generate(
        self,
        request: ProviderRequest,
        *,
        detected_lang: str | None = None,
        try_fallbacks: bool = True,
    ) -> ProviderResult:
        """Generate a response using the selected provider with automatic fallback."""
        import uuid
        if not request.correlation_id:
            request.correlation_id = str(uuid.uuid4())
            
        logger.info(
            "LLM generate [%s] - Intent: %s - Provider: %s",
            request.correlation_id,
            request.intent,
            request.provider_hint or "auto"
        )

        # C9: Check LLM response cache before making API call
        if self.cache:
            cached = await self.cache.get(
                request.message,
                request.intent,
                request.tool_summaries,
            )
            if cached:
                logger.info("LLM cache hit for intent=%s", request.intent)
                return ProviderResult(
                    text=cached.text,
                    provider=cached.provider,
                    model=cached.model,
                    prompt_tokens=cached.prompt_tokens,
                    completion_tokens=cached.completion_tokens,
                    total_tokens=cached.total_tokens,
                    provider_used='cache',
                    detected_lang=detected_lang,
                )

        # Auto-detect language from request content if not provided
        if detected_lang is None:
            detected_lang = detect_lang(request.message or '')

        primary = self._select_provider_name(request, detected_lang=detected_lang)
        provider = self.providers.get(primary) or self.providers.get('groq') or self.providers['template']

        try:
            if not await self._is_provider_available_async(primary):
                raise ProviderUnavailableError(f"{primary} is temporarily disabled by circuit breaker")
            result = await self._generate_with_timeout(provider, request)

            confidence = self._calculate_confidence(result, request.intent, primary)
            result.confidence_score = confidence  # type: ignore[attr-defined]
            if confidence < self._confidence_threshold:
                logger.warning(
                    "Low confidence %.2f for %s on intent=%s, trying fallback",
                    confidence, primary, request.intent,
                )
                return await self._try_fallback_chain(
                    request, primary, detected_lang,
                    primary_err=None, skip_low_confidence=True,
                )

            # Attach routing metadata
            result.provider_used = primary  # type: ignore[attr-defined]
            result.detected_lang = detected_lang  # type: ignore[attr-defined]
            # Add badge when Sarvam is used
            if primary.startswith('sarvam'):
                result.india_badge = True  # type: ignore[attr-defined]

            # C9: Store successful response in cache
            if self.cache and result.provider != 'template':
                await self.cache.set(
                    request.message,
                    request.intent,
                    request.tool_summaries,
                    CacheEntry(
                        text=result.text,
                        provider=result.provider,
                        model=result.model,
                        prompt_tokens=result.prompt_tokens,
                        completion_tokens=result.completion_tokens,
                        total_tokens=result.total_tokens,
                    ),
                )
            
            return result
        except Exception as primary_err:
            self._mark_provider_failure(primary, primary_err)
            if not try_fallbacks:
                raise

            return await self._try_fallback_chain(
                request, primary, detected_lang, primary_err=primary_err,
            )

    async def _try_fallback_chain(
        self,
        request: ProviderRequest,
        primary: str,
        detected_lang: str | None,
        *,
        primary_err: Exception | None = None,
        skip_low_confidence: bool = False,
    ) -> ProviderResult:
        """Try fallback providers when primary fails or has low confidence."""
        error_msg = str(primary_err) if primary_err else "Low confidence score"

        candidate_chain = list(dict.fromkeys(self._fallback_chain))
        if primary in candidate_chain:
            candidate_chain.remove(primary)

        if skip_low_confidence:
            scored = self._score_providers_for_intent(request.intent, candidate_chain)
            candidate_chain = [name for _, name in scored]
            logger.info(
                "Confidence-scored fallback chain for intent=%s: %s",
                request.intent, candidate_chain[:5],
            )

        failed_providers = [primary]
        for fallback_name in candidate_chain:
            if not await self._is_provider_available_async(fallback_name):
                failed_providers.append(fallback_name)
                continue
            try:
                fallback = self.providers[fallback_name]
                result = await self._generate_with_timeout(fallback, request)

                confidence = self._calculate_confidence(result, request.intent, fallback_name)
                result.confidence_score = confidence  # type: ignore[attr-defined]
                result.provider_used = fallback_name  # type: ignore[attr-defined]
                result.fallback_from = primary  # type: ignore[attr-defined]

                if confidence < self._confidence_threshold:
                    logger.warning(
                        "Fallback %s returned low confidence %.2f for intent=%s, trying next",
                        fallback_name, confidence, request.intent,
                    )
                    failed_providers.append(fallback_name)
                    continue

                logger.info(
                    "Fallback success: %s → %s (confidence=%.2f)",
                    primary, fallback_name, confidence,
                )
                return result
            except Exception as fallback_err:
                self._mark_provider_failure(fallback_name, fallback_err)
                failed_providers.append(fallback_name)
                logger.warning(
                    "LLM fallback provider %s failed: %s",
                    fallback_name, fallback_err,
                )
                continue

        alerts = get_alert_service()
        alerts.alert_all_providers_failed(
            primary_provider=primary,
            failed_providers=failed_providers,
            error_msg=error_msg,
            user_message=request.message or "",
        )

        raise RuntimeError(
            f"All providers exhausted. Error: {error_msg}"
        ) from primary_err

    def _calculate_confidence(
        self,
        result: ProviderResult,
        intent: str,
        provider_name: str,
    ) -> float:
        """Calculate confidence score for a provider result (0.0 to 1.0)."""
        if provider_name == 'template':
            return 0.3

        score = 0.5

        text = result.text or ""
        if not text:
            return 0.0

        if len(text) > 50:
            score += 0.15
        if len(text) > 200:
            score += 0.1

        if "[⚠️ Low confidence]" in text:
            score -= 0.3
        if "I do not know" in text or "I cannot" in text:
            score -= 0.2

        if result.total_tokens and result.total_tokens > 50:
            score += 0.1

        score = max(0.0, min(1.0, score))

        self._provider_scores.setdefault(provider_name, {}).setdefault(intent, []).append(score)
        scores = self._provider_scores[provider_name][intent]
        if len(scores) > 20:
            self._provider_scores[provider_name][intent] = scores[-20:]

        return score

    def _average_confidence(
        self,
        provider_name: str,
        intent: str,
    ) -> float:
        """Get average confidence for a provider on a given intent."""
        scores = self._provider_scores.get(provider_name, {}).get(intent, [])
        if not scores:
            return 0.5
        return sum(scores) / len(scores)

    def _score_providers_for_intent(
        self,
        intent: str,
        candidates: list[str],
    ) -> list[tuple[float, str]]:
        """Score and sort provider candidates by historical performance for intent."""
        scored = []
        for name in candidates:
            if name not in self.providers:
                continue
            avg_conf = self._average_confidence(name, intent)
            scored.append((avg_conf, name))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    async def stream_generate(
        self,
        request: ProviderRequest,
        *,
        detected_lang: str | None = None,
    ):
        """Stream tokens from the selected provider.

        Yields dicts: {'type': 'token', 'text': str}
        On completion: {'type': 'done', 'provider': str, 'model': str}
        On error: falls back to non-streaming generate + yields full text as one token.
        """
        if detected_lang is None:
            detected_lang = detect_lang(request.message or '')

        import uuid
        if not request.correlation_id:
            request.correlation_id = str(uuid.uuid4())
            
        logger.info(
            "LLM stream_generate [%s] - Intent: %s - Provider: %s",
            request.correlation_id,
            request.intent,
            request.provider_hint or "auto"
        )

        primary = self._select_provider_name(request, detected_lang=detected_lang)
        provider = self.providers.get(primary) or self.providers.get('groq') or self.providers['template']

        try:
            if not await self._is_provider_available_async(primary):
                raise ProviderUnavailableError(f"{primary} is temporarily disabled by circuit breaker")

            stream_method = getattr(provider, 'stream', None)
            if stream_method is None:
                result = await self._generate_with_timeout(provider, request)
                yield {'type': 'token', 'text': result.text, 'provider': primary, 'model': getattr(result, 'model', '')}
                yield {'type': 'done', 'provider': primary, 'model': getattr(result, 'model', '')}
                return

            first_token = True
            async for token in self._stream_with_timeout(provider, request):
                if first_token:
                    first_token = False
                if token:
                    yield {'type': 'token', 'text': token, 'provider': primary}

            yield {'type': 'done', 'provider': primary}

        except Exception as exc:
            self._mark_provider_failure(primary, exc)
            logger.info("Streaming failed for %s, falling back to generate: %s", primary, exc)

            try:
                result = await self._try_fallback_chain(request, primary, detected_lang, primary_err=exc)
                yield {'type': 'token', 'text': result.text, 'provider': result.provider, 'model': result.model}
                yield {'type': 'done', 'provider': result.provider, 'model': result.model}
            except Exception as fallback_exc:
                logger.error("All fallbacks exhausted in stream_generate: %s", fallback_exc)
                yield {'type': 'error', 'message': 'All providers failed. Please try again later.'}

    async def _stream_with_timeout(
        self,
        provider,
        request: ProviderRequest,
    ):
        """Wrapper around provider.stream() with timeout."""
        try:
            async for token in asyncio.wait_for(
                provider.stream(request),
                timeout=self.provider_timeout_seconds,
            ):
                yield token
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"{provider.name} streaming timed out after {self.provider_timeout_seconds:.1f}s"
            )

    async def _generate_with_timeout(
        self,
        provider: TemplateProvider,
        request: ProviderRequest,
    ) -> ProviderResult:
        try:
            return await asyncio.wait_for(
                provider.generate(request),
                timeout=self.provider_timeout_seconds,
            )
        except TimeoutError as exc:
            raise TimeoutError(
                f"{provider.name} timed out after {self.provider_timeout_seconds:.1f}s"
            ) from exc

    def _provider_unavailable(self, provider_name: str) -> bool:
        """Fallback synchronous check (retained for compatibility)."""
        if provider_name == 'template':
            return False
        until = self._unavailable_until.get(provider_name)
        if until is None:
            return False
        if until <= time.time():
            self._unavailable_until.pop(provider_name, None)
            return False
        return True

    async def _is_provider_available_async(self, provider_name: str) -> bool:
        """Check if provider is available, using in-memory fast-path and Redis fallback."""
        if provider_name == 'template':
            return True
            
        # TokenBucket Rate Limiting (Phase 18)
        limiter = self._rate_limiters.get(provider_name)
        if limiter and not limiter.allow(1):
            logger.warning(f"Rate limit exceeded for provider {provider_name} via TokenBucket.")
            return False

        now = time.time()
        until = self._unavailable_until.get(provider_name)
        if until is not None:
            if until > now:
                return False
            else:
                self._unavailable_until.pop(provider_name, None)

        # Fallback to checking Redis if available
        if self.cache and hasattr(self.cache, 'get_provider_unavailable_until'):
            redis_until = await self.cache.get_provider_unavailable_until(provider_name)
            if redis_until is not None and isinstance(redis_until, (int, float)):
                if redis_until > now:
                    # Sync to local in-memory dict for rapid future queries
                    self._unavailable_until[provider_name] = redis_until
                    return False
        return True

    def _mark_provider_failure(self, provider_name: str, exc: Exception) -> None:
        if provider_name == 'template':
            return
        duration = 0
        if isinstance(exc, RateLimitError):
            duration = exc.retry_after
        elif isinstance(exc, QuotaExhaustedError):
            duration = 24 * 60 * 60
        elif isinstance(exc, (InvalidProviderKeyError, ModelUnavailableError)):
            duration = 60 * 60
        elif isinstance(exc, ProviderUnavailableError):
            duration = 5 * 60
        elif isinstance(exc, TimeoutError):
            duration = 60
        if duration > 0:
            until_time = time.time() + duration
            self._unavailable_until[provider_name] = until_time
            # Persistent state synchronization to Redis
            if self.cache and hasattr(self.cache, 'set_provider_unavailable_until'):
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        loop.create_task(
                            self.cache.set_provider_unavailable_until(provider_name, until_time, int(duration))
                        )
                except RuntimeError:
                    logger.debug("No running event loop for Redis circuit-breaker sync of %s", provider_name, exc_info=True)
            logger.warning(
                "Provider %s disabled for %ss after %s",
                provider_name,
                duration,
                exc.__class__.__name__,
            )
            chatbot_circuit_breaker_trips_total.labels(
                provider=provider_name, error_type=exc.__class__.__name__
            ).inc()
            self._sync_circuit_metrics()
            # C12: Send alert when circuit breaker trips for > 5 minutes
            if duration >= 300:
                alerts = get_alert_service()
                alerts.alert_circuit_breaker_tripped(
                    provider=provider_name,
                    duration_seconds=duration,
                    error_type=exc.__class__.__name__,
                    error_message=str(exc)[:500],
                )

    def _sync_circuit_metrics(self) -> None:
        now = time.time()
        unavailable = {
            name for name, until in self._unavailable_until.items()
            if until > now
        }
        update_circuit_breaker_gauges(unavailable, list(self.providers.keys()))
