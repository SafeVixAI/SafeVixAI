# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.config import get_settings

router = APIRouter(tags=["Probes"])

_startup_complete = False


def set_startup_complete() -> None:
    global _startup_complete
    _startup_complete = True


@router.get("/readyz")
async def readiness_probe(request: Request) -> JSONResponse:
    settings = get_settings()
    services: dict[str, str] = {}

    db_ok = False
    try:
        from core.database import check_database
        db_ok = await check_database()
    except Exception:
        db_ok = False
    services["database"] = "ok" if db_ok else "degraded"

    cache_ok = False
    cache = getattr(request.app.state, "cache", None)
    if cache is not None:
        try:
            cache_ok = await asyncio_wrap(cache.ping(), timeout=5.0)
        except Exception:
            cache_ok = False
    services["cache"] = "ok" if cache_ok else "degraded"

    chatbot_ok = False
    if settings.chatbot_service_url and settings.environment != "test":
        try:
            cb_health_url = f"{settings.chatbot_service_url.replace('/api/v1', '')}/health"
            async with httpx.AsyncClient(timeout=5.0) as client:
                cb_resp = await client.get(cb_health_url)
                chatbot_ok = cb_resp.status_code == 200
        except Exception:
            chatbot_ok = False
    else:
        chatbot_ok = True
    services["chatbot"] = "ok" if chatbot_ok else "degraded"

    all_ok = all(v == "ok" for v in services.values())
    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if all_ok else "degraded", "services": services},
    )


@router.get("/livez")
async def liveness_probe() -> JSONResponse:
    return JSONResponse(status_code=200, content={"status": "alive"})


@router.get("/startupz")
async def startup_probe() -> JSONResponse:
    if _startup_complete:
        return JSONResponse(status_code=200, content={"status": "started"})
    return JSONResponse(status_code=503, content={"status": "starting"})


async def asyncio_wrap(coro, timeout: float = 5.0):
    import asyncio
    return await asyncio.wait_for(coro, timeout=timeout)
