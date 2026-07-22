# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import get_settings

settings = get_settings()

if settings.redis_url:
    # P1-02: Use Redis storage for rate limiting to share limits across worker processes (audit H3)
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.redis_url
    )
else:
    # Fallback to memory for local dev
    limiter = Limiter(key_func=get_remote_address)

if settings.environment == "test":
    limiter.enabled = False

