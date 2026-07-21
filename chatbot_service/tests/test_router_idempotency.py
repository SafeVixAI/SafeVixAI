# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
import pytest
from unittest.mock import AsyncMock
from providers.router import ProviderRouter
from providers.base import ProviderRequest
from config import Settings
from cache.llm_cache import LLMResponseCache, CacheEntry

@pytest.fixture
def mock_settings():
    settings = Settings(default_llm_provider="template")
    return settings

@pytest.fixture
def mock_cache():
    cache = AsyncMock(spec=LLMResponseCache)
    return cache

@pytest.fixture
def router(mock_settings, mock_cache):
    return ProviderRouter(settings=mock_settings, cache=mock_cache)

@pytest.mark.asyncio
async def test_router_idempotency_cache_hit(router, mock_cache):
    mock_cache.get.return_value = CacheEntry(
        text="Cached response",
        provider="groq",
        model="llama3-70b-8192",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )
    
    req = ProviderRequest(
        message="Hello",
        intent="general",
        history=[],
        idempotency_key="idemp_123"
    )
    
    res = await router.generate(req)
    
    mock_cache.get.assert_called_once()
    assert res.text == "Cached response"
    assert res.provider_used == "cache"

@pytest.mark.asyncio
async def test_router_idempotency_cache_miss(router, mock_cache):
    mock_cache.get.return_value = None
    
    # We'll use the template provider to ensure it generates a result
    router._fallback_chain = ["template"]
    
    req = ProviderRequest(
        message="Hello",
        intent="general",
        history=[],
        idempotency_key="idemp_123",
        provider_hint="template"
    )
    
    res = await router.generate(req)
    
    mock_cache.get.assert_called_once()
    # Template provider doesn't cache (see code: result.provider != 'template')
    mock_cache.set.assert_not_called()
    assert "I can help with road safety" in res.text
    assert res.provider_used == "template"

@pytest.mark.asyncio
async def test_router_cache_set_for_real_provider(router, mock_cache):
    mock_cache.get.return_value = None
    
    # Mocking a real provider
    mock_provider = AsyncMock()
    from providers.base import ProviderResult
    mock_provider.generate.return_value = ProviderResult(
        text="Real response",
        provider="real",
        model="real_model"
    )
    mock_provider.get_model_name.return_value = "real_model"
    
    router.providers["real"] = mock_provider
    router._fallback_chain = ["real"]
    
    req = ProviderRequest(
        message="Hello",
        intent="general",
        history=[],
        idempotency_key="idemp_123",
        provider_hint="real"
    )
    
    res = await router.generate(req)
    
    mock_cache.get.assert_called_once()
    mock_cache.set.assert_called_once()
    assert res.text == "Real response"
    assert res.provider_used == "real"
