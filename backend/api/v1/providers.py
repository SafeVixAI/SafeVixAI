# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.limiter import limiter
from core.security import get_current_user
from models.provider_config import UserProviderConfig
from services.provider_encrypt import decrypt_api_key, encrypt_api_key, mask_api_key

logger = logging.getLogger("safevixai.api.providers")

router = APIRouter(prefix="/api/v1/providers", tags=["Providers"])


class ProviderConfigCreate(BaseModel):
    provider_name: str = Field(..., min_length=1, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=128)
    api_key: str | None = Field(None, max_length=4096)
    base_url: str | None = Field(None, max_length=512)
    default_model: str | None = Field(None, max_length=128)
    extra_headers: dict[str, str] | None = None
    is_active: bool = True
    priority: int = 0
    is_custom: bool = False
    is_local_model: bool = False
    timeout_ms: int | None = Field(None, ge=1000, le=60000)

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        if v and not str(v).startswith(('http://', 'https://')):
            raise ValueError("base_url must start with http:// or https://")
        return v


class ProviderConfigUpdate(BaseModel):
    display_name: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None
    extra_headers: dict[str, str] | None = None
    is_active: bool | None = None
    priority: int | None = None
    is_local_model: bool | None = None
    timeout_ms: int | None = Field(None, ge=1000, le=60000)

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        if v and not str(v).startswith(('http://', 'https://')):
            raise ValueError("base_url must start with http:// or https://")
        return v


class ProviderConfigResponse(BaseModel):
    id: str
    provider_name: str
    display_name: str
    api_key_masked: str | None
    base_url: str | None
    default_model: str | None
    is_active: bool
    priority: int
    is_custom: bool
    is_local_model: bool
    timeout_ms: int | None
    circuit_breaker_failures: int
    created_at: str
    updated_at: str


class ProviderTestRequest(BaseModel):
    provider_name: str
    api_key: str
    model: str | None = None


