# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Provider configuration API — allows dynamic provider loading from the backend.

Users can configure their own API keys and custom providers via the backend,
which get synced to the chatbot service via Redis or direct API call.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from config import get_settings
from limiter import limiter
from providers.router import ProviderRouter

logger = logging.getLogger("safevixai.chatbot.api.providers")

router = APIRouter(prefix="/api/v1/providers", tags=["Providers"])


def get_provider_router(request: Request) -> ProviderRouter:
    return request.app.state.chat_engine.provider_router


@router.post("/configure")
@limiter.limit("5/minute")
async def configure_providers(
    request: Request,  # noqa
    providers: list[dict[str, Any]],
    provider_router: ProviderRouter = Depends(get_provider_router),
):
    """Dynamically configure providers for the current session.

    Accepts a list of provider configs with:
      - provider_name: str
      - api_key: str
      - base_url: str | None (for custom providers)
      - default_model: str | None
      - is_custom: bool
      - priority: int
    """
    configured = provider_router.configure_user_providers(providers)
    return {
        "status": "ok",
        "configured": len(configured),
        "providers": configured,
    }


@router.get("/active")
@limiter.limit("10/minute")
async def get_active_providers(
    request: Request,  # noqa
    provider_router: ProviderRouter = Depends(get_provider_router),
):
    """Return currently active provider configs (env + user-configured)."""
    return provider_router.get_active_provider_info()


def _lookup_provider_url(provider_name: str, provider_router: ProviderRouter) -> str:
    """Look up the base URL for a provider from the active provider config."""
    providers = provider_router.get_active_provider_info()
    for p in providers:
        name = p.get("name", "") or p.get("provider_name", "")
        if name == provider_name:
            base_url = p.get("base_url", "")
            if base_url:
                return base_url
    # Fallback: check env provider configs
    settings = get_settings()
    env_providers = getattr(settings, "provider_configs", [])
    for p in env_providers:
        if p.get("name") == provider_name:
            base_url = p.get("base_url", "")
            if base_url:
                return base_url
    raise HTTPException(status_code=404, detail=f"Unknown provider '{provider_name}'")


@router.post("/test")
@limiter.limit("5/minute")
async def test_provider(
    request: Request,  # noqa
    data: dict[str, Any],
    provider_router: ProviderRouter = Depends(get_provider_router),
):
    """Test a provider connection."""

    import httpx

    import urllib.parse
    
    api_key = data.get("api_key", "")
    provider_name = data.get("provider_name", "custom")
    model = data.get("model", "gpt-3.5-turbo")

    base_url = data.get("base_url", "") or _lookup_provider_url(provider_name, provider_router)
    
    if not base_url.startswith("https://"):
        return {"status": "error", "message": "Only HTTPS endpoints are allowed for custom providers"}
    
    # Explicit whitelist to prevent SSRF (fixes CodeQL alert)
    ALLOWED_DOMAINS = {
        "api.openai.com",
        "api.anthropic.com",
        "generativelanguage.googleapis.com",
        "api.groq.com",
        "api.mistral.ai",
        "api.together.xyz",
        "api.x.ai",
        "api.deepseek.com"
    }

    parsed = urllib.parse.urlparse(base_url)
    hostname = parsed.hostname or ""
    
    if hostname not in ALLOWED_DOMAINS:
        return {"status": "error", "message": f"Domain '{hostname}' is not in the allowed providers whitelist."}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    test_payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with: pong"}],
        "max_tokens": 10,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(base_url, headers=headers, json=test_payload)
            if resp.status_code == 200:
                return {"status": "ok", "message": "Connection successful", "provider": provider_name}
            return {"status": "error", "message": f"HTTP {resp.status_code}: Error testing provider"}
    except Exception as exc:
        logger.warning("Provider test failed for %s: %s", provider_name, exc)
        return {"status": "error", "message": "Connection failed or timeout occurred"}


@router.post("/reset")
@limiter.limit("5/minute")
async def reset_providers(
    request: Request,  # noqa
    provider_router: ProviderRouter = Depends(get_provider_router),
):
    """Reset to default env-var-based providers (clear user configs)."""
    provider_router.reset_to_env_providers()
    return {"status": "ok", "message": "Reset to default providers"}
