# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from fastapi import APIRouter

from config import get_settings

router = APIRouter(prefix="/api/v1", tags=["version"])


@router.get("/version")
async def get_version():
    settings = get_settings()
    return {
        "version": "1.0.0",
        "service": settings.service_name,
        "environment": settings.environment,
    }