_BUILTIN_PROVIDERS = [
    {"name": "groq", "display": "Groq Cloud", "base_url": "https://api.groq.com/openai/v1/chat/completions", "models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"]},
    {"name": "cerebras", "display": "Cerebras", "base_url": "https://api.cerebras.ai/v1/chat/completions", "models": ["llama-3.1-8b", "llama-3.3-70b"]},
    {"name": "gemini", "display": "Google Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta/models", "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]},
    {"name": "github", "display": "GitHub Models", "base_url": "https://models.inference.ai.azure.com/chat/completions", "models": ["gpt-4o", "gpt-4o-mini", "Phi-3.5-mini-instruct"]},
    {"name": "nvidia", "display": "NVIDIA NIM", "base_url": "https://integrate.api.nvidia.com/v1/chat/completions", "models": ["meta/llama-3.1-8b-instruct", "mistralai/mistral-7b-instruct-v0.3"]},
    {"name": "openrouter", "display": "OpenRouter", "base_url": "https://openrouter.ai/api/v1/chat/completions", "models": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "google/gemini-1.5-flash"]},
    {"name": "mistral", "display": "Mistral AI", "base_url": "https://api.mistral.ai/v1/chat/completions", "models": ["mistral-large-latest", "mistral-medium-latest", "open-mistral-nemo"]},
    {"name": "together", "display": "Together AI", "base_url": "https://api.together.xyz/v1/chat/completions", "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "mistralai/Mixtral-8x7B-Instruct-v0.1"]},
    {"name": "sarvam", "display": "Sarvam AI", "base_url": "https://api.sarvam.ai/v1/chat/completions", "models": ["sarvam-30b", "sarvam-105b"]},
    {"name": "openai", "display": "OpenAI", "base_url": "https://api.openai.com/v1/chat/completions", "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]},
    {"name": "anthropic", "display": "Anthropic", "base_url": "https://api.anthropic.com/v1/messages", "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]},
    {"name": "deepseek", "display": "DeepSeek", "base_url": "https://api.deepseek.com/v1/chat/completions", "models": ["deepseek-chat", "deepseek-reasoner"]},
    {"name": "ollama", "display": "Ollama (Local)", "base_url": "http://localhost:11434/v1/chat/completions", "models": ["llama3.2", "mistral", "codellama", "phi", "qwen2.5"]},
    {"name": "lmstudio", "display": "LM Studio (Local)", "base_url": "http://localhost:1234/v1/chat/completions", "models": ["local-model"]},
    {"name": "vllm", "display": "vLLM (Local)", "base_url": "http://localhost:8000/v1/chat/completions", "models": ["local-model"]},
    {"name": "localai", "display": "LocalAI", "base_url": "http://localhost:8080/v1/chat/completions", "models": ["local-model"]},
]


@router.get("/builtins", response_model=list[dict])
async def list_builtin_providers():
    """List all built-in provider templates with their default endpoints and models."""
    return _BUILTIN_PROVIDERS


@router.get("/", response_model=list[ProviderConfigResponse])
@limiter.limit("20/minute")
async def list_provider_configs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all configured providers for the current user."""
    user_id = str(current_user.get("sub"))
    result = await db.execute(
        select(UserProviderConfig)
        .where(UserProviderConfig.user_id == user_id)
        .order_by(UserProviderConfig.priority, UserProviderConfig.provider_name)
    )
    configs = result.scalars().all()
    return [
        ProviderConfigResponse(
            id=str(c.id),
            provider_name=c.provider_name,
            display_name=c.display_name,
            api_key_masked=mask_api_key(decrypt_api_key(c.api_key_encrypted)),
            base_url=c.base_url,
            default_model=c.default_model,
            is_active=c.is_active,
            priority=c.priority,
            is_custom=c.is_custom,
            is_local_model=c.is_local_model,
            timeout_ms=c.timeout_ms,
            circuit_breaker_failures=c.circuit_breaker_failures,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in configs
    ]


@router.post("/", response_model=ProviderConfigResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_provider_config(
    request: Request,
    data: ProviderConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new provider configuration."""
    user_id = str(current_user.get("sub"))

    existing = await db.execute(
        select(UserProviderConfig).where(
            UserProviderConfig.user_id == user_id,
            UserProviderConfig.provider_name == data.provider_name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Provider '{data.provider_name}' already configured. Use PUT to update.")

    encrypted = encrypt_api_key(data.api_key) if data.api_key else None

    config = UserProviderConfig(
        user_id=user_id,
        provider_name=data.provider_name,
        display_name=data.display_name,
        api_key_encrypted=encrypted,
        base_url=data.base_url,
        default_model=data.default_model,
        extra_headers=data.extra_headers,
        is_active=data.is_active,
        priority=data.priority,
        is_custom=data.is_custom,
        is_local_model=data.is_local_model,
        timeout_ms=data.timeout_ms,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    return ProviderConfigResponse(
        id=str(config.id),
        provider_name=config.provider_name,
        display_name=config.display_name,
        api_key_masked=mask_api_key(data.api_key),
        base_url=config.base_url,
        default_model=config.default_model,
        is_active=config.is_active,
        priority=config.priority,
        is_custom=config.is_custom,
        is_local_model=config.is_local_model,
        timeout_ms=config.timeout_ms,
        circuit_breaker_failures=config.circuit_breaker_failures,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.put("/{config_id}", response_model=ProviderConfigResponse)
@limiter.limit("20/minute")
async def update_provider_config(
    request: Request,
    config_id: uuid.UUID,
    data: ProviderConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update an existing provider configuration."""
    user_id = str(current_user.get("sub"))

    result = await db.execute(
        select(UserProviderConfig).where(
            UserProviderConfig.id == config_id,
            UserProviderConfig.user_id == user_id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Provider config not found")

    if data.display_name is not None:
        config.display_name = data.display_name
    if data.api_key is not None:
        config.api_key_encrypted = encrypt_api_key(data.api_key)
    if data.base_url is not None:
        config.base_url = data.base_url
    if data.default_model is not None:
        config.default_model = data.default_model
    if data.extra_headers is not None:
        config.extra_headers = data.extra_headers
    if data.is_active is not None:
        config.is_active = data.is_active
    if data.priority is not None:
        config.priority = data.priority
    if data.is_local_model is not None:
        config.is_local_model = data.is_local_model
    if data.timeout_ms is not None:
        config.timeout_ms = data.timeout_ms

    await db.commit()
    await db.refresh(config)

    return ProviderConfigResponse(
        id=str(config.id),
        provider_name=config.provider_name,
        display_name=config.display_name,
        api_key_masked=mask_api_key(decrypt_api_key(config.api_key_encrypted)),
        base_url=config.base_url,
        default_model=config.default_model,
        is_active=config.is_active,
        priority=config.priority,
        is_custom=config.is_custom,
        is_local_model=config.is_local_model,
        timeout_ms=config.timeout_ms,
        circuit_breaker_failures=config.circuit_breaker_failures,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider_config(
    request: Request,
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a provider configuration."""
    user_id = str(current_user.get("sub"))

    result = await db.execute(
        select(UserProviderConfig).where(
            UserProviderConfig.id == config_id,
            UserProviderConfig.user_id == user_id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Provider config not found")

    await db.delete(config)
    await db.commit()


def _lookup_provider_url(provider_name: str) -> str:
    """Look up the base URL for a built-in provider by name. Raises 404 if not found."""
    for p in _BUILTIN_PROVIDERS:
        if p["name"] == provider_name:
            return p["base_url"]
    raise HTTPException(status_code=404, detail=f"Unknown provider '{provider_name}'")


@router.post("/test")
@limiter.limit("10/minute")
async def test_provider_connection(
    request: Request,
    data: ProviderTestRequest,
):
    """Test a provider connection by making a lightweight API call."""
    import traceback

    import httpx

    base_url = _lookup_provider_url(data.provider_name)
    model = data.model or "gpt-3.5-turbo"

    headers = {
        "Authorization": f"Bearer {data.api_key}",
        "Content-Type": "application/json",
    }

    test_payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: pong"}],
        "max_tokens": 10,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(base_url, headers=headers, json=test_payload)
            if resp.status_code == 200:
                return {"status": "ok", "message": "Connection successful", "provider": data.provider_name, "model": model}
            elif resp.status_code == 401:
                return {"status": "error", "message": "Invalid API key (401)"}
            elif resp.status_code == 403:
                return {"status": "error", "message": "API key lacks access (403)"}
            elif resp.status_code == 404:
                return {"status": "error", "message": f"Endpoint not found: {resp.status_code}"}
            else:
                body = await resp.aread()
                return {"status": "error", "message": f"HTTP {resp.status_code}: {body[:200].decode(errors='replace')}"}
    except httpx.ConnectError:
        logger.warning("Provider connection failed for %s: %s", data.provider_name, base_url)
        return {"status": "error", "message": f"Cannot connect to {data.provider_name}. Check URL and network."}
    except httpx.TimeoutException:
        return {"status": "error", "message": "Connection timed out after 10s"}
    except Exception:
        logger.exception("Unexpected error testing provider %s", data.provider_name)
        return {"status": "error", "message": "Internal server error"}


@router.post("/sync", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def sync_providers_to_chatbot(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Sync active provider configs to the chatbot service for the current session."""
    user_id = str(current_user.get("sub"))

    from core.distributed_lock import distributed_lock

    # P17: Enforce distributed Redlock isolation around /api/v1/providers/sync
    async with distributed_lock(f"sync_providers:{user_id}", ttl_seconds=5) as acquired:
        if not acquired:
            raise HTTPException(status_code=409, detail="Sync operation already in progress")

        result = await db.execute(
            select(UserProviderConfig)
            .where(
                UserProviderConfig.user_id == user_id,
                UserProviderConfig.is_active == True,
            )
            .order_by(UserProviderConfig.priority)
        )
        configs = result.scalars().all()

        provider_list = []
        for c in configs:
            key = decrypt_api_key(c.api_key_encrypted)
            provider_list.append({
                "provider_name": c.provider_name,
                "display_name": c.display_name,
                "api_key": key,
                "base_url": c.base_url,
                "default_model": c.default_model,
                "extra_headers": c.extra_headers,
                "is_custom": c.is_custom,
                "is_local_model": c.is_local_model,
                "timeout_ms": c.timeout_ms,
                "priority": c.priority,
            })

        from core.redis_client import get_redis_client
        redis = await get_redis_client()
        if redis:
            import json
            await redis.setex(f"user_providers:{user_id}", 86400, json.dumps(provider_list))

        return {"synced": len(provider_list), "providers": [p["provider_name"] for p in provider_list]}
