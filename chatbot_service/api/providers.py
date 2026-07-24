# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Provider configuration API — allows dynamic provider loading from the backend.

Users can configure their own API keys and custom providers via the backend,
which get synced to the chatbot service via Redis or direct API call.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlparse

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
    request: Request,
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
    request: Request,
    provider_router: ProviderRouter = Depends(get_provider_router),
):
    """Return currently active provider configs (env + user-configured)."""
    return provider_router.get_active_provider_info()


_ALLOWED_PROVIDER_DOMAINS = {
    "api.groq.com", "api.cerebras.ai", "generativelanguage.googleapis.com",
    "models.inference.ai.azure.com", "integrate.api.nvidia.com",
    "openrouter.ai", "api.mistral.ai", "api.together.xyz",
    "api.sarvam.ai", "api.openai.com", "api.anthropic.com",
    "api.deepseek.com", "huggingface.co",
}


def _validate_provider_url(url: str) -> str:
    """Validate and return a sanitized provider URL. Raises HTTPException on invalid URL."""
    parsed = urlparse(url)
    if not parsed.scheme:
        parsed = urlparse("https://" + url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="URL must use http or https scheme")
    hostname = parsed.hostname or ""
    if hostname not in _ALLOWED_PROVIDER_DOMAINS and not hostname.endswith(".safevixai.internal") and hostname not in ("localhost", "127.0.0.1", "host.docker.internal"):
        raise HTTPException(status_code=400, detail=f"Provider domain '{hostname}' is not allowed")
    return url


@router.post("/test")
@limiter.limit("5/minute")
async def test_provider(
    request: Request,
    data: dict[str, Any],
):
    """Test a provider connection directly from the chatbot service."""
    import traceback

    import httpx

    api_key = data.get("api_key", "")
    base_url = data.get("base_url", "")
    model = data.get("model", "gpt-3.5-turbo")
    provider_name = data.get("provider_name", "custom")

    if not base_url:
        raise HTTPException(status_code=400, detail="base_url is required")

    base_url = _validate_provider_url(base_url)

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
            return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception:
        logger.exception("Provider test failed for %s", provider_name)
        return {"status": "error", "message": "An unexpected error occurred. Check server logs."}


@router.post("/reset")
@limiter.limit("5/minute")
async def reset_providers(
    request: Request,
    provider_router: ProviderRouter = Depends(get_provider_router),
):
    """Reset to default env-var-based providers (clear user configs)."""
    provider_router.reset_to_env_providers()
    return {"status": "ok", "message": "Reset to default providers"}
