# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from core.circuit_breaker import CircuitBreakerRegistry
from core.limiter import limiter
from core.rbac import Role, require_role
from core.security import get_current_user

router = APIRouter(prefix="/api/v1/circuit-breaker", tags=["Circuit Breaker"])


@router.get("/")
@limiter.limit("30/minute")
async def get_circuit_breakers(
    request: Request,
    _current_user: dict = Depends(get_current_user),
) -> dict:
    stats = CircuitBreakerRegistry.all_stats()
    return {"breakers": stats, "count": len(stats)}


@router.get("/{name}")
@limiter.limit("30/minute")
async def get_circuit_breaker(
    request: Request,
    name: str,
    _current_user: dict = Depends(require_role(Role.ADMIN)),
) -> dict:
    stats = CircuitBreakerRegistry.all_stats()
    if name not in stats:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")
    return {"breaker": stats[name]}


@router.post("/reset")
@limiter.limit("5/minute")
async def reset_circuit_breakers(
    request: Request,
    _current_user: dict = Depends(require_role(Role.ADMIN)),
) -> dict:
    CircuitBreakerRegistry.reset_all()
    return {"status": "ok", "message": "All circuit breakers reset"}


@router.post("/trigger/{name}")
@limiter.limit("5/minute")
async def trigger_breaker(
    request: Request,
    name: str,
    _current_user: dict = Depends(require_role(Role.ADMIN)),
) -> dict:
    cb = CircuitBreakerRegistry._breakers.get(name)
    if cb is None:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")
    cb.force_open()
    return {"status": "ok", "message": f"Circuit breaker '{name}' opened manually"}


@router.post("/close/{name}")
@limiter.limit("5/minute")
async def close_breaker(
    request: Request,
    name: str,
    _current_user: dict = Depends(require_role(Role.ADMIN)),
) -> dict:
    cb = CircuitBreakerRegistry._breakers.get(name)
    if cb is None:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")
    cb.force_close()
    return {"status": "ok", "message": f"Circuit breaker '{name}' closed manually"}
